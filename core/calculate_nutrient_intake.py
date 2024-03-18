import duckdb
import logging
import pandas as pd
from fuzzywuzzy import fuzz, process
from core.utils import handle_exception
import streamlit as st

# Setting up duckdb
conn = duckdb.connect()

# Setting up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(name)s:%(funcName)s:%(message)s")

# Setting up file handler to save logs in a log file
file_handler = logging.FileHandler("data/logs.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class NutrientMaster:
    def __init__(self):
        self.ingredients_in_database = conn.execute(
                                                    """
                                                    SELECT *
                                                    FROM "data/csv/nutrients_per_ingredient.csv"
                                                    """
                                                    ).df()


    def _calculate_single_ingredient_match_score(self, ingredient_from_user) -> tuple:

        try:
            # Calculate ingredient match score using fuzzy matching
            result = process.extractOne(ingredient_from_user, self.ingredients_in_database['database_ingredient'], scorer=fuzz.token_sort_ratio)
        
        except Exception as e:
            logger.exception(f"Exception name: {type(e).__name__}")

        else:
            logger.info(f"Finished calculating match score for: {ingredient_from_user}")
            return result[0], result[1]
    
   
    def calculate_match_score_for_all_ingredients(self, ingredients_from_user) -> pd.DataFrame:

        try:
            # Calculate match score for each ingredient
            for index, ingredient in ingredients_from_user.iterrows():
                ingredients_from_user.at[index, 'database_ingredient'], ingredients_from_user.at[index, 'match_score'] = self._calculate_single_ingredient_match_score(ingredient["Ingredient"])
        
        except Exception as e:
            logger.exception(f"Exception name: {type(e).__name__}")

        else:    
            logger.info("Finished calculating match score for all ingredients")
            return ingredients_from_user


    def group_ingredients_based_on_match_score(self, min_match_score, ingredients_from_user) -> pd.DataFrame:

        try:
            # Calculate ingredient match score
            match_result = self.calculate_match_score_for_all_ingredients(ingredients_from_user)

            # Extract ingredients with high match score
            ingredient_with_high_match_score = match_result[match_result["match_score"] > min_match_score]

            # Extract ingredients with low match score
            ingredient_with_low_match_score = match_result[match_result["match_score"] <= min_match_score] 
        
        except Exception as e:
            logger.exception(f"Exception name: {type(e).__name__}")
        
        else:
            logger.info("Finished sorting ingredients based on match score")
            return ingredient_with_high_match_score, ingredient_with_low_match_score


    def _calculate_total_nutrients_per_ingredient_based_on_ingredient_weight(self, ingredients_and_nutrients_df) -> pd.DataFrame:

        try:
            # Calculate total nutrients per ingredient based on ingredient weight
            ingredients_and_nutrients_df.iloc[:, 2:] = ingredients_and_nutrients_df.iloc[:, 2:].multiply(ingredients_and_nutrients_df['Estimated weight (g)'], axis=0)

        except Exception as e:
            logger.exception(f"Exception name: {type(e).__name__}")

        else:
            logger.info("Finished calculating total nutrients per ingredient based on weight")
            return ingredients_and_nutrients_df


    def extract_ingredients_with_high_match_score_and_their_nutrients(self, ingredients_from_user) -> pd.DataFrame:

        try:
            # Extract ingredients with high match score
            high_score_ingredients, _ = self.group_ingredients_based_on_match_score(min_match_score=55, ingredients_from_user=ingredients_from_user)

            # Merge ingredients with nutrient values from database
            ingredients_and_nutrients_df = pd.merge(high_score_ingredients, self.ingredients_in_database, on="database_ingredient", how="left")

            # Drop irrelevant columns
            ingredients_and_nutrients_df.drop(columns=["database_ingredient", "match_score"], inplace=True)

            # Calculate total nutrients per ingredient based on ingredient weight
            ingredients_and_total_nutrients_df = self._calculate_total_nutrients_per_ingredient_based_on_ingredient_weight(ingredients_and_nutrients_df)

            # Drop irrelevant columns
            ingredients_and_total_nutrients_df.drop(columns=["Ingredient", "Estimated weight (g)"], inplace=True)
        
        except Exception as e:
            logger.exception(f"Exception name: {type(e).__name__}")

        else:
            logger.info("Finished extracting ingredients with high match score and their total nutrients")
            return ingredients_and_total_nutrients_df


    def sum_total_nutrients_in_the_meal(self, ingredients_from_user, date_input) -> pd.DataFrame:

        try:  
            # Extract ingredients and total nutrients for each ingredient
            total_nutrients_in_each_ingredient_df = self.extract_ingredients_with_high_match_score_and_their_nutrients(ingredients_from_user)

            # Sum all nutrients for the meal
            total_nutrients_in_the_meal= total_nutrients_in_each_ingredient_df.sum()
            total_nutrients_in_the_meal_df = pd.DataFrame(total_nutrients_in_the_meal).T
            total_nutrients_in_the_meal_df.index = [len(total_nutrients_in_each_ingredient_df)]

            # Extract sum of nutrients for the meal
            merged_df = pd.concat([total_nutrients_in_each_ingredient_df, total_nutrients_in_the_meal_df])
            merged_df.insert(loc=0, column="date_input", value=date_input)
            merged_df = merged_df.iloc[-1:]

        except Exception as e:
            logger.exception(f"Exception name: {type(e).__name__}")

        else:
            logger.info("Finished summing total nutrients in the meal")
            return merged_df
        

    def _define_age_group(self, user_age) -> str:
        
        if user_age <= 3:
            age_group = "1-3"
        elif user_age <= 8:
            age_group = "4-8"
        elif user_age <= 13:
            age_group = "9-13"
        elif user_age <= 18:
            age_group = "14-18"
        elif user_age <= 30:
            age_group = "19-30"
        elif user_age <= 50:
            age_group = "31-50"
        elif user_age <= 70:
            age_group = "51-70"
        else:
            age_group = "71+"
            
        return age_group
    

    def _transpose_and_reformat_dataframe(self, df=None) -> pd.DataFrame:

        # Transpose and reformat dataframe
        if df is not None:
            transposed_df = df.iloc[-1:].T.reset_index()
            transposed_df.columns = transposed_df.iloc[0]
            transposed_df = transposed_df[1:]

            # Rename column
            transposed_df = transposed_df.rename(columns={'date_input': 'Nutrient'})
        
        return transposed_df

    @handle_exception(funny_message="Your meal is exceptionally distinctive, and we may need to reconsider how to calculate its nutrient contents. Please visit us again later.")
    def total_nutrition_based_on_food_intake(self, ingredients_from_user, date_input) -> pd.DataFrame:

        # Extracts total nutrients in the meal
        df = self.sum_total_nutrients_in_the_meal(ingredients_from_user, date_input)
        
        # Extracts tranposed dataframe        
        transposed_df = self._transpose_and_reformat_dataframe(df)

        # Converts nutrient values into float
        transposed_df[date_input] = transposed_df[date_input].astype(float).round(1)

        # Showing total nutrients on streamlit
        st.table(transposed_df.style.format({date_input: "{:.1f}"}))

        logger.info("Finished calculating total nutrients based on food intake")

        return transposed_df
