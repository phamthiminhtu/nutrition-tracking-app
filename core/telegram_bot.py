import requests as re
from core.utils import handle_exception


class TelegramBot:

    def __init__(self, telegram_bot_token) -> None:
        self.telegram_bot_token = telegram_bot_token
        self.telegram_bot_base_url = f"https://api.telegram.org/bot{self.telegram_bot_token}/"

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

        result = {
            "status": 200,
            "value": user_name_chat_id_map
        }

        return result

    def get_new_chat_ids_from_user_names(
        self,
        user_names: list
    ) -> dict:
        bot_update_results = self.fetch_bot_updates()
        result = self.extract_new_chat_id_from_user_names(
            bot_update_results=bot_update_results,
            user_names=user_names
        )
        return result

    def send_telegram_message(
        self,
        chat_id,
        message
    ) -> None:
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
        return sending_message_result

    @handle_exception(funny_message="Oops, we couldn't send the recipe 😞 Double check your Telegram user name or try again later")
    def send_message_to_user_name(
        self,
        user_name,
        message,
        layout_position
    ) -> None:
        user_name_trim = user_name.strip()
        layout_position.write("Sending you the awesome recipe 🥘 ...")
        chat_id_info = self.get_new_chat_ids_from_user_names(
            user_names=[user_name_trim]
        )
        sending_message_result_dict = {"status": 200}
        if chat_id_info.get("status") == 200:
            chat_id = chat_id_info.get("value").get(user_name_trim)
            sending_message_result = self.send_telegram_message(chat_id=chat_id, message=message)
            sending_message_result_dict["sending_message_result"] = sending_message_result
            if sending_message_result:
                layout_position.write(sending_message_result)
            else:
                layout_position.write("We couldn't send the recipe 😞 Double check your Telegram user name or try again later")
        return sending_message_result_dict