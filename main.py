import os
import logging
import threading
import streamlit as st
from core.main_app_miscellaneous import *
from core.calculate_nutrient_intake import NutrientMaster
from core.diabetes_assessor import *
from core.telegram_bot import *
from core.monali import read_data   ### TODO: rename
from core.monali import *
from core.auth import *
from core.utils import wait_while_condition_is_valid

OPENAI_API_KEY = "OPENAI_API_KEY"
OPENAI_CLIENT = OpenAI(
  api_key=os.environ.get(OPENAI_API_KEY),
)
TELEGRAM_BOT_API_KEY_ENV_KEY = "TELEGRAM_BOT_API_KEY"
TELEGRAM_BOT_TOKEN = os.environ.get(TELEGRAM_BOT_API_KEY_ENV_KEY)
DIABETES_MODEL_PATH = "core/ml_models/diabetes_random_forest_model.sav"

main_app_miscellaneous = MainAppMiscellaneous(openai_client=OPENAI_CLIENT)
diabetes_assessor = DiabetesAssessor(model_path=DIABETES_MODEL_PATH)
telegram_bot = TelegramBot(telegram_bot_token=TELEGRAM_BOT_TOKEN)
authenticator = Authenticator()
logging.basicConfig(level=logging.INFO)
st.set_page_config(layout='wide')

st.session_state['logged_in'] = False
st.session_state['expander'] = False
# @Nyan
# Login option.
# A class in a python file (Nyan.py file - please rename it) e.g. Authenticator = Authenticator(), with methods like:
# Authenticator.log_in()
# Authenticator.recover_password()
# Authenticator.create_new_account()
if 'login_button' not in st.session_state:
        st.session_state.login_button = False

def click_login_button():
    st.session_state.login_button = True
    #if not st.session_state.get('authentication_status'):
    st.session_state["name"], st.session_state["logged_in"], st.session_state["username"] = authenticator.log_in()
    print('____________',st.session_state.get("name"),'___________',st.session_state.get("logged_in"))
login_button = st.sidebar.button('Login',disabled=st.session_state.get('logged_in'), on_click=click_login_button())
with st.sidebar:
    with st.expander('Register new user'):
        st.session_state.expander = True
        authenticator.register_user_form()
    if st.session_state.get('logged_in'):
        authenticator.log_out()

### TODO: replace this with actual input
        #print(st.session_state.get('email'))
st.session_state['is_logged_in'] = st.session_state.get("logged_in")
st.session_state['user_name'] = st.session_state.get("username")
#print(authenticator.get_user_id(st.session_state.get('username')))
st.session_state['user_id'] = authenticator.get_user_id(st.session_state.get('username'))
# user_name = None
# user_id = "abc"
#st.session_state['user_id'] = "tu_4@gmail.com"
# st.session_state["user_id"] = None
def reset_session_state():
    st.session_state['dish_description'] = None
    st.session_state['ingredient_df'] = None
    st.session_state['confirm_ingredient_weights_button'] = False
    st.session_state['total_nutrients_based_on_food_intake'] = None
    st.session_state['user_personal_data'] = None
    st.session_state['assess_diabetes_risk_button'] = False
    st.session_state['get_intake_history_button'] = False
    st.session_state['user_age_and_gender'] = None  # for diabetes prediction
    st.session_state['has_fruit_and_veggie_intake'] = True
    st.session_state['save_meal_result'] = None
    st.session_state['user_telegram_user_name'] = None
    st.session_state['recommended_recipe'] = None


main_app_miscellaneous.say_hello(user_name=st.session_state['user_name'])

# Main page with 2 tabs
track_new_meal_tab, user_recommended_intake_history_tab, assess_diabetes_risk_tab = st.tabs(
    [":green[Track the food I ate] 🍔", "See my nutrition intake history 📖", "Assess my diabetes risk 👩‍⚕👨‍⚕"]
)

