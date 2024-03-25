import os
import logging
import threading
import streamlit as st
from core.main_app_miscellaneous import *
from core.calculate_nutrient_intake import NutrientMaster
from core.monali import read_data   ### TODO: rename
from core.monali import *

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
st.session_state['is_logged_in'] = True
st.session_state['user_name'] = "Tu"
# user_name = None
# user_id = "abc"
st.session_state['user_id'] = "tu_2@gmail.com"
###


main_app_miscellaneous.say_hello(user_name=st.session_state['user_name'])

# Main page with 2 tabs
track_new_meal_tab, user_recommended_intake_history_tab = st.tabs(
    [":green[Track the food I ate] 🍔", "See my nutrition intake history 📖"]
)

# Flow 3 - 12. User wants to get their historical data
logging.info("-----------Running get_user_historical_data()-----------")
selected_date_range = main_app_miscellaneous.select_date_range(layout_position=user_recommended_intake_history_tab)

user_recommended_intake_history_df = main_app_miscellaneous.show_user_historical_data_result(
    is_logged_in=st.session_state['is_logged_in'],
    user_id=st.session_state['user_id'],
    layout_position=user_recommended_intake_history_tab,
    selected_date_range=selected_date_range
)
logging.info("-----------Finished get_user_historical_data.-----------")

# 1. Get dish description from user and estimate its ingredients
dish_description = track_new_meal_tab.text_input("What have you eaten today? 😋").strip()
if 'dish_description' not in st.session_state and dish_description!= '':
    logging.info("-----------Running get_user_input_dish_and_estimate_ingredients()-----------")
    st.session_state['dish_description'] = dish_description

event = threading.Event()
while 'dish_description' not in st.session_state:
    event.wait()

if 'ingredient_df' not in st.session_state:
    ingredient_df = main_app_miscellaneous.get_user_input_dish_and_estimate_ingredients(
        dish_description=st.session_state['dish_description'],
        layout_position=track_new_meal_tab
    )
    st.session_state['ingredient_df'] = ingredient_df

while 'ingredient_df' not in st.session_state:
    event.wait()


if 'ingredient_df' in st.session_state and 'confirm_ingredient_weights_button' not in st.session_state:
    track_new_meal_tab.write("Press continue to get your nutrition estimation...")
    logging.info("-----------Finished get_user_input_dish_and_estimate_ingredients.-----------")
    confirm_ingredient_weights_button = track_new_meal_tab.button(label="Continue", key="confirm_ingredient_weights")
    if confirm_ingredient_weights_button:
        st.session_state['confirm_ingredient_weights_button'] = confirm_ingredient_weights_button

event = threading.Event()
while not st.session_state.get('confirm_ingredient_weights_button', False):
    event.wait()

# # 2-3. Nutrient actual intake
# # wait until user inputs

if 'total_nutrients_based_on_food_intake' not in st.session_state:
    Nutrient = NutrientMaster(openai_client=OPENAI_CLIENT)
    total_nutrients_based_on_food_intake = Nutrient.total_nutrients_based_on_food_intake(
                                            ingredients_from_user=st.session_state['ingredient_df'],
                                            layout_position=track_new_meal_tab
                                        )
    st.session_state['total_nutrients_based_on_food_intake'] = total_nutrients_based_on_food_intake
# 3. Check user's log in status
# @Nyan
# TODO: create the a table storing user's personal data: age, gender etc.
# Update this data if there are any changes.

while 'total_nutrients_based_on_food_intake' not in st.session_state:
    event.wait()
### TODO: replace this with actual input
user_intake_df_temp = st.session_state['total_nutrients_based_on_food_intake']
# user_intake_df_temp["dish_description"] = dish_description
# user_intake_df_temp["user_id"] = user_id
###

# # 4 + 5. Get user's age + gender
# # @Tu
if 'user_personal_data' not in st.session_state:
    logging.info("----------- Running get_user_personal_data()-----------")
    user_personal_data = main_app_miscellaneous.get_user_personal_data(
        is_logged_in=st.session_state['is_logged_in'],
        user_id=st.session_state['user_id'],
        has_user_intake_df_temp_empty=user_intake_df_temp.empty if isinstance(user_intake_df_temp, pd.DataFrame) else True,   ## handle case total_nutrients_based_on_food_intake is not a DataFrame but a dict
        layout_position=track_new_meal_tab
    )
    st.session_state['user_personal_data'] = user_personal_data
    logging.info("-----------Finished get_user_personal_data-----------")

# 6. Join with recommended intake
# Only run when we have user_personal_data
# @Tu
logging.info("-----------Running combine_and_show_users_recommended_intake()-----------")
if 'user_recommended_intake_result' not in st.session_state:
    user_recommended_intake_result = main_app_miscellaneous.combine_and_show_users_recommended_intake(
        user_personal_data=st.session_state['user_personal_data'],
        user_intake_df_temp=user_intake_df_temp,
        user_intake_df_temp_name="user_intake_df_temp",
        layout_position=track_new_meal_tab
    )
    st.session_state['user_recommended_intake_result'] = user_recommended_intake_result

user_recommended_intake_df = st.session_state['user_recommended_intake_result'].get("value")
logging.info("-----------Finished combine_and_show_users_recommended_intake-----------")

# # 6. @Michael
# # Visualize data

logging.info("-----------Running get_user_confirmation_and_try_to_save_their_data()-----------")
if st.session_state['user_recommended_intake_result'].get("status") == 200 and 'save_meal_result' not in st.session_state:

    ### TODO: replace this with actual input
    # is_logged_in = True
    user_intake_df_temp["user_id"] = st.session_state['user_id']
    ###

    save_meal_result = main_app_miscellaneous.get_user_confirmation_and_try_to_save_their_data(
        dish_description=st.session_state['dish_description'],
        user_id=st.session_state['user_id'],
        is_logged_in=st.session_state['is_logged_in'],
        layout_position=track_new_meal_tab
    )
    user_recommended_intake_df["result"] = save_meal_result.get("login_or_create_account")
    st.session_state['save_meal_result'] = save_meal_result

save_meal_result_persisted = st.session_state.get('save_meal_result')
if save_meal_result_persisted.get("status") == 200:
    storing_historical_data_result = save_meal_result_persisted.get("storing_historical_data_result")
    if storing_historical_data_result:
        storing_historical_data_message = storing_historical_data_result.get("message")
        track_new_meal_tab.write(storing_historical_data_message)
logging.info("-----------Finished get_user_confirmation_and_try_to_save_their_data-----------")

# 5. Recommend dish.
### TODO: aggregate user_recommended_intake_df to make sure the actual_intake column is the daily actual intake
### now actual_intake might just be one meal's actual intake
df_nutrient_data = user_recommended_intake_df.copy()

#### TODO: remove this
df_nutrient_data['daily_requirement_microgram'] = df_nutrient_data["daily_recommended_intake"]
df_nutrient_data["daily_actual_microgram"] = df_nutrient_data["actual_intake"]
####

if not df_nutrient_data.empty:

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