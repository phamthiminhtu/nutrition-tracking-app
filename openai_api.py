import json
from openai import OpenAI
import pandas as pd
import streamlit as st
from utils import handle_exception

class OpenAIAssistant:
    def __init__(self, openai_client) -> None:
        self.openai_client = openai_client
    
    @handle_exception
    def run_prompt(self, prompt) -> dict:
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
        completion = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant designed to output JSON with format ingredient: weight (interger type)."},
                {"role": "user", "content": prompt}
            ],
            seed=seed,
            response_format={ "type": "json_object"}
        )
        estimation = completion.choices[0].message.content
        result = {
            "status": 200,
            "value": estimation
        }
        return result

    @handle_exception(has_random_message_printed_out=True)
    def extract_estimation_to_dataframe(self, estimation, df=None, headers=None) -> pd.DataFrame:
        """
            Input: json-like string
            Output: dataframe
        """
        if df is None:
            df = pd.DataFrame()
        if headers is None:
            headers = ["Ingredient", "Estimated weight (g)"]
        if estimation:
            estimation_dict = json.loads(estimation)
            df = pd.DataFrame(estimation_dict.items(), columns=headers)
        return df

    def estimate_and_extract_dish_info(self, dish_description, ingredient_estimation_prompt, df=None) -> pd.DataFrame:
        """
            Get user's input: str - description of the dish.
            Return a dataframe containing info regarding weights of dish's ingredients.
        """
        if df is None:
            df = pd.DataFrame()
        if dish_description:
            result = self.run_prompt(prompt=ingredient_estimation_prompt)
            if result.get("status") == 200:
                df = self.extract_estimation_to_dataframe(estimation=result.get("value"))
                if not df.empty:
                    st.write(f'Here is our estimated weight of each ingredient for one serving of 🍕 {dish_description} 🍳:')
                    st.dataframe(df)
                else:
                    message = "Sorry, we've tried our best but cannot estimate the ingredients of your dish. Can you try to describe it differently?"
                    st.write(message)
            else:
                st.write(result.get("value"))
                print(result.get("exception"))
        return df