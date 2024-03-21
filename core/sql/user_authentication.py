create_user_profiles_query = """
    CREATE OR REPLACE TABLE ilab.main.users (
        user_id STRING,
        gender STRING,
        age FLOAT,
        username  STRING,
        password STRING
    );
"""
fetch_users_query = """
    SELECT user_id, username, password FROM {{table_id}}
"""

update_users_query = """
    UPDATE users
SET username = 'Alfred', City= 'Gotham'
WHERE user_id = 'alfy';
"""
register_new_user_query = """
    INSERT INTO {{ table_id }} VALUES ({{user_info}})
"""