# 1. Get dish description from user and estimate its ingredients
dish_description = track_new_meal_tab.text_input("What have you eaten today? 😋").strip()
if dish_description != st.session_state.get('dish_description', '###') and dish_description!= '':
    reset_session_state()   # rerun the whole app when user inputs a new dish
    st.session_state['dish_description'] = dish_description

# Flow 3 - 12. User wants to get their historical data
get_intake_history_button = user_recommended_intake_history_tab.button("I want to get my nutrition intake history")
if not st.session_state.get('get_intake_history_button') and get_intake_history_button:
    st.session_state['get_intake_history_button'] = True

if st.session_state.get('get_intake_history_button'):
    logging.info("-----------Running get_user_historical_data()-----------")
    selected_date_range = main_app_miscellaneous.select_date_range(layout_position=user_recommended_intake_history_tab)
    user_recommended_intake_history_result = main_app_miscellaneous.show_user_historical_data_result(
        is_logged_in=st.session_state['is_logged_in'],
        user_id=st.session_state['user_id'],
        layout_position=user_recommended_intake_history_tab,
        selected_date_range=selected_date_range
    )
    user_recommended_intake_history_df = user_recommended_intake_history_result.get("value")
    st.session_state['user_recommended_intake_history_df'] = user_recommended_intake_history_df
    logging.info("-----------Finished get_user_historical_data.-----------")


# Diabetes prediction
assess_diabetes_risk_button = assess_diabetes_risk_tab.button("Start assessing my diabetes risk")
if not st.session_state.get('assess_diabetes_risk_button') and assess_diabetes_risk_button:
    st.session_state['assess_diabetes_risk_button'] = True


if st.session_state.get('assess_diabetes_risk_button'):
    if st.session_state.get('user_age_and_gender') is None:
        logging.info("----------- Running main_app_miscellaneous.get_user_age_and_gender()-----------")
        user_age_and_gender =  main_app_miscellaneous.get_user_age_and_gender(
            is_logged_in=st.session_state['is_logged_in'],
            user_id=st.session_state['user_id'],
            get_user_age_gender_message="First of all, we need your age 📆 and gender ♀♂ to assess your diabetes risk.",
            layout_position=assess_diabetes_risk_tab
        )
        st.session_state['user_age_and_gender'] = user_age_and_gender
        logging.info("----------- Finished running main_app_miscellaneous.get_user_age_and_gender.-----------")

    has_fruit_and_veggie_intake = diabetes_assessor.get_user_fruit_and_veggie_intake(
        user_id=st.session_state['user_id'],
        layout_position=assess_diabetes_risk_tab
    )
    if has_fruit_and_veggie_intake != st.session_state.get('has_fruit_and_veggie_intake'):
        st.session_state['has_fruit_and_veggie_intake'] = has_fruit_and_veggie_intake

    logging.info("-----------Running make_diabetes_prediction()-----------")
    diabetes_risk_message = diabetes_assessor.make_diabetes_prediction(
        is_logged_in=st.session_state['is_logged_in'],
        user_age_and_gender=st.session_state.get('user_age_and_gender'),
        has_fruit_and_veggie_intake=st.session_state.get('has_fruit_and_veggie_intake'),
        layout_position=assess_diabetes_risk_tab,
    )
    logging.info("-----------Finished running make_diabetes_prediction-----------")

# Main flow
# wait for users' input
wait_while_condition_is_valid((st.session_state.get('dish_description') is None))

if st.session_state.get('ingredient_df') is None:
    logging.info("-----------Running get_user_input_dish_and_estimate_ingredients()-----------")
    ingredient_df = main_app_miscellaneous.get_user_input_dish_and_estimate_ingredients(
        dish_description=st.session_state['dish_description'],
        layout_position=track_new_meal_tab
    )
    st.session_state['ingredient_df'] = ingredient_df
    logging.info("-----------Finished get_user_input_dish_and_estimate_ingredients.-----------")

wait_while_condition_is_valid((st.session_state.get('ingredient_df') is None))

edited_ingredient_df = main_app_miscellaneous.display_and_let_user_edit_ingredient(
    ingredient_df=st.session_state.get('ingredient_df'),
    layout_position=track_new_meal_tab
)

