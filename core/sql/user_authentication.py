create_user_profiles_query = """
    CREATE OR REPLACE TABLE ilab.main.users (
        user_id STRING,
        gender STRING,
        age FLOAT,
        username  STRING,
        password STRING
    );
"""

create_user_profiles_query_2nd_version = """
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
    INSERT INTO {{ table_id }} BY NAME
    (WITH
        source_raw AS
            (SELECT
                $user_id AS user_id,
                $gender AS gender,
                $age AS age,
                $username AS username,
                $password AS password
        )
        ,source AS
            (SELECT
                CAST(user_id AS STRING) AS user_id,
                CAST(gender AS STRING) AS gender,
                CAST(age AS FLOAT) AS age,
                CAST(username as STRING) as username,
                CAST(password as STRING) AS password
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
            ON s.user_id = t.user_id
            WHERE t.user_id IS NULL
        )

        SELECT * FROM records_to_insert
    );
"""

register_new_user_query_2nd_version = """
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