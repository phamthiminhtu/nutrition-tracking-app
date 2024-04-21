import os
import re
import openai 
import pandas as pd
import numpy as np
import logging
import streamlit as st
from core.openai_api import *
from core.visualization import *
from core.utils import handle_exception

# Setting up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Class for dish recommendation feature
class DishRecommender:
    def __init__(self, openai_client) -> None:
        #self.df_nutrient_data = df_nutrient_data
        self.openai_api = OpenAIAssistant(openai_client=openai_client)

    
    @handle_exception(has_random_message_printed_out=True)
    def retrieve_nutrient_intake_info(self, user_recommended_intake_result):
        logging.info("Function call to retrieve nutrient intake information.")
        """
            Collecting the nutrient, daily_recommended_intake, and its measurement information. 
        """
        # Creating a dataframe to extract the required details.
        df_user_recommended_intake_result = pd.DataFrame(user_recommended_intake_result['value'])

        # Extracting nutrient, daily_recommended_intake, and its measurement
        nutrient_info = ", ".join([f"{row['nutrient']}-{row['intake_diff']} {row['measurement']}" for index, row in df_user_recommended_intake_result.iterrows()])
        logging.info("End of the function call to retrieve nutrient intake information.")
        return nutrient_info

    @handle_exception(has_random_message_printed_out=True)
    def get_user_input(self, layout_position):
        logging.info("Function call to read user preferences for dish recommendation.")
        """
            Takes input from the user for Cuisine, Ingredients, and if any Allergies.
            Returns the user inputs. 
        """

        # Reading the user preferences for cuisine, allergies, if any leftover ingredients
        cuisine = layout_position.text_input("🍴🥗 Enter your preferred cuisine:")
        allergies = layout_position.text_input("🤧😷 Enter if you have any allergies (optional):")
        ingredients = layout_position.text_input("🥖🍅 Enter the ingredients/leftover in fridge separated by commas (optional):")

        if not allergies:
            allergies = None
        if not ingredients:
            ingredients = None

        # Returing user preferences for cuisine, allergies, if any leftover ingredients
        return cuisine, allergies, ingredients

        logging.info("End of the function call to read user preferences for dish recommendation.")

    
    
    @handle_exception(has_random_message_printed_out=True)
    def get_dish_recommendation(self, nutrient_info, cuisine, ingredients, allergies):
        """
            Provides dish recommendations based on the given user preferences using the OpenAI API.
        """
        logging.info("Function call for dish recommendation.")
        prompt = ""
        
        if (allergies is not None and ingredients is not None):
            prompt = f"""Recommend a dish and recipe in cuisine {cuisine} which contains this exact nutrient amount:
		        {nutrient_info}, including ingredients: {ingredients} and excluding: {allergies}
		        The output should always contain exactly 3 titles "Dish Name:", "Ingredients:" and "Recipe:"
		        with Ingredients always in the format ```'ingredient': weight'``` 
		        where ingredient is string and weight is always integer in gram unit."""
            
        if (allergies is not None and ingredients is None):
            prompt = f"""Recommend a dish and recipe in cuisine {cuisine} which contains this exact nutrient amount:
		        {nutrient_info} and excluding: {allergies}
		        The output should always contain exactly 3 titles "Dish Name:", "Ingredients:" and "Recipe:"
		        with Ingredients always in the format ```'ingredient': weight'``` 
		        where ingredient is string and weight is always integer in gram unit."""
            
        if (allergies is None and ingredients is not None):
            prompt = f"""Recommend a dish and recipe in cuisine {cuisine} which contains this exact nutrient amount:
		        {nutrient_info} and including ingredients: {ingredients}
		        The output should always contain exactly 3 titles "Dish Name:", "Ingredients:" and "Recipe:"
		        with Ingredients always in the format ```'ingredient': weight'``` 
		        where ingredient is string and weight is always integer in gram unit."""
            
        if (allergies is None and ingredients is None):
            prompt = f"""Recommend a dish and recipe in cuisine {cuisine} which contains this exact nutrient amount:
		        {nutrient_info}
		        The output should always contain exactly 3 titles "Dish Name:", "Ingredients:" and "Recipe:"
		        with Ingredients always in the format ```'ingredient': weight'``` 
		        where ingredient is string and weight is always integer in gram unit."""

    
        # Retrieving the dish to be recommend to user using OpenAI API 
        response = self.openai_api.run_prompt(prompt=prompt)

        if response.get("status") == 200:
            dish_recommendation = response.get("value")
            recommended_dish = f"{dish_recommendation}"
            logging.info("End of the function call for dish recommendation.")
            return recommended_dish
        else:
            raise ValueError("Sorry!! couldn't to retrieve dish recommendation for your preferences.")


    @handle_exception(has_random_message_printed_out=True)
    def get_recommended_dish_ingredients(self, recommended_dish):
        """
            Retrieve ingredients of the recommended dish.
        """
        logging.info("Function call to retrieve recommended dish ingredients.")
        recommended_dish_ingredients = {}
        df_recommended_dish_ingredients = pd.DataFrame()
        for line in recommended_dish.split("Ingredients")[1].split("Recipe")[0].split("\n- "):
            try:
                if ":" in line:
                    recommended_ingredients_name, recommended_ingredients_weight = line.split(": ")
                    ingredients_name, weight = recommended_ingredients_name.strip().replace("- ", ""), recommended_ingredients_weight.strip().replace("g", "")
                    recommended_dish_ingredients[ingredients_name] = float(weight)
            except Exception as e:
                pass
        if recommended_dish_ingredients:
            df_recommended_dish_ingredients = pd.DataFrame(recommended_dish_ingredients.items(), columns=['Ingredient', 'Estimated weight (g)'])
        logging.info("End of the function call to retrieve recommended dish ingredients.")
        return df_recommended_dish_ingredients

    @handle_exception(has_random_message_printed_out=True)
    def get_total_nutrients_after_dish_recommend(self, earlier_nutrients_intake, recommended_dish_nutrients, layout_position):
        """
            Calculates and displays the total nutrients after the dish recommendation.
        """
        logging.info("Function call to calculate and display the total nutrients after the dish recommendation.")
        df_earlier_nutrients_intake = pd.DataFrame(earlier_nutrients_intake['value'])
        df_recommended_dish_nutrients = pd.DataFrame(recommended_dish_nutrients)
        
        # Renaming the actual_intake column in the recommended_dish_nutrients recommended_intake
        df_recommended_dish_nutrients.rename(columns={"actual_intake": "recommended_intake"}, inplace=True)  

        # Merging the two dataframes on the common column "Nutrient"
        df_merged = pd.merge(df_earlier_nutrients_intake, df_recommended_dish_nutrients, left_on="nutrient", right_on="Nutrient")

        # Adding the actual intake from dish concumed and dish recommended
        df_merged["Total_Nutrient_Value"] = df_merged["actual_intake"] + df_merged["recommended_intake"]
        
        # Selecting only required columns
        df_computed_recommended_nutrients = df_merged[["Nutrient", "Total_Nutrient_Value", "daily_recommended_intake"]]
        
        # Calculating the total_recommended_nutrients_percent
        df_computed_recommended_nutrients["Actual intake / Recommended intake (%)"] = np.ceil(df_computed_recommended_nutrients["Total_Nutrient_Value"] * 100 / df_computed_recommended_nutrients["daily_recommended_intake"])
        
        # Displaying the graph nutirents after the dish recommendation
        # users_recommended_intake_chart(df_computed_recommended_nutrients, layout_position=layout_position)
        logging.info("End of the function call to calculate and display the total nutrients after the dish recommendation.")
        
        return df_computed_recommended_nutrients

        