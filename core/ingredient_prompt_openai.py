import json
import openai
import pandas as pd

class OpenAIAssistant:
    def __init__(self, openai_client) -> None:
        self.openai_client = openai_client
    
    def convert_input_df_into_text_prompt(self,ingredient_data):
        '''
            Check with Michael      
        '''
        input_data = NutrientMaster.group_ingredients_based_on_match_score(self, min_match_score, ingredients_from_user)
        ingredient_prompt = {}
        for item in input_data:
            ingredient_prompt[item['Ingredient']] = {'Estimated weight (g)': item['Estimated weight (g)']}
        print(ingredient_prompt)

    def run_prompt(self, ingredient_prompt) -> dict:
        '''
            - To get this running, you should have your OPENAI_API_KEY stored in your environment variables.
                Details at: 
                    - https://platform.openai.com/docs/quickstart?context=python#:~:text=write%20any%20code.-,MacOS,-Windows
                    - https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key
            - Tutorial: https://platform.openai.com/docs/quickstart?context=python
            - Input: prompt.
            - Output: JSON-like string.
        '''
        seed = 1234 # to get deterministic estimation
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant designed to output JSON with format ingredient: weight (interger type)."},
                {"role": "user", "content": f"Provide a table output for approximate average values for, Energy (kJ), Protein (g), Total water (L), Thiamin (B1) (mg), Riboflavin (B2) (mg), Niacin (mg), Pyridoxine (B6) (mg), Cobalamin (B12) (μg), Vitamin A (μg), Vitamin C (mg), Vitamin D (μg), Vitamin E (mg), Calcium (mg), Phosphorus (mg), Zinc (mg), Iron (mg), Magnesium (mg), Sodium (mg) and Potassium (mg), for the following ingredients and considering their weights, input from the following: {ingredient_prompt}?"},
                {"role": "assistant", "content": "the response should only provide the amount and as a json output"},
            ],
            seed=seed,
            response_format={ "type": "json_object"}
        )
        generated_content = response.choices[0].message.content
        result = {
            "status": 200,
            "value": generated_content
        }
        return result
    
    def convert_json_into_df(self, generated_content) -> dataframe:
        # Using json.loads() to convert the JSON string into a Python dictionary
        python_dict = json.loads(generated_content)
        #Convert to dataframe
        df_generated_content = pd.DataFrame(python_dict, index=[0]).T.reset_index()
        df_generated_content.columns = ['Nutrients', 'Total']
        print(df_generated_content)