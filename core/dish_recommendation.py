import os
import re
import openai 
import pandas as pd
import logging
import streamlit as st
from core.openai_api import *

# Setting up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(name)s:%(funcName)s:%(message)s")

# Setting up file handler to save logs in a log file
file_handler = logging.FileHandler("data/logs.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class DishRecommender:
    def __init__(self, openai_client) -> None:
        #self.df_nutrient_data = df_nutrient_data
        self.openai_api = OpenAIAssistant(openai_client=openai_client)

    logging.info("Function call to retrieve nutrient intake information.")
    def retrieve_nutrient_intake_info(self, user_recommended_intake_result):
        """
            Collecting the nutrient, daily_recommended_intake, and its measurement information. 
        """
        # Creating a dataframe to extract the required details.
        df_user_recommended_intake_result = pd.DataFrame(user_recommended_intake_result['value'])

        # Extracting nutrient, daily_recommended_intake, and its measurement
        nutrient_info = ", ".join([f"{row['nutrient']}-{row['daily_recommended_intake']} {row['measurement']}" for index, row in df_user_recommended_intake_result.iterrows()])
    
    logging.info("End of the function call to retrieve nutrient intake information.")


    logging.info("Function call to read user preferences for dish recommendation.")
    def get_user_input(self):
        """
            Takes input from the user for Cuisine, Ingredients, and if any Allergies.
            Returns the user inputs. 
        """

        # Reading the user preferences for cuisine, allergies, if any leftover ingredients
        cuisine = st.text_input("Enter your preferred cuisine:")
        allergies = st.text_input("Enter if you have any allergies: ")
        ingredients = st.text_input("Enter the ingredients/leftover in fridge(separated by commas): ")

        if not allergies:
            allergies = None
        if not ingredients:
            ingredients = None

        # Returing user preferences for cuisine, allergies, if any leftover ingredients
        return cuisine, allergies, ingredients

    logging.info("End of the function call to read user preferences for dish recommendation.")

    
    logging.info("Function call for dish recommendation.")
    def get_dish_recommendation(self, nutrient_info, cuisine, ingredients, allergies):
        """
            Provides dish recommendations based on the given user preferences using the OpenAI API.
        """
        prompt = ""

        if (allergies is not None and ingredients is not None):
            prompt = f"Based on your preferences - nutrient: {nutrient_info}, cuisine: {cuisine}, ingredients: {ingredients}, and allergies: {allergies}, recommend a dish along with its dish name, ingredients and receipe.   "
        
        if (allergies is not None and ingredients is None):
            prompt = f"Based on your preferences - nutrient: {nutrient_info}, cuisine: {cuisine}, and allergies: {allergies}, recommend a dish along with its dish name, ingredients and receipe."
        
        if (allergies is None and ingredients is not None):
            prompt = f"Based on your preferences - nutrient: {nutrient_info}, cuisine: {cuisine}, and ingredients: {ingredients}, recommend a dish along with its dish name, ingredients and receipe"
        
        if (allergies is None and ingredients is None):
            prompt = f"Based on your preferences - nutrient: {nutrient_info}, and cuisine: {cuisine}, recommend a dish along with its and in a format dish name, ingredients and receipe."
    
        # Retrieving the dish to be recommend to user using OpenAI API 
        response = self.openai_api.run_prompt(prompt=prompt)

        if response.get("status") == 200:
            dish_recommendation = response.get("value")
            recommended_dish = f"{dish_recommendation}"
            return recommended_dish
        else:
            raise ValueError("Sorry!! couldn't to retrieve dish recommendation for your preferences.")
        
    logging.info("End of the function call for dish recommendation.")