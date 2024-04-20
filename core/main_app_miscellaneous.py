import time
import jinja2
import pandas as pd
import streamlit as st
import datetime
import altair as alt
import numpy as np
from datetime import datetime as dt
from core.openai_api import *
from core.duckdb_connector import *
from core.utils import handle_exception, wait_while_condition_is_valid
from core.sql.user_daily_recommended_intake_history import anonymous_user_daily_nutrient_intake_query_template, combine_user_actual_vs_recommend_intake_logic
from core.visualization import users_recommended_intake_chart, user_historical_square_heatmap

RECOMMENDED_DAILY_NUTRIENT_INTAKE_TABLE_ID = "ilab.main.daily_nutrients_recommendation"
USER_DAILY_RECOMMENDED_INTAKE_HISTORY_VIEW_ID = "ilab.main.user_daily_recommended_intake_history"

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

    @handle_exception(has_random_message_printed_out=True)
    def get_user_age_and_gender(
        self,
        is_logged_in,
        user_id,
        layout_position,
        get_user_age_gender_message
    ):
        user_personal_data = {}
        if is_logged_in:
            user_personal_data = self.db.get_user_personal_data_from_database(user_id=user_id)

        if user_personal_data.get("status", 400) != 200:
            layout_position.info(get_user_age_gender_message)
            layout_position.write("But looks like we've just met for the first time, do you want to manually input your info?")
            user_personal_data = self.get_user_personal_info_manual_input(
                layout_position=layout_position
            )
        return user_personal_data

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
                get_user_age_gender_message="We need your age 📆 and gender ♀♂ to suggest the recommended intake.",
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
                # layout_position.dataframe(user_recommended_intake_df_to_show[columns_to_show]) ## TODO: remove this table once we have a working graph
                users_recommended_intake_chart(user_recommended_intake_df_to_show, layout_position=layout_position)
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
            "status": 200
        }
        has_historical_data_saved = layout_position.radio(
            "Do you want to save this meal info?",
            ("Yes", 'No'),
            index=None,
            horizontal=True
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
                layout_position.info("Looks like you haven't logged in, please log in at the top of this page to save this meal 😉", icon="🔐")
        return result


    @handle_exception(has_random_message_printed_out=True)
    def combined_intake_chart(self,df1, df2, layout_position=st):
        # Rename columns in df1 for clarity
       
        df1 = pd.DataFrame(df1['value'])
        df2 = pd.DataFrame(df2)
        
        df1.rename(columns={'nutrient': 'Nutrient'}, inplace=True)
        
        df1=df1[['Nutrient','daily_recommended_intake','actual_intake']]
        df2=df2[['Nutrient','Total_Nutrient_Value']]
        
        df2 = pd.merge(df1, df2, on='Nutrient')
        
        # Calculate remaining capacity for new intake
        df2['old_percentage'] = np.minimum((df2['actual_intake'] / df2['daily_recommended_intake']) * 100, 100)

        df2['remaining_capacity'] = 100 - df2['old_percentage']

        # Calculate new intake percentage and adjust not to exceed the remaining capacity
        df2['percentage'] = (df2['Total_Nutrient_Value'] / df2['daily_recommended_intake']) * 100
        df2['percentage'] = np.minimum(df2['percentage'], df2['remaining_capacity'])
        df2=df2[['Nutrient','daily_recommended_intake','Total_Nutrient_Value','percentage']]
        df2.rename(columns={'Total_Nutrient_Value': 'actual_intake'}, inplace=True)

        df1['type'] = 'Previous Meal'  # Adding a new column 'C' with all values set to 0
        df2['type'] = 'Recommended Meal'
        df1['percentage'] = np.minimum((df1['actual_intake'] / df1['daily_recommended_intake']) * 100, 100)

        # Join the dataframes on the 'Nutrient' column
        df = pd.concat([df1, df2], ignore_index=True)
            
        bar_chart = alt.Chart(df).mark_bar().encode(
            x=alt.X('sum(percentage)', title='Percentage Intake'),
            y=alt.Y('Nutrient', sort=alt.EncodingSortField(field='percentage', op='sum', order='ascending')),
            color=alt.Color('type', scale=alt.Scale(domain=['Previous Meal', 'Recommended Meal'],
                                                    range=['#096913', '#B6C471'])),
            tooltip=[
                alt.Tooltip('Nutrient', title='Nutrient:'),
                alt.Tooltip('type', title='Meal:'),
                alt.Tooltip('percentage', title='Intake Percentage:')
            ]
        ).properties(width=800,
        title=alt.TitleParams('Cumulative Intake Chart', anchor='middle'))

        # Show graph in the Streamlit layout position
        layout_position.altair_chart(bar_chart)



    @handle_exception(has_random_message_printed_out=True)
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
            view_id=USER_DAILY_RECOMMENDED_INTAKE_HISTORY_VIEW_ID,
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
                user_historical_square_heatmap(user_recommended_intake_history_df, layout_position=layout_position)
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
    def display_and_let_user_edit_ingredient(self, ingredient_df, layout_position=st):
        if not ingredient_df.empty:
            columns_to_display = ["Ingredient", "Estimated weight (g)"]
            layout_position.write(f'Here is our estimated weight of each ingredient for one serving of 🍴 {st.session_state["dish_description"]} 🍴:')
            
            # Show ingredients table and let users edit 
            edited_df = layout_position.data_editor(ingredient_df[columns_to_display], num_rows="dynamic")

            # Adding dish_description column back to the main dataframe
            edited_df["dish_description"] = ingredient_df["dish_description"]
            edited_df["dish_description"] = edited_df["dish_description"].fillna(ingredient_df["dish_description"].iloc[0])
            return edited_df

    @handle_exception(has_random_message_printed_out=True)
    def compare_and_return_the_smaller_date(
        self,
        date_input_1: datetime.datetime.date,
        date_input_2=None
    ) -> str:
        today = datetime.datetime.now(pytz.timezone('Australia/Sydney')).date()
        if date_input_1 is None:
            date_input_1 = today
        if date_input_2 is None:
            date_input_2 = today
        date_to_filter = date_input_1 if date_input_1 < date_input_2 else date_input_2
        return date_to_filter

    