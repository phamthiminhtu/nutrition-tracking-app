create_user_nutrient_intake_history_query = """
    CREATE OR REPLACE TABLE ilab.main.user_telegram_info (
        telegram_username STRING,
        telegram_chat_id STRING
    );
"""

insert_new_record_user_telegram_info_query_template = """
    INSERT INTO {{ table_id }} BY NAME
    (WITH
        source_raw AS
            (SELECT
                '{{ telegram_username }}' AS telegram_username,
                '{{ telegram_chat_id }}' AS telegram_chat_id
            )

        ,source AS
            (SELECT
                CAST(telegram_username AS STRING) AS telegram_username,
                CAST(telegram_chat_id AS STRING) AS telegram_chat_id
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
            ON s.telegram_username = t.telegram_username
            WHERE t.telegram_username IS NULL
        )

        SELECT * FROM records_to_insert
    );
"""