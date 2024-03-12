
combine_user_actual_vs_recommend_intake_logic = """
    ,recommended_daily_nutrient_intake AS
            (SELECT
                gender,
                age_start,
                age_end AS age_end,
                nutrient AS nutrient,
                AVG(daily_requirement_intake) AS daily_recommended_intake,
                MAX(measurement) AS measurement
            FROM recommended_daily_nutrient_intake_source
            GROUP BY
                gender,
                age_start,
                age_end,
                nutrient)

    SELECT
        u.*,
        r.daily_recommended_intake,
        r.daily_recommended_intake - u.actual_intake AS intake_diff,
        CEIL((r.daily_recommended_intake - u.actual_intake)*100 / daily_recommended_intake) AS intake_diff_percent,
        r.measurement
    FROM user_nutrient_intake AS u
    -- only get nutrients that exist in recommended_daily_nutrient_intake table
    INNER JOIN recommended_daily_nutrient_intake AS r
        ON u.gender = r.gender
        AND u.age BETWEEN r.age_start AND r.age_end
        AND u.nutrient = r.nutrient
    ;
"""

anonymous_user_daily_nutrient_intake_query_template = """
    WITH
        user_nutrient_intake AS
            (SELECT
                gender,
                age,
                nutrient,
                dish_description,
                SUM(actual_intake) AS actual_intake
            FROM {{ user_intake_df_temp_name }}
            GROUP BY
                gender,
                age,
                nutrient,
                dish_description)

        ,recommended_daily_nutrient_intake_source AS
            (SELECT * FROM {{ recommended_daily_nutrient_intake_table_id }})

        {{ combine_user_actual_vs_recommend_intake_logic }}

"""

create_user_daily_nutrient_intake_query_template = """
    CREATE OR REPLACE VIEW ilab.main.user_daily_recommended_intake_history AS
    WITH
        recommended_daily_nutrient_intake_source AS
            (SELECT * FROM {{ recommended_daily_nutrient_intake_table_id }})

        ,user_nutrient_intake AS 
            (SELECT
                user_id,
                gender,
                age,
                nutrient,
                DATE_TRUNC('day', created_datetime_tzsyd) AS record_date,
                SUM(actual_intake) AS actual_intake
            FROM {{ user_nutrient_intake_history_table_id }}
            GROUP BY
                user_id,
                gender,
                age,
                nutrient,
                record_date
            )
            
        {{ combine_user_actual_vs_recommend_intake_logic }}
"""
