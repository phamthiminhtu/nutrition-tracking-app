check_fruit_and_veggies_intake_template = """
    WITH
        fruit_and_veggies_nutrients AS
            (
                SELECT *
                FROM (
                    VALUES
                        {% for fruit_veggies_nutrient in nutrient_list %}
                            ('{{ fruit_veggies_nutrient }}') {% if not loop.last %} , {% endif %}
                        {% endfor %}
                ) Nutrients(nutrient)
            )

        ,user_nutrient_intake AS
            (SELECT
                nutrient,
                DATE_TRUNC('day', meal_record_date) AS record_date,
                SUM(actual_intake) AS actual_intake
            FROM {{ user_nutrient_intake_history_table_id }}
            WHERE
                user_id = '{{ user_id }}'
                AND nutrient IN (
                    {% for fruit_veggies_nutrient in nutrient_list %}
                        '{{ fruit_veggies_nutrient }}',
                    {% endfor %}
                    '__placeholder__'
                )
            GROUP BY
                nutrient,
                record_date
            )

        ,fruit_and_veggies_nutrient_consumption AS
            (SELECT
                f.nutrient,
                (
                    COUNT(DISTINCT (CASE WHEN u.actual_intake > 0 THEN u.record_date END))
                    /COUNT(DISTINCT u.record_date)
                ) AS fruit_and_veggies_comsumption_ratio
            FROM fruit_and_veggies_nutrients as f
            LEFT JOIN user_nutrient_intake AS u
            ON f.nutrient = u.nutrient
            GROUP BY
                f.nutrient
            )

        SELECT
            /*
                if user has consumed more than <no_nutrient_threshold>
                out of total number of nutrients representing fruits and veggies
                for 70% of the time (number of record dates in the database),
                assume they has consumed enough fruit and veggies.
            */
            COUNT_IF(fruit_and_veggies_comsumption_ratio > 0.7) >= {{ no_nutrient_threshold }} AS has_consumed_fruit_and_veggies
        FROM fruit_and_veggies_nutrient_consumption

"""
