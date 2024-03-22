import os
import logging
import threading
import streamlit as st
from core.openai_api import *
from core.duckdb_connector import *
from core.main_app_miscellaneous import *
from core.calculate_nutrient_intake import NutrientMaster
from core.monali import read_data   ### TODO: rename
from core.monali import *

file_path = "/Users/monalipatil/Monali/MDSI-Semester1/iLab Capstone Project/Assignment2/ilab/data/csv/nutrients_data.csv"

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

### TODO: replace this with actual input
is_logged_in = False
# user_name = "Tu"
user_name = None
# user_id = "abc"
user_id = "tu@gmail.com"
###

main_app_miscellaneous.say_hello(user_name=user_name)

# Main page with 2 tabs
track_new_meal_tab, user_recommended_intake_history_tab = st.tabs(
    [":green[Track the food I ate] 🍔", "See my nutrition intake history 📖"]
)

# Flow 3 - 12. User wants to get their historical data
logging.info("-----------Running get_user_historical_data()-----------")
selected_date_range = main_app_miscellaneous.select_date_range(layout_position=user_recommended_intake_history_tab)

user_recommended_intake_history_df = main_app_miscellaneous.show_user_historical_data_result(
    is_logged_in=is_logged_in,
    user_id=user_id,
    layout_position=user_recommended_intake_history_tab,
    selected_date_range=selected_date_range
)
logging.info("-----------Finished get_user_input_dish_and_estimate_ingredients.-----------")


# 1. Get dish description from user and estimate its ingredients
logging.info("-----------Running get_user_input_dish_and_estimate_ingredients()-----------")
dish_description = track_new_meal_tab.text_input("What have you eaten today? 😋").strip()
ingredient_df = main_app_miscellaneous.get_user_input_dish_and_estimate_ingredients(
    dish_description=dish_description,
    layout_position=track_new_meal_tab
)

# wait until user input
event = threading.Event()
while not dish_description:
    event.wait()
    event.clear()
logging.info("-----------Finished get_user_input_dish_and_estimate_ingredients.-----------")

# 2-3. Nutrient actual intake
if track_new_meal_tab.button("Go"):
    Nutrient = NutrientMaster(openai_client=OPENAI_CLIENT)
    total_nutrients_based_on_food_intake = Nutrient.total_nutrients_based_on_food_intake(
                                                    ingredients_from_user=ingredient_df,
                                                    layout_position=track_new_meal_tab)
    
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
df_nutrient_data = read_data(file_path)

dishrecommend = DishRecommender(openai_client=OPENAI_CLIENT)

logging.info("-----------Running calculate_intake_difference-----------")
nutrient_info = dishrecommend.calculate_intake_difference(df_nutrient_data)
logging.info("-----------Finished calculate_intake_difference-----------")

logging.info("-----------Running get_user_input-----------")        
cuisine, allergies, ingredients = dishrecommend.get_user_input()
logging.info("-----------Finished get_user_input-----------")

logging.info("-----------Running get_dish_recommendation-----------")
if st.button("Recommend Dish"):
    recommended_dish = dishrecommend.get_dish_recommendation(nutrient_info, cuisine, ingredients, allergies)
    st.write(recommended_dish)
logging.info("-----------Finished get_dish_recommendation-----------")