from typing import Optional

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from src.project.management_service.mongo.db.models import History


class Database:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self, db_url: str, db_name: str):
        self.client = AsyncIOMotorClient(db_url)
        self.db = self.client[db_name]

        await init_beanie(
            database=self.db,
            document_models=[History]
        )




db = Database()