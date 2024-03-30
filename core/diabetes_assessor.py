import time
import pickle
import jinja2
import pandas as pd
import streamlit as st
from core.duckdb_connector import *
from core.sql.check_fruit_and_veggies_nutrients import check_fruit_and_veggies_intake_template
from core.utils import handle_exception, wait_while_condition_is_valid
from core.main_app_miscellaneous import MainAppMiscellaneous


USER_NUTRIENT_INTAKE_HISTORY_TABLE_ID = "ilab.main.user_nutrient_intake_history"
OVERALL_HEALTH_MAP = {
    'Excellent': 1,
    'Very good': 2,
    'Good': 3,
    'Fair': 4,
    'Poor': 5
}
FRUIT_AND_VEGGIES_REPRESENTATIVES = [
    "Vitamin A",
    "Vitamin C",
    "Zinc",
    "Vitamin E",
    "Magnesium",
    "Phosphorus"
]
MODEL_INPUT_SCHEMA_MAP = {
    "has_cholesterol_check": "CholCheck",
    "bmi": "BMI",
    "is_smoker": "Smoker",
    "has_stroke": "Stroke",
    "has_heart_disease": "HeartDiseaseorAttack",
    "has_physical_activity": "PhysActivity",
    "has_fruit_in_diet": "Fruits",
    "has_veggies_in_diet": "Veggies",
    "is_heavy_alcohol_consumer": "HvyAlcoholConsump",
    "overall_health": "GenHlth",
    "gender": "Sex",
    "age": "Age"
}
DIABETES_MODEL_OUTPUT_MAP = {
    "0": "Looks like your diabetes risk is very low! Keep up the healthy diet 💪",
    "1": "We advise you to consider consulting with a doctor to undergo screening for prediabetes",
    "2": "It seems there's a possibility that you may have diabetes. We kindly suggest considering a visit to your doctor for a health evaluation."
}

main_app_miscellaneous = MainAppMiscellaneous(has_openai_connection_enabled=False)

