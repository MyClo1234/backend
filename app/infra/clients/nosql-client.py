from typing import Optional

from azure.cosmos import ContainerProxy, CosmosClient, DatabaseProxy

from app.core.config import Config


class NoSqlClient:
    """Azure Cosmos DB 클라이언트"""

    def __init__(self):
        Config.check_api_key()

        self.endpoint = Config.AZURE_COSMOS_ENDPOINT
        self.key = Config.AZURE_COSMOS_KEY
        self.database = Config.AZURE_COSMOS_DATABASE

        if not self.endpoint or not self.key:
            raise ValueError("Azure Cosmos DB endpoint/key 설정이 필요합니다.")

        self.client = CosmosClient(self.endpoint, credential=self.key)

    def get_container(
        self,
        container_name: str,
        database_name: Optional[str] = None,
    ) -> ContainerProxy:
        """컨테이너 클라이언트 가져오기 (여러 컨테이너 사용 가능)"""
        db_name = database_name or self.database
        if not db_name:
            raise ValueError("Azure Cosmos DB database 이름이 필요합니다.")
        if not container_name:
            raise ValueError("Azure Cosmos DB container 이름이 필요합니다.")
        return self.client.get_database_client(db_name).get_container_client(
            container_name
        )

    def get_db(self) -> DatabaseProxy:
        if not self.database:
            raise ValueError("Azure Cosmos DB database 이름이 필요합니다.")
        return self.client.get_database_client(self.database)

    def close(self) -> None:
        self.client.close()


nosql_client = NoSqlClient()


def get_nosql_client() -> NoSqlClient:
    return nosql_client
