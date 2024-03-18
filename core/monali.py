import pandas as pd
import openai 
import os
import streamlit as st
from core.openai_api import *


def read_data(file_path):
    """
        Reads data from a file. 
        Returns a DataFrame containing the CSV data.
    """
    df = pd.read_csv(file_path)
    
    return df

class DishRecommender:
    def __init__(self, openai_client) -> None:
        #self.df_nutrient_data = df_nutrient_data
        self.openai_api = OpenAIAssistant(openai_client=openai_client)

    def calculate_intake_difference(self, df_nutrient_data):
        """
            Calculates the difference between 'daily_requirement_microgram' and 'daily_actual_microgram'.
            Updates with a new column 'intake_difference'.
        """
        df_nutrient_data['intake_difference'] = df_nutrient_data['daily_requirement_microgram'] - df_nutrient_data['daily_actual_microgram']
        
        nutrient_info = ", ".join([f"{nutrient}-{intake_diff}" for nutrient, intake_diff in zip(df_nutrient_data['nutrient'], df_nutrient_data['intake_difference'])])

        return nutrient_info

    def get_user_input(self):
        """
            Takes input from the user for Cuisine, Ingredients, and if any Allergies.
            Returns the user inputs. 
        """
        cuisine = st.text_input("Enter your preferred cuisine:")
        allergies = st.text_input("Enter if you have any allergies: ")
        ingredients = st.text_input("Enter the ingredients/leftover in fridge(separated by commas): ")

        if not allergies:
            allergies = None
        if not ingredients:
            ingredients = None

        return cuisine, allergies, ingredients

    def get_dish_recommendation(self, nutrient_info, cuisine, ingredients, allergies):
        """
            Provides dish recommendations based on the given user preferences using the OpenAI API.
        """
        prompt = ""

        if (allergies is not None and ingredients is not None):
            prompt = f"Based on your preferences - nutrient: {nutrient_info}, cuisine: {cuisine}, ingredients: {ingredients}, and allergies: {allergies}, recommend a dish."
        
        if (allergies is not None and ingredients is None):
            prompt = f"Based on your preferences - nutrient: {nutrient_info}, cuisine: {cuisine}, and allergies: {allergies}, recommend a dish."
        
        if (allergies is None and ingredients is not None):
            prompt = f"Based on your preferences - nutrient: {nutrient_info}, cuisine: {cuisine}, and ingredients: {ingredients}, recommend a dish."
        
        if (allergies is None and ingredients is None):
            prompt = f"Based on your preferences - nutrient: {nutrient_info}, and cuisine: {cuisine}, recommend a dish."
    
        print(prompt)
        response = self.openai_api.run_prompt(prompt=prompt)

        if response.get("status") == 200:
            dish_recommendation = response.get("value")
            recommended_dish = f"The recommended dish based on your preferences is: {dish_recommendation}"
            return recommended_dish
        else:
            raise ValueError("Sorry!! couldn't to retrieve dish recommendation for your preferences.")