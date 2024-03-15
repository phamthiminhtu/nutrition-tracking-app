import pandas as pd
from openai import OpenAI
import os

OPENAI_API_KEY = "OPENAI_API_KEY"
OPENAI_CLIENT = OpenAI(api_key=os.environ.get(OPENAI_API_KEY),)

prompt = "Based on your preferences - nutrient: protein-3000000.0, fluids(including plain water, milk and other drinks)-100000000.0, fibre-3000000.0, vitamin a--50.0, thiamin-100.0, riboflavin-100.0, niacin-1000.0, vitamin b6--50.0, vitamin b12-0.20000000000000007, folate-50.0, vitamin c-10000.0, calcium-100000.0, iodine-20.0, iron-2000.0, magnesium-10000.0, potassium-100000.0, sodium-50000.0, zinc--1000.0, and cuisine: Chinese, recommend a dish."

response = OpenAI.Completions.create(
    engine="davinci-002",  
    prompt=prompt,
    max_tokens=150,  
    temperature=0.7,  
    n=1,  
    stop=None  
)

print(prompt)
print(response.choices[0].text.strip())