import os
import logging
import threading
import pickle

from pathlib import Path
from core.openai_api import *
from core.duckdb_connector import *
from core.main_app_miscellaneous import *


OPENAI_API_KEY = "OPENAI_API_KEY"
OPENAI_CLIENT = OpenAI(
  api_key=os.environ.get(OPENAI_API_KEY),
)
main_app_miscellaneous = MainAppMiscellaneous(openai_client=OPENAI_CLIENT)
logging.basicConfig(level=logging.INFO)
st.set_page_config(layout='wide')


# @Nyan
# Login option.
# A class in a python file (Nyan.py file - please rename it) e.g. Authenticator = Authenticator(), with methods like:
# Authenticator.log_in()
# Authenticator.recover_password()
# Authenticator.create_new_account()

dish_description = st.text_input(
    "What have you eaten today? 😋"
)
st.session_state["dish_description"] = dish_description

openai_api = OpenAIAssistant(openai_client=OPENAI_CLIENT)

if dish_description:
    ingredient_estimation_prompt = f"""
                        Given the input which is the description of a dish,
                        guess the ingredients of that dish
                        and estimate the weight of each ingredient in gram for one serve,
                        just 1 estimate for each ingredient and return the output in a python dictionary.
                        Input ```{dish_description}```
                    """
    ingredient_df = openai_api.estimate_and_extract_dish_info(
        dish_description=dish_description,
        ingredient_estimation_prompt=ingredient_estimation_prompt
    )

# 2-3. Nutrient actual intake
# @Michael @Johnny
    # Ask users' information:
        # age, gender, date
    # I think your methods should be in the same class in the same python file (Michael_Johnny.py file - please rename it).
    # E.g. NutrientMaster = NutrientMaster()
    # NutrientMaster.calculate_recommended_intake_from_database()
    # NutrientMaster.calculate_recommended_intake_using_openapi()


# 3. Check user's log in status
# @Nyan
# TODO: create the a table storing user's personal data: age, gender etc.
# Update this data if there are any changes.


### TODO: replace this with actual input
user_intake_df_temp = pd.DataFrame(
    [
        {
            "user_id": "tu@gmail.com",
            "gender": "female",
            "age": 20,
            "dish_description": "beef burger",
            "nutrient": "Protein",
            "actual_intake": 2,
        },
        {
            "user_id": "tu@gmail.com",
            "gender": "female",
            "age": 20,
            "dish_description": "beef burger",
            "nutrient": "Vitamin A",
            "actual_intake": 3,
        }
    ]
)

###

# 4 + 5. Get user's age + gender
# @Tu
logging.info("----------- Running get_user_personal_data()-----------")
user_personal_data = main_app_miscellaneous.get_user_personal_data(
    is_logged_in=is_logged_in,
    user_id=user_id,
    has_user_intake_df_temp_empty=user_intake_df_temp.empty,
    layout_position=track_new_meal_tab
)
logging.info("-----------Finished get_user_personal_data-----------")

# 6. Join with recommended intake
# Only run when we have user_personal_data
# @Tu
logging.info("-----------Running combine_and_show_users_recommended_intake()-----------")
user_recommended_intake_df = main_app_miscellaneous.combine_and_show_users_recommended_intake(
    user_personal_data=user_personal_data,
    user_intake_df_temp=user_intake_df_temp,
    user_intake_df_temp_name="user_intake_df_temp",
    layout_position=track_new_meal_tab
)
logging.info("-----------Finished combine_and_show_users_recommended_intake-----------")

# 6. @Michael
# Visualize data


# 7. Store data into duckdb
# @Tu
### TODO: replace this with actual input
# is_logged_in = True
user_recommended_intake_df["user_id"] = user_id
###

logging.info("-----------Running get_user_confirmation_and_try_to_save_their_data()-----------")
if not user_recommended_intake_df.empty:
    result = main_app_miscellaneous.get_user_confirmation_and_try_to_save_their_data(
        dish_description=dish_description,
        user_id=user_id,
        is_logged_in=is_logged_in,
        layout_position=track_new_meal_tab
    )
    login_or_create_account = result.get("login_or_create_account")
logging.info("-----------Finished get_user_confirmation_and_try_to_save_their_data-----------")


# 5. Recommend dish.
# @Anika
# A python class in a separate file (Anika.py - Please rename it), containing different methods:
    # E.g. DishRecommender = DishRecommender()
    # DishRecommender.get_user_preference()
    # DishRecommender.recommend_recipe()
# Ask user's preference (diet/ what do you have left in your fridge?)
