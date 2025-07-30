from typing import Annotated

from redis.asyncio import Redis
from fastapi import Depends


async def get_redis():
    redis = Redis.from_url("redis://127.0.0.1:6379",
                         decode_responses=True)
    try:
        yield redis
    finally:
        await redis.aclose()

RedisDep = Annotated[Redis, Depends(get_redis)]