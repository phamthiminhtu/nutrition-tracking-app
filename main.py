import os
import time
import streamlit as st
from core.openai_api import *
from core.duckdb_connector import *


OPENAI_API_KEY = "OPENAI_API_KEY"
OPENAI_CLIENT = OpenAI(
  api_key=os.environ.get(OPENAI_API_KEY),
)

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

# 2. Nutrient actual intake vs recommended intake
# @Michael @Johnny
    # Ask users' information:
        # age, gender, date
    # I think your methods should be in the same class in the same python file (Michael_Johnny.py file - please rename it).
    # E.g. NutrientMaster = NutrientMaster()
    # NutrientMaster.calculate_recommended_intake_from_database()
    # NutrientMaster.calculate_recommended_intake_using_openapi()


# 3. Authentication 
# @Nyan



# 4. Store data into duckdb
# @Tu
### TODO: replace this with actual input
is_logged_in = True
user_id = "tu@gmail.com"
user_intake_df = pd.DataFrame(
    [
        {
            "user_id": "tu@gmail.com",
            "gender": "female",
            "age": 20,
            "dish_description": "beef burger",
            "nutrient": "protein",
            "actual_intake": 2,
        },
        {
            "user_id": "tu@gmail.com",
            "gender": "female",
            "age": 20,
            "dish_description": "beef burger",
            "nutrient": "vitamin a",
            "actual_intake": 3,
        }
    ]
)
###
has_historical_data_saved = st.selectbox(
    "Do you want to save this meal info?",
    ("Yes", 'No'),
    index=None,
    placeholder="Select your answer..."
)
if has_historical_data_saved == "Yes":
    if is_logged_in:
        duckdb = DuckdbConnector()
        storing_historical_data_result = duckdb.save_user_nutrient_intake(dish_description, user_id)
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

# 5. Recommend dish.
# @Anika
# A python class in a separate file (Anika.py - Please rename it), containing different methods:
    # E.g. DishRecommender = DishRecommender()
    # DishRecommender.get_user_preference()
    # DishRecommender.recommend_recipe()
# Ask user's preference (diet/ what do you have left in your fridge?)