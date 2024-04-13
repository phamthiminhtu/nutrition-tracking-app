import os
import re
import openai 
import pandas as pd
import logging
import streamlit as st
from core.openai_api import *
from core.visualization import *

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
        nutrient_info = ", ".join([f"{row['nutrient']}-{row['intake_diff']} {row['measurement']}" for index, row in df_user_recommended_intake_result.iterrows()])
    
    logging.info("End of the function call to retrieve nutrient intake information.")


    logging.info("Function call to read user preferences for dish recommendation.")
    def get_user_input(self, layout_position):
        """
            Takes input from the user for Cuisine, Ingredients, and if any Allergies.
            Returns the user inputs. 
        """

        # Reading the user preferences for cuisine, allergies, if any leftover ingredients
        cuisine = layout_position.text_input("Enter your preferred cuisine:")
        allergies = layout_position.text_input("Enter if you have any allergies: ")
        ingredients = layout_position.text_input("Enter the ingredients/leftover in fridge(separated by commas): ")

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
        result_format = f"""recommend a dish along with its dish name, ingredients with its weight in gram and receipe.
                        """
        if (allergies is not None and ingredients is not None):
            prompt = f"Based on your preferences - nutrient: {nutrient_info}, cuisine: {cuisine}, ingredients: {ingredients}, and allergies: {allergies}, recommend a dish in this exact format dish name, ingredients with its weight in gram and receipe for one serve."
        
        if (allergies is not None and ingredients is None):
            prompt = f"Based on your preferences - nutrient: {nutrient_info}, cuisine: {cuisine}, and allergies: {allergies}, recommend a dish in this exact format dish name, ingredients with its weight in gram and receipe for one serve."
        
        if (allergies is None and ingredients is not None):
            prompt = f"Based on your preferences - nutrient: {nutrient_info}, cuisine: {cuisine}, and ingredients: {ingredients}, recommend a dish in this exact format dish name, ingredients with its weight in gram and receipe for one serve."
        
        if (allergies is None and ingredients is None):
            prompt = f"Based on your preferences - nutrient: {nutrient_info}, and cuisine: {cuisine}, recommend a dish in this exact format dish name, ingredients with its weight in gram and receipe for one serve."
    
        # Retrieving the dish to be recommend to user using OpenAI API 
        response = self.openai_api.run_prompt(prompt=prompt)

        if response.get("status") == 200:
            dish_recommendation = response.get("value")
            recommended_dish = f"{dish_recommendation}"
            return recommended_dish
        else:
            raise ValueError("Sorry!! couldn't to retrieve dish recommendation for your preferences.")
        
    logging.info("End of the function call for dish recommendation.")

    logging.info("Function call to retrieve recommended dish name.")
    def get_recommended_dish_name(self, recommended_dish):
        #print("inside the function call to retrieve recommended dish name.")
        #print(recommended_dish)
        dish_name = None
            
        if dish_name is None:
            result_lines = recommended_dish.split('\n')
            # Extracting the dish name
            for line in result_lines:
                if line.startswith("Dish Name:") or line.startswith("Dish:"):
                    dish_name = line.split(":")[1].strip()
                    break

        if dish_name is None:
            pattern = r"called\s(.*?)[.]"
            # Checking the first match of the pattern in the prompt_result variable
            match = re.search(pattern, recommended_dish)

            # Extracting the dish name if a match is found
            if match:
                dish_name = match.group(1).strip()
        
        return dish_name
    logging.info("End of the function call to retrieve recommended dish name.")

    logging.info("Function call to calculate and display the total nutrients after the dish recommendation.")
    def get_recommended_dish_nutrients(self, earlier_nutrients_intake, recommended_dish_nutrients, layout_position):
        print("inside the get_recommended_dish_nutrients function.")
        df_earlier_nutrients_intake = pd.DataFrame(earlier_nutrients_intake['value'])
        df_recommended_dish_nutrients = pd.DataFrame(recommended_dish_nutrients)
        
        # Renaming the actual_intake column in the recommended_dish_nutrients recommended_intake
        df_recommended_dish_nutrients.rename(columns={"actual_intake": "recommended_intake"}, inplace=True)  

        print("Earlier consumed dish.")
        print(df_earlier_nutrients_intake)
        print("Recommended dish.")  
        print(df_recommended_dish_nutrients)

        # Merging the two dataframes on the common column "Nutrient"
        #df_merged = pd.merge(df_earlier_nutrients_intake, df_recommended_dish_nutrients, left_on="nutrient", right_on="Nutrient")

        # Adding a new column "Nutrient_Value" which is the sum of "daily_recommended_intake" and "actual_intake"
        #df_merged["Nutrient_Value"] = df_merged["actual_intake"] + df_merged["recommended_intake"]
        

        # Selecting only the "Nutrient" and "Nutrient_Value" columns to create the new dataframe
        #df_computed_recommended_nutrients = df_merged[["Nutrient", "Nutrient_Value"]]

        #print("New df", df_computed_recommended_nutrients)
        #recommended_nutrients_chart(df_computed_recommended_nutrients, layout_position=layout_position)
    logging.info("End of the function call to calculate and display the total nutrients after the dish recommendation.")