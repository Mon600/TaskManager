import json

from fastapi.params import Depends
from typing import Annotated

from starlette.requests import Request
from starlette.responses import RedirectResponse

from src.shared.dependencies.redis_deps import RedisDep

from src.shared.dependencies.service_deps import auth_service
from src.shared.jwt.jwt import decode_token



async def get_current_user(request: Request, service: auth_service, redis: RedisDep):
    token = request.cookies.get('access_token')
    print(token)
    if token:
        payload = await decode_token(token)
        try:
            user_info = await redis.get(f"current_user{payload['user_id']}")
            res = json.loads(user_info)
            return res
        except:
            user = await service.get_user_data(payload['user_id'])
            if user:
                try:
                    await redis.set(f"current_user{payload['user_id']}", json.dumps(user), ex=3600)
                except Exception as e:
                    print(f"Redis недоступен: {e}")
                return user
            else:
                return RedirectResponse('/auth')
    else:
        return None

current_user = Annotated[str, Depends(get_current_user)]
