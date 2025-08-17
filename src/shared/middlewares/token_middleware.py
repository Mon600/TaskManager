import datetime
import json
import logging
from typing import Dict

import aiormq.exceptions
from fastapi import Request, Response

from redis.asyncio.client import Redis
from sqlalchemy.util import await_only
from starlette.middleware.base import BaseHTTPMiddleware


# from faststream.rabbit import RabbitBroker


# class RefreshTokenMiddleware(BaseHTTPMiddleware):
#     def __init__(self, app):
#         super().__init__(app)
#         self.redis = Redis.from_url("redis://localhost:6379", decode_responses=True)
#         self.broker = RabbitBroker()
#         self.logger = logging.getLogger(__name__)
#
#     async def dispatch(self, request: Request, call_next):
#         timestamp = datetime.datetime.now().timestamp()
#         last_time = request.session.get('last_time_timestamp', 0)
#         if (timestamp - last_time) > 600:
#             refresh_token = request.cookies.get('refresh_token')
#             if not refresh_token:
#                 return await call_next(request)
#             access_token_json = await self.redis.get(f'access_for_{refresh_token}')
#             if not access_token_json is None:
#                 access_token = json.loads(access_token_json)
#                 response = await call_next(request)
#                 response.set_cookie(
#                     key="access_token",
#                     value=access_token['token'],
#                     max_age=30 * 60,
#                     secure=True,
#                     httponly=True,
#                     samesite="strict"
#                 )
#                 await self.redis.delete(f'access_for_{refresh_token}')
#                 return response
#             try:
#                 await self.broker.connect()
#                 await self.broker.publish(
#                     message={"refresh_token": refresh_token},
#                     queue="refresh_tokens"
#                 )
#             except aiormq.exceptions.ChannelInvalidStateError as e:
#                 self.logger.warning(f'Ошибка подключения к брокеру {e}')
#         return await call_next(request)

