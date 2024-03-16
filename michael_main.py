import datetime
import streamlit as st
from michael_tests import NutrientMaster
import duckdb

# User input age
user_age = int(st.slider("How old are you?", 1, 120, 25))
st.session_state["user_age"] = user_age

# User input gender
user_gender = st.selectbox(
                "What's your gender?", 
                ("Male", "Female"),
                index=None,
                placeholder="Select gender")
st.session_state["user_gender"] = user_gender

# User input date
date_input = st.date_input(
                "When was your meal consumed or plan to be consumed?", 
                datetime.date.today(), 
                format="DD/MM/YYYY")
st.session_state["date_input"] = date_input



# Setting up duckdb
conn = duckdb.connect()

ingredients_from_user = conn.execute(
    """
    SELECT *
    FROM "sample_beef_burger_ingredients.csv"
    """
).df()

if st.button("Go"):
    Nutrient = NutrientMaster()
    df = Nutrient.compare_daily_recommendation_against_user_intake(ingredients_from_user, user_age, user_gender, date_input)
    
    st.table(df.style.format({"Total/day": "{:.1f}", date_input: "{:.1f}"}))