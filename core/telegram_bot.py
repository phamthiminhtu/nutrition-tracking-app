import jinja2
import logging
import requests as re
import streamlit as st
from core.utils import handle_exception
from core.duckdb_connector import DuckdbConnector
from core.sql.user_telegram_info import insert_new_record_user_telegram_info_query_template


USER_TELEGRAM_INFO_TABLE_ID = "ilab.main.user_telegram_info"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
logger.disabled = True

class TelegramBot:

    def __init__(self, telegram_bot_token) -> None:
        self.telegram_bot_token = telegram_bot_token
        self.telegram_bot_base_url = f"https://api.telegram.org/bot{self.telegram_bot_token}/"
        self.jinja_environment = jinja2.Environment()
        self.db = DuckdbConnector()

    def fetch_bot_updates(self) -> list:
        bot_update_results = []
        telegram_bot_updates_url = self.telegram_bot_base_url + "getUpdates"
        bot_updates = re.get(telegram_bot_updates_url).json()
        if bot_updates.get("ok"):
            bot_update_results = bot_updates.get("result")
        return bot_update_results

    def extract_new_chat_id_from_user_names(
        self,
        bot_update_results: list,
        user_names: list
        ) -> dict:
        if not bot_update_results:
            return {
                "status": 400,
                "value": "empty bot_update_results"
            }

        user_name_chat_id_map = {}
        for result in bot_update_results:
            chat_info = result.get("message").get("chat")
            sender_user_name = chat_info.get("username")
            if sender_user_name in user_names:
                chat_id = chat_info.get("id")
                user_name_chat_id_map[sender_user_name] = chat_id
                break

            if len(user_name_chat_id_map.values()) == len(user_names):
                break
        if user_name_chat_id_map:
            result = {
                "status": 200,
                "value": user_name_chat_id_map
            }
        else:
            result = {
                "status": 400,
                "value": "User has not interacted with the bot"
            }

        return result

    def save_user_telegram_info_to_database(self, new_telegram_info_result):
        logger.info("------Running save_user_telegram_info_to_database------")
        if new_telegram_info_result.get("status") == 200:

            user_name_chat_id_map = new_telegram_info_result.get("value")

            for telegram_user_name, chat_id in user_name_chat_id_map.items():
                query_template = self.jinja_environment.from_string(
                    insert_new_record_user_telegram_info_query_template
                )
                query = query_template.render(
                    table_id=USER_TELEGRAM_INFO_TABLE_ID,
                    telegram_username=telegram_user_name,
                    telegram_chat_id=str(chat_id)
                )
                self.db.run_query(
                    sql=query
                )
        logger.info("------Finished running save_user_telegram_info_to_database------")

    def get_and_save_to_database_new_chat_ids_from_user_names(
        self,
        user_names: list
    ) -> dict:
        logger.info("------Running get_and_save_to_database_new_chat_ids_from_user_names------")
        bot_update_results = self.fetch_bot_updates()
        result = self.extract_new_chat_id_from_user_names(
            bot_update_results=bot_update_results,
            user_names=user_names
        )
        self.save_user_telegram_info_to_database(new_telegram_info_result=result)
        logger.info("------Finished running get_and_save_to_database_new_chat_ids_from_user_names------")
        return result

    def get_chat_id_from_database(self, user_name):
        logger.info("------Running get_chat_id_from_database------")
        chat_id = ''
        query_template = self.jinja_environment.from_string(
            """
                SELECT
                    MAX(telegram_chat_id) AS telegram_chat_id
                FROM {{ table_id }}
                WHERE telegram_username = '{{ input_user_name }}'
            """
        )
        query = query_template.render(
            table_id=USER_TELEGRAM_INFO_TABLE_ID,
            input_user_name=user_name
        )
        result = self.db.run_query(
            sql=query
        )
        # checks all the values of a list are true or false. Note: None, empty string and 0 are considered false.
        if all(result[0]):
            chat_id = result[0][0]
        logger.info("------Finished running get_chat_id_from_database------")
        return chat_id

    def get_chat_id(self, user_name) -> str:
        logger.info("------Running get_chat_id------")
        # check chat_id from the database
        chat_id = self.get_chat_id_from_database(user_name)

        if chat_id:
            return chat_id
        # if the user does not exist in the database
        # get_and_save_to_database_new_chat_ids_from_user_names
        chat_id_info = self.get_and_save_to_database_new_chat_ids_from_user_names(user_names=[user_name])
        if chat_id_info.get("status") == 200:
            chat_id = str(chat_id_info.get("value").get(user_name))
        logger.info("------Finished running get_chat_id------")
        return chat_id


    def send_telegram_message(
        self,
        chat_id,
        message
    ) -> None:
        logger.info("------Running send_telegram_message------")
        sending_message_result = ""
        # URL for the Telegram Bot API endpoint to send messages
        telegram_bot_updates_url = self.telegram_bot_base_url + "sendMessage"

        # Payload for the HTTP POST request
        payload = {
            'chat_id': chat_id,
            'text': message
        }

        response = re.post(telegram_bot_updates_url, json=payload)

        if response.status_code == 200:
            sending_message_result = "📩 Message sent successfully!"
        else:
            raise Exception(f"Failed to send message. Status code: {response.status_code}")
        logger.info("------Finished running send_telegram_message------")
        return sending_message_result

    @handle_exception(funny_message="Oops, we couldn't send the recipe 😞 Double check your Telegram user name or try again later")
    def send_message_to_user_name(
        self,
        user_name,
        message,
        layout_position=st
    ) -> None:
        logger.info("------Running send_message_to_user_name------")
        user_name_trim = user_name.strip()
        layout_position.write("Sending you the awesome recipe 🥘 ...")
        chat_id = self.get_chat_id(user_name=user_name_trim)
        sending_message_result_dict = {"status": 0}
        if chat_id:
            chat_id = int(chat_id)
            sending_message_result = self.send_telegram_message(chat_id=chat_id, message=message)
            sending_message_result_dict["sending_message_result"] = sending_message_result
            if sending_message_result:
                sending_message_result_dict["status"] = 200
                layout_position.write(sending_message_result)
            else:
                layout_position.write("We couldn't send the recipe 😞 Double check your Telegram user name or try again later")
        else:
            layout_position.write("We couldn't send the recipe 😞 Double check your Telegram user name or try again later")
        logger.info("------Finished running send_message_to_user_name------")
        return sending_message_result_dict