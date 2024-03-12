import time
import jinja2
import threading
import pandas as pd
import streamlit as st
from core.openai_api import *
from core.duckdb_connector import *
from core.utils import handle_exception
from core.sql.user_daily_nutrient_intake import anonymous_user_daily_nutrient_intake_query_template, combine_user_actual_vs_recommend_intake_logic


RECOMMENDED_DAILY_NUTRIENT_INTAKE_TABLE_ID = "ilab.main.daily_nutrients_recommendation"
USER_INTAKE_COLUMNS_DICT = {
    "gender": "Gender",
    "age": "Age",
    "dish_description": "Dish",
    "nutrient": "Nutrient",
    "actual_intake": "Actual intake",
    "daily_recommended_intake": "Daily recommended intake",
    "measurement": "Measurement",
    "intake_diff_percent": "Intake difference (%)"
}

class MainAppMiscellaneous:
    def __init__(self, openai_client) -> None:
        self.jinja_environment = jinja2.Environment()
        self.db = DuckdbConnector()
        self.openai_api = OpenAIAssistant(openai_client=openai_client)

    @handle_exception(has_random_message_printed_out=True)
    def get_user_input_dish_and_estimate_ingredients(
        self,
        dish_description: str
    ) -> pd.DataFrame:
        # st.session_state["dish_description"] = dish_description
        ingredient_df = pd.DataFrame()
        if dish_description:
            ingredient_estimation_prompt = f"""
                Given the input which is the description of a dish,
                guess the ingredients of that dish
                and estimate the weight of each ingredient in gram for one serve,
                just 1 estimate for each ingredient and return the output in a python dictionary.
                If input is not food, return an empty dictionary.
                Input ```{dish_description}```
            """
            ingredient_df = self.openai_api.estimate_and_extract_dish_info(
                dish_description=dish_description,
                ingredient_estimation_prompt=ingredient_estimation_prompt
            )
            ingredient_df["dish_description"] = dish_description
        return ingredient_df

    @handle_exception(has_random_message_printed_out=True)
    def check_whether_user_needs_to_input_personal_info_manually(self) -> bool:
        has_user_personal_info_input_manually = True
        user_input_personal_info_agreement = None
        st.write("We need your age 📆 and gender ♀♂ to suggest the recommended intake.")
        user_input_personal_info_agreement = st.selectbox(
            "But looks like we've just met for the first time, do you want to manually input your info?",
            ("Yes, let's do it!", 'No'),
            placeholder="Select your answer..."
        )
        if user_input_personal_info_agreement == "No":
            has_user_personal_info_input_manually = False
        return has_user_personal_info_input_manually

    def get_user_personal_info_manual_input(self) -> dict:

        user_gender = st.selectbox(
            "Please select your gender",
            ("male", 'female'),
            index=None,
            placeholder="Select your gender..."
        )
        user_age_input = st.number_input("How old are you?", value=None, placeholder="Type a number...")

        # wait until user input
        event = threading.Event()
        while user_age_input is None or user_gender is None:
            event.wait()
            event.clear()

        user_personal_data = {
            "status": 200,
            "gender": user_gender,
            "age": float(user_age_input)
        }
        return user_personal_data

    @handle_exception(has_random_message_printed_out=True)
    def get_user_personal_data(
        self,
        is_logged_in: bool,
        user_id: str,
        has_user_intake_df_temp_empty: bool
    ) -> dict:
        user_personal_data = {}
        if not has_user_intake_df_temp_empty:
            if is_logged_in:
                user_personal_data = self.db.get_user_personal_data(user_id=user_id)

            if user_personal_data.get("status", 400) != 200:
                has_user_personal_info_input_manually = self.check_whether_user_needs_to_input_personal_info_manually()
                # If user has not logged in or we don't have user's data, get them manually input their age + gender
                if has_user_personal_info_input_manually:
                    user_personal_data = self.get_user_personal_info_manual_input()
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
        user_intake_df_temp_name: str
    ) -> pd.DataFrame:
        user_recommended_intake_df = pd.DataFrame()

        if user_personal_data.get("status") == 200 and not user_intake_df_temp.empty:
            user_intake_df_temp["gender"] = user_personal_data.get("gender")
            user_intake_df_temp["age"] = user_personal_data.get("age")

            user_recommended_intake_df = self.get_user_recommended_intake(
                user_intake_df_temp_name=user_intake_df_temp_name
            )
            user_recommended_intake_df_to_show = user_recommended_intake_df.rename(columns=USER_INTAKE_COLUMNS_DICT)
            columns_to_show = USER_INTAKE_COLUMNS_DICT.values()
            st.write("Just one moment, we are doing the science 😎 ...")
            time.sleep(1)
            if not user_recommended_intake_df_to_show.empty:
                st.dataframe(user_recommended_intake_df_to_show[columns_to_show])
            else:
                st.write("Oops! Turned out it's pseudoscience 🫥 We cannot estimate your intake just yet 😅 Please try again later...")

        return user_recommended_intake_df

    @handle_exception(has_random_message_printed_out=True)
    def get_user_confirmation_and_try_to_save_their_data(
        self,
        dish_description: str,
        user_id: str,
        is_logged_in: bool
    ):
        result = {
            "status": 200,
            "login_or_create_account": "No"
        }
        has_historical_data_saved = st.selectbox(
            "Do you want to save this meal info?",
            ("Yes", 'No'),
            index=None,
            placeholder="Select your answer..."
        )
        if has_historical_data_saved == "Yes":
            if is_logged_in:
                storing_historical_data_result = self.db.save_user_data(
                    dish_description=dish_description,
                    user_id=user_id,
                    user_intake_df_temp_name="user_intake_df_temp"
                )
                if storing_historical_data_result.get("status") == 200:
                    storing_historical_data_message = storing_historical_data_result.get("message")
                    st.write(storing_historical_data_message)
            else:
                login_or_create_account = st.selectbox(
                    "Looks like you haven't logged in, do you want to log in to save this meal's intake estimation?",
                    ("Yes", 'No'),
                    index=None,
                    placeholder="Select your answer..."
                )
                result["login_or_create_account"] = login_or_create_account
        return result