if st.session_state.get('ingredient_df') is not None:
    track_new_meal_tab.write("Press continue to get your nutrition estimation...")
    if track_new_meal_tab.button(label="Continue", key="confirm_ingredient_weights"):
        st.session_state['confirm_ingredient_weights_button'] = True

wait_while_condition_is_valid((not st.session_state.get('confirm_ingredient_weights_button', False)))

# Wait and let user edit their ingredients until user click confirm_ingredient_weights_button
st.session_state['ingredient_df'] = edited_ingredient_df

# # 2-3. Nutrient actual intake
if st.session_state.get('total_nutrients_based_on_food_intake') is None:
    Nutrient = NutrientMaster(openai_client=OPENAI_CLIENT)
    total_nutrients_based_on_food_intake = Nutrient.total_nutrients_based_on_food_intake(
                                            ingredients_from_user=st.session_state['ingredient_df'],
                                            layout_position=track_new_meal_tab
                                        )
    st.session_state['total_nutrients_based_on_food_intake'] = total_nutrients_based_on_food_intake

wait_while_condition_is_valid((st.session_state.get('total_nutrients_based_on_food_intake') is None))

main_app_miscellaneous.display_user_intake_df(
    user_intake_df=st.session_state['total_nutrients_based_on_food_intake'],
    layout_position=track_new_meal_tab
)

# 3. Check user's log in status
# @Nyan
# TODO: create the a table storing user's personal data: age, gender etc.
# Update this data if there are any changes.

wait_while_condition_is_valid((st.session_state.get('total_nutrients_based_on_food_intake') is None))

### TODO: replace this with actual input
user_intake_df_temp = st.session_state['total_nutrients_based_on_food_intake']
user_intake_df_temp["user_id"] = st.session_state['user_id']
###

# 4 + 5. Get user's age + gender
has_user_intake_df_temp_empty = user_intake_df_temp.empty if isinstance(user_intake_df_temp, pd.DataFrame) else True
if st.session_state.get('user_personal_data') is None:
    logging.info("----------- Running get_user_personal_data()-----------")
    user_personal_data = main_app_miscellaneous.get_user_personal_data(
        is_logged_in=st.session_state['is_logged_in'],
        user_id=st.session_state['user_id'],
        has_user_intake_df_temp_empty=has_user_intake_df_temp_empty,   ## handle case total_nutrients_based_on_food_intake is not a DataFrame but a dict
        layout_position=track_new_meal_tab
    )
    st.session_state['user_personal_data'] = user_personal_data
    logging.info("-----------Finished get_user_personal_data-----------")


# 6. Join with recommended intake
# Only run when we have user_personal_data
# @Tu

logging.info("-----------Running combine_and_show_users_recommended_intake()-----------")
user_recommended_intake_result = main_app_miscellaneous.combine_and_show_users_recommended_intake(
    user_personal_data=st.session_state['user_personal_data'],
    user_intake_df_temp=user_intake_df_temp,
    user_intake_df_temp_name="user_intake_df_temp",
    layout_position=track_new_meal_tab
)
logging.info("-----------Finished combine_and_show_users_recommended_intake-----------")

# # 6. @Michael
# # Visualize data


meal_record_date = main_app_miscellaneous.get_meal_record_date(
    layout_position=track_new_meal_tab,
    has_user_intake_df_temp_empty=has_user_intake_df_temp_empty
)
user_intake_df_temp['meal_record_date'] = meal_record_date

logging.info("-----------Running get_user_confirmation_and_try_to_save_their_data()-----------")
if st.session_state.get('save_meal_result') is None:
    save_meal_result = main_app_miscellaneous.get_user_confirmation_and_try_to_save_their_data(
        dish_description=st.session_state['dish_description'],
        user_id=st.session_state['user_id'],
        is_logged_in=st.session_state['is_logged_in'],
        layout_position=track_new_meal_tab,
        has_user_intake_df_temp_empty=has_user_intake_df_temp_empty
    )
    st.session_state['save_meal_result'] = save_meal_result
