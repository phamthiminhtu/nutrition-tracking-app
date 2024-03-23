create_user_nutrient_intake_history_query = """
    CREATE OR REPLACE TABLE ilab.main.user_nutrient_intake_history (
        user_id STRING,
        gender STRING,
        age FLOAT,
        dish_description AS STRING,
        meal_id STRING,
        create_timestamp TIMESTAMP,
        nutrient STRING,
        actual_intake FLOAT
    );
"""

insert_new_record_user_nutrient_intake_history_query_template = """
    INSERT INTO {{ table_id }} BY NAME
    (WITH
        source_raw AS
            (SELECT
                user_id AS user_id,
                gender AS gender,
                age AS age,
                dish_description AS dish_description,
                $meal_id AS meal_id,
                $meal_fingerprint AS meal_fingerprint,
                $created_datetime_tzsyd AS created_datetime_tzsyd,
                nutrient AS nutrient,
                actual_intake AS actual_intake
            FROM {{ user_intake_df_temp_name }}
            )

        ,source AS
            (SELECT
                CAST(user_id AS STRING) AS user_id,
                CAST(gender AS STRING) AS gender,
                CAST(age AS FLOAT) AS age,
                CAST(dish_description AS STRING) AS dish_description,
                CAST(meal_id AS STRING) AS meal_id,
                CAST(meal_fingerprint AS STRING) AS meal_fingerprint,
                STRPTIME(created_datetime_tzsyd, '%Y-%m-%d %H:%M:%S') AS created_datetime_tzsyd,
                CAST(nutrient AS STRING) AS nutrient,
                CAST(actual_intake AS FLOAT) AS actual_intake
            FROM source_raw
            )

        ,target AS (
            SELECT * FROM {{ table_id }}
        )

        ,records_to_insert AS (
            SELECT
                s.*
            FROM source AS s
            LEFT JOIN target AS t
            ON s.meal_id = t.meal_id
            WHERE t.meal_id IS NULL
        )

        SELECT * FROM records_to_insert
    );
"""