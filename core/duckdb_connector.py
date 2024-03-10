import pytz
import duckdb
import hashlib
import datetime
import streamlit as st
from core.utils import handle_exception
from core.sql.user_nutrient_intake_history import insert_new_record_user_nutrient_intake_history_query

USER_NUTRIENT_INTAKE_HISTORY_TABLE_NAME = "ilab.main.user_nutrient_intake_history"

class DuckdbConnector:

    def __init__(
            self,
            database_path="data/ilab.db",
            read_only=False
        ) -> None:
        self.database_path = database_path
        self.read_only = read_only

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
            FROM {USER_NUTRIENT_INTAKE_HISTORY_TABLE_NAME}
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

    def get_user_confirmation_for_duplicated_meal_id(self, is_existing_meal_id):
        has_meal_id_stored = True
        if is_existing_meal_id:
            user_confirmation = st.selectbox(
                "The same meal has been recorded within 60 seconds, do you still want to proceed?",
                ("Yes", 'No')
            )
            if user_confirmation == 'No':
                has_meal_id_stored = False
        return has_meal_id_stored

    @handle_exception(has_random_message_printed_out=True)
    def save_user_nutrient_intake(self, dish_description, user_id):
        has_meal_id_stored = True
        meal_id_info = self.generate_and_check_meal_id(dish_description=dish_description, user_id=user_id)
        is_existing_meal_id = meal_id_info.get("is_existing_meal_id")
        if is_existing_meal_id:
            has_meal_id_stored = self.get_user_confirmation_for_duplicated_meal_id(is_existing_meal_id=is_existing_meal_id)
        if has_meal_id_stored:
            query = insert_new_record_user_nutrient_intake_history_query.format(
                    table_name=USER_NUTRIENT_INTAKE_HISTORY_TABLE_NAME
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
            result = {
                "status": 200,
                "message": "Successfully saved your meal!"
            }
        return result

