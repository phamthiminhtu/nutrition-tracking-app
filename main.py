import os
import time
import streamlit as st
from openai_api import *

OPENAI_API_KEY = "OPENAI_API_KEY"
OPENAI_CLIENT = OpenAI(
  api_key=os.environ.get(OPENAI_API_KEY),
)

dish_description = st.text_input(
    "What have you eaten today? 😋"
)
st.session_state["dish_description"] = dish_description
# submit_button = st.button("Estimate your nutrition intake", key="nutrition_intake")

openai_api = IngredientExtracter(openai_client=OPENAI_CLIENT)

if dish_description:
    openai_api.estimate_and_extract_dish_info(dish_description=dish_description)

# 2. Join with the food data in duckdb. Expected output: a dataframe containing nutrients, recommended_intake and actual_intake.
# Show this to user on the app
# Ask them whether they want to save the estimation. If:
    # No. Say bye. 
    # Yes, go to 3.
    

# 3. Take the input from step 2 + email + date, save them into duckdb.
# Note: Either hash(email, date+hour+minute) or ask confirmation from user.
    

# 4. Develop the log in functionality.