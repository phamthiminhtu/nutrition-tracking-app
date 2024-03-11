import jinja2
import threading
import pandas as pd
import streamlit as st
from core.duckdb_connector import *
from core.utils import handle_exception
from core.sql.user_daily_nutrient_intake import anonymous_user_daily_nutrient_intake_query_template, combine_user_actual_vs_recommend_intake_logic


RECOMMENDED_DAILY_NUTRIENT_INTAKE_TABLE_ID = "ilab.main.recommended_nutrients"
USER_INTAKE_COLUMNS_MAP = {
    "gender": "Gender",
    "age": "Age",
    "nutrient": "Nutrient",
    "actual_intake": "Actual intake",
    "daily_recommended_intake": "Daily recommended intake",
    "unit": "Unit",
    "intake_diff_percent": "Intake difference (%)"
}

class MainAppMiscellaneous:
    def __init__(self) -> None:
        self.jinja_environment = jinja2.Environment()
        self.db = DuckdbConnector()

    @handle_exception(has_random_message_printed_out=True)
    def get_user_recommended_intake(
            self,
            user_intake_df_temp_name
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
        user_personal_data,
        user_intake_df_temp,
        user_intake_df_temp_name
    ) -> pd.DataFrame:
        if user_personal_data.get("status") == 200:
            user_intake_df_temp["gender"] = user_personal_data.get("gender")
            user_intake_df_temp["age"] = user_personal_data.get("age")

            user_recommended_intake_df = self.get_user_recommended_intake(
                user_intake_df_temp_name=user_intake_df_temp_name
            )
            user_recommended_intake_df_to_show = user_recommended_intake_df.rename(columns=USER_INTAKE_COLUMNS_MAP)
            columns_to_show = USER_INTAKE_COLUMNS_MAP.values()
            st.dataframe(user_recommended_intake_df_to_show[columns_to_show])
        return user_recommended_intake_df

    @handle_exception(has_random_message_printed_out=True)
    def check_whether_user_needs_to_input_personal_info_manually(
            self,
            user_id,
            is_logged_in,
            time_out=120
        ):
        has_user_personal_info_input_manually = True
        user_input_personal_info_agreement = None
        st.write("We need your age and gender to suggest the recommended intake.")
        user_input_personal_info_agreement = st.selectbox(
            "But looks like we just meet for the first time, do you want to manually input your info?",
            ("Yes", 'No'),
            index=None,
            placeholder="Select your answer..."
        )
        event = threading.Event()
        # if user does not confirm within time_out time period
        # return has_user_personal_info_input_manually as True
        while user_input_personal_info_agreement is None:
            if event.wait(time_out):
                event.clear()
        if user_input_personal_info_agreement != "Yes":
            has_user_personal_info_input_manually = False
        return has_user_personal_info_input_manually

    def get_user_personal_info_manual_input(self):
        event = threading.Event()
        # wait until user input
        user_gender = st.selectbox(
            "Please select your gender.",
            ("male", 'female'),
            index=None,
            placeholder="Select your gender..."
        )
        user_age_input = st.number_input("How old are you?", value=None, placeholder="Type a number...")
        while user_age_input is None or user_gender is None:
            event.wait()
            event.clear()

        user_personal_data = {
            "status": 200,
            "gender": user_gender,
            "age": float(user_age_input)
        }
        return user_personal_data

    def get_user_personal_data_from_database(self, user_id):
        user_personal_data = self.db.get_user_personal_data(user_id=user_id)
        return user_personal_data

    @handle_exception(has_random_message_printed_out=True)
    def get_user_personal_data(self, is_logged_in, user_id):
        user_personal_data = {}
        if is_logged_in:
            user_personal_data = self.get_user_personal_data_from_database(user_id=user_id)

        if user_personal_data.get("status", 400) != 200:
            has_user_personal_info_input_manually = self.check_whether_user_needs_to_input_personal_info_manually(
                user_id=user_id,
                is_logged_in=is_logged_in
            )
            # If user has not logged in or we don't have user's data, manual input age + gender
            if has_user_personal_info_input_manually:
                user_personal_data = self.get_user_personal_info_manual_input()
        return user_personal_data

    def get_user_confirmation_and_try_to_save_their_data(self, dish_description, user_id, is_logged_in):
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

