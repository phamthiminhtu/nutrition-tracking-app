import logging
import warnings
import pandas as pd
from fuzzywuzzy import fuzz, process
from core.utils import handle_exception
from core.openai_api import OpenAIAssistant
import streamlit as st
import json

# Setting up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.disabled = True
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(name)s:%(funcName)s:%(message)s")
warnings.filterwarnings("ignore")

# Setting up file handler to save logs in a log file
file_handler = logging.FileHandler("data/logs.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class NutrientMaster:
    def __init__(self, openai_client):
        self.ingredients_in_database = pd.read_csv("data/csv/nutrients_per_ingredient.csv")
        self.openai_api = OpenAIAssistant(openai_client)


    def _calculate_single_ingredient_match_score(self, ingredient_from_user) -> tuple:

        # Calculate ingredient match score using fuzzy matching
        result = process.extractOne(ingredient_from_user, self.ingredients_in_database['database_ingredient'], scorer=fuzz.token_sort_ratio)
        return result[0], result[1]


    def _calculate_match_score_for_all_ingredients(self, ingredients_from_user) -> pd.DataFrame:

        # Calculate match score for each ingredient
        for index, ingredient in ingredients_from_user.iterrows():
            ingredients_from_user.at[index, 'database_ingredient'], ingredients_from_user.at[index, 'match_score'] = self._calculate_single_ingredient_match_score(ingredient["Ingredient"])

        logger.info("Finished calculating match score for all ingredients")
        return ingredients_from_user

    def _group_ingredients_based_on_match_score(self, min_match_score, ingredients_from_user) -> pd.DataFrame:

        # Calculate ingredient match score
        match_result = self._calculate_match_score_for_all_ingredients(ingredients_from_user)

        # Extract ingredients with high match score
        ingredient_with_high_match_score = match_result[match_result["match_score"] > min_match_score]

        # Extract ingredients with low match score
        ingredient_with_low_match_score = match_result[match_result["match_score"] <= min_match_score]

        logger.info("Finished sorting ingredients based on match score")
        return ingredient_with_high_match_score, ingredient_with_low_match_score


    def _calculate_total_nutrients_per_ingredient_based_on_ingredient_weight(self, ingredients_and_nutrients_df) -> pd.DataFrame:

        # Calculate total nutrients per ingredient based on ingredient weight
        ingredients_and_nutrients_df.iloc[:, 2:] = ingredients_and_nutrients_df.iloc[:, 2:].multiply(ingredients_and_nutrients_df['Estimated weight (g)'], axis=0)

        logger.info("Finished calculating total nutrients per ingredient based on weight")
        return ingredients_and_nutrients_df


    def extract_ingredients_with_high_match_score_and_their_nutrients(self, ingredients_from_user, min_match_score) -> pd.DataFrame:

        # Extract ingredients with high match score
        high_score_ingredients, _ = self._group_ingredients_based_on_match_score(min_match_score, ingredients_from_user=ingredients_from_user)

        # Merge ingredients with nutrient values from database
        ingredients_and_nutrients_df = pd.merge(high_score_ingredients, self.ingredients_in_database, on="database_ingredient", how="left")

        # Drop irrelevant columns
        ingredients_and_nutrients_df.drop(columns=["database_ingredient", "match_score"], inplace=True)

        # Calculate total nutrients per ingredient based on ingredient weight
        ingredients_and_total_nutrients_df = self._calculate_total_nutrients_per_ingredient_based_on_ingredient_weight(ingredients_and_nutrients_df)

        # Drop irrelevant columns
        ingredients_and_total_nutrients_df.drop(columns=["Ingredient", "Estimated weight (g)"], inplace=True)

        logger.info("Finished extracting ingredients with high match score and their total nutrients")
        return ingredients_and_total_nutrients_df


    def sum_total_nutrients_in_high_match_score_ingredients(self, ingredients_from_user, min_match_score) -> pd.DataFrame:

        # Extract ingredients and total nutrients for each ingredient
        total_nutrients_in_each_ingredient_df = self.extract_ingredients_with_high_match_score_and_their_nutrients(ingredients_from_user, min_match_score)

        # Sum all nutrients for the meal
        total_nutrients_in_the_meal= total_nutrients_in_each_ingredient_df.sum()
        total_nutrients_in_the_meal_df = pd.DataFrame(total_nutrients_in_the_meal).T
        total_nutrients_in_the_meal_df.index = [len(total_nutrients_in_each_ingredient_df)]

        # Extract sum of nutrients for the meal
        merged_df = pd.concat([total_nutrients_in_each_ingredient_df, total_nutrients_in_the_meal_df])
        merged_df.insert(loc=0, column="Nutrient", value="total_database")
        merged_df = merged_df.iloc[-1:]

        logger.info("Finished summing total nutrients in high match score ingredients")
        return merged_df

    def extract_ingredients_with_low_match_score_and_prepare_text_prompt(self, ingredients_from_user) -> str:

        # Extract low match score ingredients
        _, low_score_ingredients = self._group_ingredients_based_on_match_score(min_match_score=55, ingredients_from_user=ingredients_from_user)

        # Drop irrelevant columns
        low_score_ingredients.drop(["database_ingredient", "match_score"], axis=1, inplace=True)

        # Convert low score ingredients into json format
        low_score_ingredients = low_score_ingredients.to_json(orient='records')

        # Create an openai prompt containing low score ingredients
        prompt = f"Provide a table output for approximate average values for Energy (kJ), Protein (g), Total water (L), Thiamin (B1) (mg), Riboflavin (B2) (mg), Niacin (mg), Pyridoxine (B6) (mg), Cobalamin (B12) (μg), Vitamin A (μg), Vitamin C (mg), Vitamin D (μg), Vitamin E (mg), Calcium (mg), Phosphorus (mg), Zinc (mg), Iron (mg), Magnesium (mg), Sodium (mg) and Potassium (mg), for the following ingredients and considering their weights, input from the following: {low_score_ingredients} the response should only provide the amount and as a json output."

        return prompt

    def calculate_total_nutrients_for_low_match_ingredients_using_openai(self, ingredients_from_user) -> pd.DataFrame:

        # Extract prompt to be fed into openai
        prompt = self.extract_ingredients_with_low_match_score_and_prepare_text_prompt(ingredients_from_user)

        # Define openai response format
        response_format = "json_object"

        # Define openai system prompt
        system_prompt ="You are a helpful nutritionist."

        # Run the prompt and save the result
        result = self.openai_api.run_prompt(prompt=prompt, response_format=response_format, system_prompt =system_prompt)

        # Convert result into dictionary
        result_dict = json.loads(result.get("value"))

        # Convert dictionary into dataframe and reset index
        df = pd.DataFrame([result_dict]).T
        df = df.reset_index()

        # Assign new column names
        df.columns = ["Nutrient_openai", "total_openai"]

        logger.info("Finished summing total nutrients in low match score ingredients")
        return df

    def _transpose_and_reformat_dataframe(self, df=None) -> pd.DataFrame:

        # Transpose and reformat dataframe
        if df is not None:
            transposed_df = df.iloc[-1:].T.reset_index()
            transposed_df.columns = transposed_df.iloc[0]
            transposed_df = transposed_df[1:]
            transposed_df = transposed_df.reset_index(drop=True)

        return transposed_df

    @handle_exception(funny_message="Your meal is exceptionally distinctive, and we may need to reconsider how to calculate its nutrient contents. Please visit us again later.")
    def total_nutrients_based_on_food_intake(self, ingredients_from_user, layout_position=st) -> pd.DataFrame:

        layout_position.write("Just one moment, we are doing the science 😎 ...")

        # Extract total nutrients in high match score ingredients and tranpose the result
        df_database = self.sum_total_nutrients_in_high_match_score_ingredients(ingredients_from_user[["Ingredient", "Estimated weight (g)"]], min_match_score=55)
        transposed_df_database = self._transpose_and_reformat_dataframe(df_database)

        # Extract total nutrients in low match score ingredients
        df_openai = self.calculate_total_nutrients_for_low_match_ingredients_using_openai(ingredients_from_user[["Ingredient", "Estimated weight (g)"]])
        
        try:
            # Calculate total nutrients from high and low match score ingredients
            final_df = pd.concat([transposed_df_database, df_openai], axis=1)
            final_df["actual_intake"] = final_df["total_database"] + final_df["total_openai"]

            # Drop unused columns
            final_df.drop(["total_database", "Nutrient_openai", "total_openai"], axis=1, inplace=True)

            # Convert nutrient values into float
            final_df["actual_intake"] = final_df["actual_intake"].astype(float).round(1)

            logger.info("Successfully ran low match ingredients through OpenAI")
        
        except:
            logger.error("Something went wrong with OpenAI, recalculating all ingredients' nutrients using internal database")

            # Something went wrong with OpenAI prompt, recalculate using internal database only
            df_database = self.sum_total_nutrients_in_high_match_score_ingredients(ingredients_from_user[["Ingredient", "Estimated weight (g)"]], min_match_score=40)
            final_df = self._transpose_and_reformat_dataframe(df_database)
            final_df.rename(columns={"total_database": "actual_intake"}, inplace=True)

        logger.info("Finished calculating total nutrients based on food intake")

        # Add dish_description column
        final_df["dish_description"] = ingredients_from_user["dish_description"]
        final_df["dish_description"] = final_df["dish_description"].fillna(ingredients_from_user["dish_description"].iloc[0])

        return final_df

    @handle_exception(funny_message="Your meal is exceptionally distinctive, and we may need to reconsider how to calculate its nutrient contents. Please visit us again later.")
    def get_recommended_dish_nutrients(self, recommended_dish_ingredients, layout_position=st) -> pd.DataFrame:

        #layout_position.write("Just one moment, we are doing the science 😎 ...")

        # Extract total nutrients in high match score ingredients and tranpose the result
        df_database = self.sum_total_nutrients_in_high_match_score_ingredients(recommended_dish_ingredients[["Ingredient", "Estimated weight (g)"]], min_match_score=55)
        transposed_df_database = self._transpose_and_reformat_dataframe(df_database)

        # Extract total nutrients in low match score ingredients
        df_openai = self.calculate_total_nutrients_for_low_match_ingredients_using_openai(recommended_dish_ingredients[["Ingredient", "Estimated weight (g)"]])
        
        try:
            # Calculate total nutrients from high and low match score ingredients
            final_df = pd.concat([transposed_df_database, df_openai], axis=1)
            final_df["actual_intake"] = final_df["total_database"] + final_df["total_openai"]

            # Drop unused columns
            final_df.drop(["total_database", "Nutrient_openai", "total_openai"], axis=1, inplace=True)

            # Convert nutrient values into float
            final_df["actual_intake"] = final_df["actual_intake"].astype(float).round(1)

            logger.info("Successfully ran low match ingredients through OpenAI")
        
        except:
            logger.error("Something went wrong with OpenAI, recalculating all ingredients' nutrients using internal database")

            # Something went wrong with OpenAI prompt, recalculate using internal database only
            df_database = self.sum_total_nutrients_in_high_match_score_ingredients(recommended_dish_ingredients[["Ingredient", "Estimated weight (g)"]], min_match_score=40)
            final_df = self._transpose_and_reformat_dataframe(df_database)
            final_df.rename(columns={"total_database": "actual_intake"}, inplace=True)

        logger.info("Finished calculating recommended dish nutrients based on the ingredients and its weight")

        return final_df