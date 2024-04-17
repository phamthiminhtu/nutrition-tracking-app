create_user_profiles_table = """
    CREATE OR REPLACE TABLE ilab.main.user_details (
        username VARCHAR,
        name STRING,
        email STRING,
        age INTEGER,
        gender STRING,
        password VARCHAR
    );
"""

fetch_users_query = """
    SELECT username, user_id, password FROM {{table_id}}
"""

fetch_user_id = """
    SELECT user_id from {{table_id}}
    WHERE username iLike CAST($username as STRING)
"""

update_users_query = """
    UPDATE users
SET password = CAST($password as STRING)
WHERE username ilike CAST($username as STRING);
"""

register_new_user_query = """
    INSERT INTO {{ table_id }}
        (WITH raw AS (
            SELECT
                $username AS username,
                $name AS name,
                $email AS email,
                $age AS age,
                $gender AS gender,
                $password AS password
        ),
        source AS (
            SELECT
            CAST(username AS STRING) AS username,
            CAST(name AS STRING) AS name,
            CAST(email AS VARCHAR) as email,
            CAST(age as INTEGER) AS age,
            CAST(gender as STRING) AS gender,
            CAST(password as VARCHAR) AS password
        
        FROM raw
        )
        SELECT *
        FROM source
    );
"""