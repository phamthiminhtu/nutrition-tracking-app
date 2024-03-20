create_user_profiles_query = """
    CREATE OR REPLACE TABLE ilab.main.users (
        user_id STRING,
        gender STRING,
        age FLOAT,
        username  STRING,
        password STRING
    );
"""
get_users_query = """
    SELECT * FROM {{table_id}}
"""

update_users_query = """
    UPDATE users
SET username = 'Alfred', City= 'Gotham'
WHERE user_id = 'alfy';
"""
register_new_user_query = """
    INSERT INTO {{ table_id }} BY NAME
    (WITH
        source_raw AS
            (SELECT
                user_id AS user_id,
                gender AS gender,
                age AS age,
                username AS username,
                password AS password
            FROM {{ temp_user_df }}
            )

        ,source AS
            (SELECT
                CAST(user_id AS STRING) AS user_id,
                CAST(gender AS STRING) AS gender,
                CAST(age AS FLOAT) AS age,
                CAST(username AS STRING) AS username,
                CAST(password AS STRING) AS password
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