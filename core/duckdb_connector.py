import duckdb
from utils import handle_exception


class DuckdbConnector:

    def __init__(
            self,
            database_path="data/ilab.db",
            read_only=False
        ) -> None:
        self.database_path = database_path
        self.read_only = read_only

    @handle_exception(has_funny_message_shown_on_ui=False)
    def run_query(self, sql, result_format='list', parameters=None) -> list:
        """
            - Open connection to DuckDB database (default database path is data/ilab.db)
            - Run the provided sql.
            - Convert the query result into the specified result_format. Supported format:
                - list
                - dataframe
                - polardataframe
            - Close connection.
        """
        if parameters is None:
            parameters = {}

        with duckdb.connect(self.database_path, read_only=self.read_only) as con:
            query_connector = con.execute(sql, parameters=parameters)
            if result_format == 'list':
                query_result = query_connector.fetchall()
            elif result_format == 'dataframe':
                query_result = query_connector.df()
            elif result_format == 'polardataframe':
                query_result = query_connector.pl()
            else:
                raise Exception(f"The result_format {result_format} is not supported.")
            # the context manager closes the connection automatically
        return query_result
    