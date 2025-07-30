import json
import secrets

from pymongo.asynchronous.database import AsyncDatabase
from redis.asyncio import Redis

from src.shared.db.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, redis: Redis, repository: UserRepository):
        self.redis = redis
        self.repository = repository


    async def generate_code(self,  email: str, user_id: int) -> str:
        code = secrets.token_urlsafe(32)
        serialized_data = json.dumps({"email": email, "id": user_id})
        await self.redis.set(code, serialized_data, ex=1080)
        return code

    async def confirm_email(self, code: str):
        email = await self.redis.get(code)
        if email:
            data = json.loads(email)
            res = await self.repository.update_by_id(id=data["id"], data=data)
            await self.redis.delete(code)
            await self.redis.delete(f"current_user{data['id']}")
            return res
        else:
            return False