logging.info("-----------Finished get_user_confirmation_and_try_to_save_their_data-----------")

# Aggregate user_recommended_intake_df by day
if st.session_state.get('user_recommended_intake_df') is None:
    date_to_filter = main_app_miscellaneous.compare_and_return_the_smaller_date(
        date_input_1=meal_record_date
    )
    user_recommended_intake_from_database_df = main_app_miscellaneous.get_user_historical_data(
        user_id=st.session_state["user_id"],
        selected_date_range=(date_to_filter, date_to_filter)
    )
    st.session_state['user_recommended_intake_df'] = user_recommended_intake_from_database_df

user_recommended_intake_df = st.session_state['user_recommended_intake_df']

##### TEMPORARILY COMMENT OUT until columns are fixed and streamlit form is added


# 5. Recommend dish.
df_nutrient_data = pd.DataFrame() if user_recommended_intake_df is None else user_recommended_intake_df.copy()
#### TODO: CHANGE THIS - These 2 columns are not applicable anymore
# df_nutrient_data['daily_requirement_microgram'] = df_nutrient_data["daily_recommended_intake"]
# df_nutrient_data["daily_actual_microgram"] = df_nutrient_data["actual_intake"]
####
# if not df_nutrient_data.empty:

#     dishrecommend = DishRecommender(openai_client=OPENAI_CLIENT)

#     logging.info("-----------Running calculate_intake_difference-----------")
#     nutrient_info = dishrecommend.calculate_intake_difference(df_nutrient_data)
#     logging.info("-----------Finished calculate_intake_difference-----------")

#     logging.info("-----------Running get_user_input-----------")
#     cuisine, allergies, ingredients = dishrecommend.get_user_input()
#     logging.info("-----------Finished get_user_input-----------")

#     logging.info("-----------Running get_dish_recommendation-----------")
#     if st.button("Recommend Dish"):
#         recommended_dish = dishrecommend.get_dish_recommendation(nutrient_info, cuisine, ingredients, allergies)
#         st.write(recommended_dish)
#     logging.info("-----------Finished get_dish_recommendation-----------")
recommended_recipe = """
    Quick boil – Remove impurities from beef with a 5 minute boil, it’s the path to a beautiful clear soup;

    Scum – be amazed at all the icky stuff that comes out;

    Wash the bones to get all the icky scum off;

    Simmer for 3 hours – bones, beef, water, onion, ginger and spices (cinnamon, cardamom, coriander, star anise);

    Remove brisket  – some is used for Pho topping, see below recipe for ways to use remainder;

    Simmer 40 minutes further with just bones;

    Strain; then

    Ladle into bowls over noodles and pile on Toppings!
"""



if st.session_state.get('recommended_recipe') is None and recommended_recipe != "":
    st.session_state['recommended_recipe'] = recommended_recipe



if not df_nutrient_data.empty and st.session_state.get('recommended_recipe') is not None:
    track_new_meal_tab.info("""
        If this is your first time with us,
        please search for @meal_minder_bot on Telegram and say hi so that we can reach out to you 😉
    """)
    user_telegram_user_name = track_new_meal_tab.text_input("Let us know your Telegram user name to receive this recipe")

    # reset session_state if user inputs another user namse
    if st.session_state.get('user_telegram_user_name') is not None and user_telegram_user_name != "" and user_telegram_user_name != st.session_state.get('user_telegram_user_name'):
        st.session_state['user_telegram_user_name'] = None

    if st.session_state.get('user_telegram_user_name') is None and user_telegram_user_name != "":
        st.session_state['user_telegram_user_name'] = user_telegram_user_name

    if st.session_state.get('user_telegram_user_name') is not None:
        telegram_bot.send_message_to_user_name(
            user_name=st.session_state.get('user_telegram_user_name'),
            message=st.session_state.get('recommended_recipe'),
            layout_position=track_new_meal_tab
        )