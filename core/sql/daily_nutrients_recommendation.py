file_path = "data/csv/daily_nutrients_recommendation.csv"
create_recommended_nutrients_query = """
    CREATE OR REPLACE TABLE ilab.main.daily_nutrients_recommendation (
        gender STRING,
        age_start FLOAT,
        age_end FLOAT,
        nutrient STRING,
        daily_requirement_intake FLOAT,
        measurement STRING
    );

    INSERT INTO ilab.main.daily_nutrients_recommendation 
    SELECT * 
    FROM read_csv(
        '{file_path}',
        delim = ',',
        skip=1
    );

    SELECT COUNT(*) FROM recommended_nutrients;

 """