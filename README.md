# MealMinder - A Generative AI - Powered Nutrition Tracking App
This repo is the main source code for our MealMinder App, a nutrition tracking app built and deployed on Streamlit Cloud with the following features:

- User-friendly tools to interpret complex nutritional information: This involves intuitive visualisations, summaries, and comparisons to established dietary guidelines. We developed a clear and easy-to-use interface for entering meals, focusing on simplicity and minimising manual data entry.

- Robust ingredient database and historical nutrient tracking: We built a comprehensive database of foods and their nutritional values by leveraging reliable datasets provided by the Australian government. We enable users to access their historical nutrient intake data from the database and gain personalised insights.

- Ingredient estimation: Our app utilises OpenAI to estimate ingredients based on simple dish names (user input) as opposed to providing a whole list of ingredients manually

- Informative charts: The app developed intuitive charts, and graphs that display historical dietary intake, highlighting trends, deficiencies, and successes.

- Secure authentication: Given the confidential nature of personal nutrition data, we implemented robust login systems with options for authentication.

- Early health issues detection: We also enable users to detect health issues by incorporating external survey data and users’ historical nutrition data using Classification (Random Forest Algorithm).

Here is our little demo video on Youtube, check it out!
[![MealMinder](https://github.com/phamthiminhtu/ilab/assets/56192840/a1218196-8feb-4bea-be93-e3cab18c1206)](https://youtu.be/aIandiLboPo"MealMinder")


# Pre-requisites
- Install the requirements.txt
- Have an OpenAPI API KEY. Docs:
    - https://platform.openai.com/docs/quickstart?context=python#:~:text=write%20any%20code.-,MacOS,-Windows
    - https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-keyx
