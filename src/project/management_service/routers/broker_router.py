import json

from eventlet.green.http.client import responses
from faststream.rabbit.fastapi import RabbitRouter
from starlette.requests import Request
from starlette.responses import Response

from src.shared.dependencies.redis_deps import RedisDep
from src.shared.dependencies.user_deps import current_user

router = RabbitRouter()

@router.subscriber('access_tokens')
async def get_access_token(data: dict, redis: RedisDep):
    await redis.set(f'access_for_{data['refresh_token']}', json.dumps(data['access_token']), ex=600)


