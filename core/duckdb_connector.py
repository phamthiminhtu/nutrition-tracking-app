import pytz
import duckdb
import jinja2
import hashlib
import datetime
import threading
import streamlit as st
from core.utils import handle_exception
from core.sql.user_nutrient_intake_history import insert_new_record_user_nutrient_intake_history_query_template


USER_NUTRIENT_INTAKE_HISTORY_TABLE_ID = "ilab.main.user_nutrient_intake_history"
USER_DAILY_RECOMMENDED_INTAKE_HISTORY_TABLE_ID = "ilab.main.user_daily_recommended_intake_history"
USER_PROFILES_TABLE_ID = "ilab.main.users"

class DuckdbConnector:

    def __init__(
            self,
            database_path="data/ilab.db",
            read_only=False
        ) -> None:
        self.database_path = database_path
        self.read_only = read_only
        self.jinja_environment = jinja2.Environment()

    def run_query(self, sql, result_format='list', parameters=None) -> list:
        """
            - Open connection to DuckDB database (default database path is data/ilab.db)
            - Run the provided sql.
            - Convert the query result into the specified result_format. Supported format:
                - list
                - dataframe
                - polardataframe
            - Close connection.
        """
        if parameters is None:
            parameters = {}
        with duckdb.connect(self.database_path, read_only=self.read_only) as con:
            query_connector = con.execute(sql, parameters=parameters)
            if result_format == 'list':
                query_result = query_connector.fetchall()
            elif result_format == 'dataframe':
                query_result = query_connector.df()
            elif result_format == 'polardataframe':
                query_result = query_connector.pl()
            else:
                raise Exception(f"The result_format {result_format} is not supported.")
            # the context manager closes the connection automatically
        return query_result

    def generate_meal_fingerprint(self, dish_description, user_id):
        created_datetime = datetime.datetime.now(tz=pytz.timezone('Australia/Sydney'))
        meal_fingerprint = hashlib.sha256(f"{user_id}||{dish_description}".encode('utf-8')).hexdigest()
        date_format = "%Y-%m-%d %H:%M:%S"
        result = {
            "meal_fingerprint": meal_fingerprint,
            "created_datetime_tzsyd": created_datetime.strftime(date_format),
            "date_format": date_format
        }
        return result

    def generate_and_check_meal_id(self, dish_description, user_id):
        meal_info = self.generate_meal_fingerprint(dish_description=dish_description, user_id=user_id)
        meal_fingerprint, meal_created_datetime = meal_info.get("meal_fingerprint"), meal_info.get("created_datetime_tzsyd")
        is_existing_meal_id = False
        query = f"""
            SELECT
                *
            FROM {USER_NUTRIENT_INTAKE_HISTORY_TABLE_ID}
            WHERE
                -- the same meal inserted within 60s
                meal_fingerprint = '{meal_fingerprint}'
                AND DATE_DIFF('second', created_datetime_tzsyd, TIMESTAMP '{meal_created_datetime}') < 60
        """
        result = self.run_query(sql=query)
        if result:
            is_existing_meal_id = True
        meal_info["meal_id"] = hashlib.sha256(f"{meal_fingerprint}||{meal_created_datetime}".encode('utf-8')).hexdigest()
        meal_info["is_existing_meal_id"] = is_existing_meal_id
        return meal_info

    def get_user_confirmation_for_duplicated_meal_id(self) -> bool:
        user_confirmation = st.selectbox(
            "The same meal has been recorded within 60 seconds, do you still want to proceed?",
            ("Yes", 'No'),
            index=None,
            placeholder="Select your answer..."
        )

        # wait for user's confirmation
        event = threading.Event()
        while user_confirmation is None:
            event.wait()
            event.clear()

        if user_confirmation == 'Yes':
            has_meal_id_stored = True
        if user_confirmation == 'No':
            has_meal_id_stored = False
        return has_meal_id_stored

    def save_user_nutrient_intake(
        self,
        user_intake_df_temp_name: str,
        meal_id_info: dict
    ) -> None:
        query_template = self.jinja_environment.from_string(
            insert_new_record_user_nutrient_intake_history_query_template
        )
        query = query_template.render(
            table_id=USER_NUTRIENT_INTAKE_HISTORY_TABLE_ID,
            user_intake_df_temp_name=user_intake_df_temp_name
        )
        parameters = {
            "meal_id": meal_id_info.get("meal_id"),
            "meal_fingerprint": meal_id_info.get("meal_fingerprint"),
            "created_datetime_tzsyd": meal_id_info.get("created_datetime_tzsyd"),
        }
        self.run_query(
            sql=query,
            parameters=parameters
        )

    def save_user_data(
        self,
        dish_description: str,
        user_id: str,
        user_intake_df_temp_name: str
    ) -> dict:

        # check whether meal_id already exists
        meal_id_info = self.generate_and_check_meal_id(
            dish_description=dish_description,
            user_id=user_id
        )
        result = {"status": 200}
        is_existing_meal_id = meal_id_info.get("is_existing_meal_id")

        if is_existing_meal_id:
            has_meal_id_stored = self.get_user_confirmation_for_duplicated_meal_id()
            if not has_meal_id_stored:
                result["message"] = "Successfully discarded this meal!"
                return result

        # save data either when meal_id does not exist
        # or user confirmed to save existing meal_id
        self.save_user_nutrient_intake(
            user_intake_df_temp_name=user_intake_df_temp_name,
            meal_id_info=meal_id_info
        )
        result["message"] = "Successfully saved your meal!"
        return result

    @handle_exception(has_random_message_printed_out=True)
    def get_user_personal_data_from_database(
            self,
            user_id,
            table_id=USER_PROFILES_TABLE_ID  #TODO: replace with user's personal data table
        ) -> dict:
        user_personal_data = {}
        query_template = self.jinja_environment.from_string(
            """
                SELECT
                    user_id,
                    MAX(gender),
                    MAX(age)
                FROM {{ table_id }}
                WHERE user_id = '{{ user_id }}'
                GROUP BY user_id
            """
        )
        query = query_template.render(
            table_id=table_id,
            user_id=user_id
        )
        result = self.run_query(sql=query)
        if result:
            user_personal_data = {
                "status": 200,
                "user_id": result[0][0],
                "gender": result[0][1],
                "age": result[0][2]
            }
        return user_personal_data
