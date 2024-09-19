import requests
import os
from typing import List, Any

class DatabaseManager:
    def __init__(self, endpoint_url):
        self.endpoint_url = endpoint_url #os.getenv("DB_ENDPOINT_URL")

    def get_schema(self, file_uuid: str) -> str:
        """Retrieve the database schema."""
        try:
            response = requests.get(
                f"{self.endpoint_url}/get-schema/{file_uuid}"
            )
            response.raise_for_status()
            return response.json()['schema']
        except requests.RequestException as e:
            raise Exception(f"Error fetching schema: {str(e)}")

    def execute_query(self, file_uuid: str, query: str) -> List[Any]:
        """Execute SQL query on the remote database and return results."""
        try:
            response = requests.post(
                f"{self.endpoint_url}/execute-query",
                json={"file_uuid": file_uuid, "query": query}
            )
            response.raise_for_status()
            return response.json()['results']
        except requests.RequestException as e:
            raise Exception(f"Error executing query: {str(e)}")