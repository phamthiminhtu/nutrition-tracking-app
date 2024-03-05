file_path = "data/csv/recommended_nutrients.csv"
create_recommended_nutrients_query = f"""
    CREATE OR REPLACE TABLE recommended_nutrients (
        gender STRING,
        age_start FLOAT,
        age_end_inclusive FLOAT,
        nutrient_lower STRING,
        daily_requirement_microgram_lower_bound FLOAT,
        daily_requirement_microgram_upper_bound FLOAT
    );

    INSERT INTO recommended_nutrients 
    SELECT * 
    FROM read_csv(
        '{file_path}',
        delim = ',',
        skip=1
    );

    SELECT COUNT(*) FROM recommended_nutrients;

 """