class DiabetesAssessor:

    def __init__(
        self,
        model_path="core/ml_models/diabetes_random_forest_model.sav"
    ) -> None:
        self.model = pickle.load(open(model_path, 'rb'))
        self.db = DuckdbConnector()
        self.jinja_environment = jinja2.Environment()

    def _convert_string_to_int(
        self,
        string_var:str
    ) -> int:
        int_var = 0 if string_var.lower() == "no" else 1
        return int_var

    def _map_string_to_int(
        self,
        string_var:str,
        predefined_int_dict:dict
    ) -> int:
        int_var = predefined_int_dict.get(string_var)
        return int_var

    def _check_user_fruit_and_veggie_intake_from_database(
        self,
        user_id:str
    ):
        query_template = self.jinja_environment.from_string(check_fruit_and_veggies_intake_template)
        query = query_template.render(
            nutrient_list=FRUIT_AND_VEGGIES_REPRESENTATIVES,
            user_nutrient_intake_history_table_id=USER_NUTRIENT_INTAKE_HISTORY_TABLE_ID,
            no_nutrient_threshold=4,
            user_id=user_id
        )
        has_fruit_and_veggie_intake_result = self.db.run_query(
            sql=query
        )
        return has_fruit_and_veggie_intake_result[0][0]

    def get_user_fruit_and_veggie_intake(
        self,
        user_id:str,
        layout_position=st
    ):
        has_fruit_and_veggie_intake_string = True
        layout_position.write("Did you know 🥦 fruits and veggies help predict diabetes level 🥑")

        if user_id is None:
            has_fruit_and_veggie_intake_string = layout_position.selectbox(
                "Last question, have you been consuming fruits and vegetables 1 or more times per day?",
                ("No", 'Yes'),
                index=None,
                placeholder="Select your answer..."
            )
        else:
            has_fruit_and_veggie_intake = self._check_user_fruit_and_veggie_intake_from_database(user_id=user_id)
            if has_fruit_and_veggie_intake:
                layout_position.write("Great! Your nutrion history shows that you have fruits and veggies in your diet!")
            else:
                layout_position.write("We checked your nutrion history and looks like you are lacking fruits and veggies in your diet.")
                has_fruit_and_veggie_intake_string = layout_position.selectbox(
                    "Do you think so?",
                    ("Yes", 'No, I have been consuming fruits and vegetables 1 or more times per day'),
                    placeholder="Select your answer..."
                )
                has_fruit_and_veggie_intake = True if has_fruit_and_veggie_intake_string == "Yes" else False
            return has_fruit_and_veggie_intake

    def get_user_input_in_health_survey(
        self,
        gender:str,
        layout_position=st
    ) -> dict:
        layout_position.write("We need some input from you to be able to assess your diabetes risk.")
        form = layout_position.form("diabetes_prediction_form")
        weight = form.number_input(
            "What's your weight (kg)?",
            value=None,
            placeholder="Type a number..."
        )
        height = form.number_input(
            "What's your height in meters?",
            value=None,
            placeholder="Type a number..."
        )
        is_smoker = form.selectbox(
            "Have you smoked at least 100 cigarettes in your entire life?",
            ("No", 'Yes'),
            help="Note: 5 packs = 100 cigarettes",
            index=None,
            placeholder="Select your answer..."
        )

        if gender == "female":
            is_heavy_alcohol_consumer = form.selectbox(
                "Do you have more than 7 alcoholic drinks per week?",
                ("No", 'Yes'),
                index=None,
                placeholder="Select your answer..."
            )
        else:
            is_heavy_alcohol_consumer = form.selectbox(
                "Do you have more than 14 alcoholic drinks per week?",
                ("No", 'Yes'),
                index=None,
                placeholder="Select your answer..."
            )

        has_physical_activity = form.selectbox(
            "Do you have any physical activity in the past 30 days?",
            ("No", 'Yes'),
            index=None,
            placeholder="Select your answer..."
        )

        has_stroke = form.selectbox(
            "Have you (ever told) had a stroke?",
            ("No", 'Yes'),
            index=None,
            placeholder="Select your answer..."
        )
        has_heart_disease = form.selectbox(
            "Do you have coronary heart disease or myocardial infarction?",
            ("No", 'Yes'),
            index=None,
            placeholder="Select your answer..."
        )

        has_cholesterol_check = form.selectbox(
            "Have you checked your cholesterol in the past 5 years?",
            ("No", 'Yes'),
            index=None,
            placeholder="Select your answer..."
        )

        overall_health = form.selectbox(
            "Please rate your overall health",
            ('Excellent', 'Very good', 'Good', 'Fair', 'Poor'),
            index=None,
            placeholder="Select your answer..."
        )

        submitted = form.form_submit_button("Submit")
        # wait until user inputs
        wait_while_condition_is_valid(condition=(not submitted))

        result = {
            "weight": float(weight),
            "height": float(height),
            "is_smoker": self._convert_string_to_int(is_smoker),
            "is_heavy_alcohol_consumer": self._convert_string_to_int(is_heavy_alcohol_consumer),
            "has_physical_activity": self._convert_string_to_int(has_physical_activity),
            "has_stroke": self._convert_string_to_int(has_stroke),
            "has_heart_disease": self._convert_string_to_int(has_heart_disease),
            "has_cholesterol_check": self._convert_string_to_int(has_cholesterol_check),
            "overall_health": self._map_string_to_int(string_var=overall_health, predefined_int_dict=OVERALL_HEALTH_MAP)
        }

        return result

    def get_user_data_for_prediction(
        self,
        is_logged_in,
        user_id,
        layout_position=st
    ):
        user_age_and_gender =  main_app_miscellaneous.get_user_age_and_gender(
            is_logged_in=is_logged_in,
            user_id=user_id,
            layout_position=layout_position
        )

        gender, age = user_age_and_gender.get("gender"), user_age_and_gender.get("age")

        health_survey_result = self.get_user_input_in_health_survey(
            gender=gender,
            layout_position=layout_position
        )

        bmi = health_survey_result.get('weight')/(health_survey_result.get('height')**2)

        has_fruit_and_veggie_intake = self.get_user_fruit_and_veggie_intake(user_id=user_id, layout_position=layout_position)

        health_survey_result['gender'] = 0 if gender == "female" else 1
        health_survey_result['age'] = age
        health_survey_result['bmi'] = bmi
        health_survey_result['has_fruit_in_diet'] = int(has_fruit_and_veggie_intake)
        health_survey_result['has_veggies_in_diet'] = int(has_fruit_and_veggie_intake)
        st.write("#### health_survey_result", health_survey_result)
        return health_survey_result

    def map_user_input_to_feed_to_model(self, health_survey_result:dict):
        df_input = pd.DataFrame(health_survey_result, index=[0]).rename(columns=MODEL_INPUT_SCHEMA_MAP)
        return df_input

    @handle_exception(has_random_message_printed_out=True)
    def make_diabetes_prediction(
        self,
        is_logged_in,
        user_id,
        layout_position=st
    ):
        if is_logged_in:
            health_survey_result = self.get_user_data_for_prediction(
                is_logged_in=is_logged_in,
                user_id=user_id,
                layout_position=layout_position
            )
            layout_position.write("Just one moment ⏳ we are trying to assess your diabetes risk...")
            time.sleep(2)
            df_input = self.map_user_input_to_feed_to_model(health_survey_result=health_survey_result)
            predictors = list(MODEL_INPUT_SCHEMA_MAP.values())
            prediction = str(int(self.model.predict(df_input[predictors])[0]))
            message = DIABETES_MODEL_OUTPUT_MAP.get(prediction)
            layout_position.write(message)
        else:
            layout_position.write("Looks like you haven't logged in, do you want to log in to assess your diabetes risk?")
        return message