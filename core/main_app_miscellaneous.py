import time
import jinja2
import pandas as pd
import streamlit as st
import datetime
from datetime import datetime as dt
from core.openai_api import *
from core.duckdb_connector import *
from core.utils import handle_exception, wait_while_condition_is_valid
from core.sql.user_daily_recommended_intake_history import anonymous_user_daily_nutrient_intake_query_template, combine_user_actual_vs_recommend_intake_logic

RECOMMENDED_DAILY_NUTRIENT_INTAKE_TABLE_ID = "ilab.main.daily_nutrients_recommendation"
USER_DAILY_RECOMMENDED_INTAKE_HISTORY_TABLE_ID = "ilab.main.user_daily_recommended_intake_history"

USER_INTAKE_COLUMNS_DICT = {
    "gender": "Gender",
    "age": "Age",
    "dish_description": "Dish",
    "nutrient": "Nutrient",
    "actual_intake": "Actual intake",
    "daily_recommended_intake": "Daily recommended intake",
    "measurement": "Measurement",
    "actual_over_recommended_intake_percent": "Actual intake / Recommended intake (%)"
}

class MainAppMiscellaneous:
    def __init__(self, has_openai_connection_enabled=True, openai_client=None) -> None:
        self.jinja_environment = jinja2.Environment()
        self.db = DuckdbConnector()
        if has_openai_connection_enabled:
            self.openai_api = OpenAIAssistant(openai_client=openai_client)

    @handle_exception(has_random_message_printed_out=True)
    def say_hello(
        self,
        user_name=None,
        layout_position=st,
    ) -> None:
        if user_name:
            layout_position.write(f"It's good to see you back, {user_name}! What would you like to do today?")
        else:
            layout_position.write("Hello there, how can we help you?")

    @handle_exception(has_random_message_printed_out=True)
    def get_user_input_dish_and_estimate_ingredients(
        self,
        dish_description: str,
        layout_position=st
    ) -> pd.DataFrame:
        # st.session_state["dish_description"] = dish_description
        ingredient_df = pd.DataFrame()
        if dish_description:
            ingredient_estimation_prompt = f"""
                Given the input which is the description of a dish,
                guess the ingredients of that dish
                and estimate the weight of each ingredient in gram for one serve,
                just 1 estimate for each ingredient and return the output in a python dictionary.
                The estimate should be as detailed as possible.
                If input is not food, return an empty dictionary.
                Input ```{dish_description}```
            """
            ingredient_df = self.openai_api.estimate_and_extract_dish_info(
                dish_description=dish_description,
                ingredient_estimation_prompt=ingredient_estimation_prompt,
                layout_position=layout_position
            )
            ingredient_df["dish_description"] = dish_description

        return ingredient_df

    @handle_exception(has_random_message_printed_out=True)
    def check_whether_user_needs_to_input_personal_info_manually(
        self,
        layout_position = st
    ) -> bool:
        has_user_personal_info_input_manually = True
        user_input_personal_info_agreement = None
        layout_position.write("We need your age 📆 and gender ♀♂ to suggest the recommended intake.")
        user_input_personal_info_agreement = layout_position.selectbox(
            "But looks like we've just met for the first time, do you want to manually input your info?",
            ("Yes, let's do it!", 'No'),
            placeholder="Select your answer..."
        )
        if user_input_personal_info_agreement == "No":
            has_user_personal_info_input_manually = False
        return has_user_personal_info_input_manually

    def get_user_personal_info_manual_input(
        self,
        layout_position=st
    ) -> dict:
        form = layout_position.form("personal_data_form")
        user_gender = form.selectbox(
            "Please select your gender",
            ("male", 'female'),
            index=None,
            placeholder="Select your gender..."
        )
        user_age_input = form.number_input(
            "How old are you?",
            value=None,
            placeholder="Type a number..."
        )
        submitted = form.form_submit_button("Submit")
        # wait until user inputs
        wait_while_condition_is_valid((not submitted))

        user_personal_data = {
            "status": 200,
            "gender": user_gender,
            "age": float(user_age_input)
        }
        return user_personal_data

    def get_user_age_and_gender(
        self,
        is_logged_in,
        user_id,
        layout_position
    ):
        user_personal_data = {}
        if is_logged_in:
            user_personal_data = self.db.get_user_personal_data_from_database(user_id=user_id)

        if user_personal_data.get("status", 400) != 200:
            has_user_personal_info_input_manually = self.check_whether_user_needs_to_input_personal_info_manually(
                layout_position=layout_position
            )
            # If user has not logged in or we don't have user's data, get them manually input their age + gender
            if has_user_personal_info_input_manually:
                user_personal_data = self.get_user_personal_info_manual_input(
                    layout_position=layout_position
                )
        return user_personal_data

    @handle_exception(has_random_message_printed_out=True)
    def get_user_personal_data(
        self,
        is_logged_in: bool,
        user_id: str,
        has_user_intake_df_temp_empty: bool,
        layout_position=st
    ) -> dict:
        user_personal_data = {"status": 0}
        if not has_user_intake_df_temp_empty:
            user_personal_data = self.get_user_age_and_gender(
                is_logged_in=is_logged_in,
                user_id=user_id,
                layout_position=layout_position
            )
        return user_personal_data

    @handle_exception(has_random_message_printed_out=True)
    def get_user_recommended_intake(
            self,
            user_intake_df_temp_name: str
        ) -> pd.DataFrame:
        query_template = self.jinja_environment.from_string(
            anonymous_user_daily_nutrient_intake_query_template
        )
        query = query_template.render(
            recommended_daily_nutrient_intake_table_id=RECOMMENDED_DAILY_NUTRIENT_INTAKE_TABLE_ID,
            user_intake_df_temp_name=user_intake_df_temp_name,
            combine_user_actual_vs_recommend_intake_logic=combine_user_actual_vs_recommend_intake_logic
        )
        user_recommended_intake_df = self.db.run_query(
            sql=query,
            result_format='dataframe'
        )
        return user_recommended_intake_df

    @handle_exception(has_random_message_printed_out=True)
    def combine_and_show_users_recommended_intake(
        self,
        user_personal_data: dict,
        user_intake_df_temp: pd.DataFrame,
        user_intake_df_temp_name: str,
        layout_position=st,
    ) -> pd.DataFrame:
        user_recommended_intake_df = pd.DataFrame()

        if user_personal_data.get("status") == 200 and not user_intake_df_temp.empty:
            user_intake_df_temp["gender"] = user_personal_data.get("gender")
            user_intake_df_temp["age"] = user_personal_data.get("age")

            user_recommended_intake_df = self.get_user_recommended_intake(
                user_intake_df_temp_name=user_intake_df_temp_name
            )
            user_recommended_intake_df_to_show = user_recommended_intake_df.copy()
            user_recommended_intake_df_to_show = user_recommended_intake_df_to_show.rename(columns=USER_INTAKE_COLUMNS_DICT)
            columns_to_show = USER_INTAKE_COLUMNS_DICT.values()

            if not user_recommended_intake_df_to_show.empty:
                layout_position.dataframe(user_recommended_intake_df_to_show[columns_to_show])
            else:
                layout_position.write("Oops! Turns out it's pseudoscience 🫥 We cannot estimate your intake just yet 😅 Please try again later...")

        result = {
            "status": 200,
            "value": user_recommended_intake_df
        }

        return result

    @handle_exception(has_random_message_printed_out=True)
    def get_user_confirmation_and_try_to_save_their_data(
        self,
        dish_description: str,
        user_id: str,
        is_logged_in: bool,
        has_user_intake_df_temp_empty: bool,
        layout_position=st
    ):
        if has_user_intake_df_temp_empty:
            result = {"status": 4000}
            return result
        result = {
            "status": 200,
            "login_or_create_account": "No"
        }
        has_historical_data_saved = layout_position.selectbox(
            "Do you want to save this meal info?",
            ("Yes", 'No'),
            index=None,
            placeholder="Select your answer..."
        )
        # wait until user inputs
        wait_while_condition_is_valid((has_historical_data_saved is None))
        if has_historical_data_saved == "Yes":
            if is_logged_in:
                storing_historical_data_result = self.db.save_user_data(
                    dish_description=dish_description,
                    user_id=user_id,
                    user_intake_df_temp_name="user_intake_df_temp",
                    layout_position=layout_position
                )
                if storing_historical_data_result.get("status") == 200:
                    storing_historical_data_message = storing_historical_data_result.get("message")
                    layout_position.write(storing_historical_data_message)
            else:
                login_or_create_account = layout_position.selectbox(
                    "Looks like you haven't logged in, do you want to log in to save this meal's intake estimation?",
                    ("Yes", 'No'),
                    index=None,
                    placeholder="Select your answer..."
                )
                result["login_or_create_account"] = login_or_create_account
        return result

    def get_user_historical_data(
        self,
        user_id: bool,
        selected_date_range: tuple,
        date_format="%Y-%m-%d"
    ) -> pd.DataFrame:
        start_date, end_date = selected_date_range
        query_template = self.jinja_environment.from_string(
            """
                SELECT * FROM {{ view_id }}
                WHERE
                    user_id = '{{ user_id }}'
                    AND record_date BETWEEN STRPTIME('{{ start_date }}', '{{ date_format }}') AND STRPTIME('{{ end_date }}', '{{ date_format }}')
            """
        )
        query = query_template.render(
            view_id=USER_DAILY_RECOMMENDED_INTAKE_HISTORY_TABLE_ID,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            date_format=date_format
        )
        user_recommended_intake_history_df = self.db.run_query(
            sql=query,
            result_format='dataframe'
        )
        return user_recommended_intake_history_df

    @handle_exception(has_random_message_printed_out=True)
    def show_user_historical_data_result(
        self,
        is_logged_in: bool,
        user_id: bool,
        selected_date_range: tuple,
        layout_position=st
    ) -> None:
        result = {
            "status": 200
        }
        if is_logged_in and user_id:
            user_recommended_intake_history_df = self.get_user_historical_data(
                user_id=user_id,
                selected_date_range=selected_date_range
            )
            result["value"] = user_recommended_intake_history_df
            if not user_recommended_intake_history_df.empty:
                layout_position.dataframe(user_recommended_intake_history_df)   ### TODO: replace with method to visualize data
            else:
                layout_position.write("""
                    Oops, looks like you haven't tracked your nutrition.
                    Try different dates or start tracking now to see your nutrition intake history 😉
                """)
        else:
            layout_position.write("Looks like you haven't logged in, do you want to log in to see your data?")
            layout_position.link_button("Log in", "https://streamlit.io/gallery")   ### TODO: replace with actual log in

        return result

    @handle_exception(has_random_message_printed_out=True)
    def select_date_range(
        self,
        layout_position=st,
        date_format="%Y-%m-%d"
    ):
        tz = pytz.timezone('Australia/Sydney')
        today = datetime.datetime.now(tz)
        last_month = today - datetime.timedelta(days=30)
        start_date = datetime.date(2000, 1, 1)
        end_date = datetime.date(3000, 1, 1)

        selected_date_range = layout_position.date_input(
            "Select time range",
            (last_month, today),
            start_date,
            end_date,
            format="YYYY.MM.DD",
        )
        if len(selected_date_range) == 2:
            selected_date_range_str = (
                selected_date_range[0].strftime(date_format),
                selected_date_range[1].strftime(date_format)
            )
        else:
            selected_date_range_str = (
                last_month.strftime(date_format),
                today.strftime(date_format)
            )

        return selected_date_range_str

    @handle_exception(has_random_message_printed_out=True)
    def get_meal_record_date(
        self,
        has_user_intake_df_temp_empty:bool,
        layout_position=st
    ) -> datetime.datetime:
        if has_user_intake_df_temp_empty:
            return None
        meal_record_date = layout_position.date_input(
            "When was your meal consumed or plan to be consumed?",
            datetime.datetime.now(pytz.timezone('Australia/Sydney'))
        )
        return meal_record_date

    @handle_exception(has_random_message_printed_out=True)
    def display_ingredient_df(self, ingredient_df, layout_position=st):
        if not ingredient_df.empty:
            columns_to_display = ["Ingredient", "Estimated weight (g)"]
            layout_position.write(f'Here is our estimated weight of each ingredient for one serving of 🍕 {st.session_state["dish_description"]} 🍳:')
            layout_position.write(ingredient_df[columns_to_display])

    @handle_exception(has_random_message_printed_out=True)
    def display_user_intake_df(self, user_intake_df, layout_position=st):
        if isinstance(user_intake_df, pd.DataFrame):
            user_intake_df = user_intake_df.rename(columns={
                "actual_intake": "Actual Intake",
            })
            layout_position.dataframe(user_intake_df[["Nutrient", "Actual Intake"]].style.format({"Actual Intake": "{:.1f}"}))