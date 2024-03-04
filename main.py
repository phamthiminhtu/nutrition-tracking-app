import os
import time
import streamlit as st
from openai_api import *

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
        prompt=ingredient_estimation_prompt
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
# Take the input from step 2 + email + date, save them into duckdb.
# Side note: Either hash(email, date+hour+minute) to ensure that the user does not 
# submit the same dish twicw.
# or ask confirmation from user.
    

# 5. Recommend dish.
# @Anika
# A python class in a separate file (Anika.py - Please rename it), containing different methods:
    # E.g. DishRecommender = DishRecommender()
    # DishRecommender.get_user_preference()
    # DishRecommender.recommend_recipe()
# Ask user's preference (diet/ what do you have left in your fridge?)