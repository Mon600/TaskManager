from typing import Optional, Dict, Any

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from src.shared.config import get_mongo_db_url, get_mongo_db_name
from src.shared.mongo.db.models import History, BaseActionData


class Database:
    def __init__(self, db_url: str, db_name: str):
        self.db_url = db_url
        self.db_name = db_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self):
        self.client = AsyncIOMotorClient(self.db_url)
        self.db = self.client[self.db_name]


    async def init(self):
        await init_beanie(
            database=self.db,
            document_models=[History]
        )

    async def close(self):
        if self.client:
            self.client.close()


database = Database(get_mongo_db_url(), get_mongo_db_name())