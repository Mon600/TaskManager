import json
import logging
from typing import Annotated

from fastapi.params import Depends
from redis import exceptions
from starlette.requests import Request

from src.shared.dependencies.redis_deps import RedisDep
from src.shared.dependencies.service_deps import auth_service, members_service
from src.project.auth_service.jwt.jwt import decode_token
from src.shared.schemas.Project_schemas import ProjectContext
from src.shared.schemas.Role_schemas import RoleSchema
from src.shared.schemas.User_schema import UserSchema

logger = logging.getLogger(__name__)


async def get_current_user(request: Request, service: auth_service, redis: RedisDep) -> UserSchema | None:
    if hasattr(request.state, 'current_user'):
        return request.state.current_user
    token = request.cookies.get('access_token')
    if not token:
        return None
    payload = await decode_token(token)
    if payload is None:
        return None
    try:
        user_info = await redis.get(f"current_user{payload['user_id']}")
        user_dict = json.loads(user_info)
        user_schema = UserSchema.model_validate(user_dict)
        request.state.current_user = user_schema
        return user_schema
    except:
        user_db = await service.get_user_data(payload['user_id'])
        if user_db:
            user_schema = UserSchema.model_validate(user_db)
            try:
                cached = await redis.get(f"current_user{payload['user_id']}")
                if not cached:
                    await redis.set(f"current_user{payload['user_id']}", user_schema.model_dump_json(), ex=3600)
            except exceptions.ConnectionError as e:
                logger.warning(f"Redis недоступен: {e}")
            return user_schema
        else:
            return None


current_user = Annotated[UserSchema, Depends(get_current_user)]


async def get_project_member(project_id: int,
                             user: current_user,
                             service: members_service) -> ProjectContext | None:
    if user is None:
        return None
    project_member = await service.is_user_project_member(project_id, user.id)
    if project_member is None:
        return None
    return ProjectContext(member=project_member, user=user)

project_context = Annotated[ProjectContext, Depends(get_project_member)]


async def get_user_role(project_id: int,
                        project_member: project_context,
                        service: members_service) -> RoleSchema | None:
    if project_member is None:
        return None
    return project_member.member.role_rel


user_role = Annotated[RoleSchema, Depends(get_user_role)]

