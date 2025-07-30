from typing import Annotated
from fastapi import Depends

from src.shared.dependencies.redis_deps import RedisDep
from src.shared.dependencies.repository_deps import user_repository, project_repository, role_repository, link_repository, \
    token_repository, task_repository
from src.shared.services.auth_service import AuthService
from src.shared.services.link_service import LinkService
from src.shared.services.project_service import ProjectService
from src.shared.services.role_service import RoleService
from src.shared.services.task_service import TaskService
from src.shared.services.user_service import UserService


async def get_auth_service(repository: user_repository, tokens_repository: token_repository, redis: RedisDep) -> AuthService:
    return AuthService(repository, tokens_repository, redis)

auth_service = Annotated[AuthService, Depends(get_auth_service)]


async def get_user_service(redis: RedisDep, repository: user_repository) -> UserService:
    return UserService(redis, repository)

user_service = Annotated[UserService, Depends(get_user_service)]

async def get_project_service(redis: RedisDep, repository: project_repository) -> ProjectService:
    return ProjectService(repository, redis)

project_service = Annotated[ProjectService, Depends(get_project_service)]

async def get_role_service(repository: role_repository) -> RoleService:
    return RoleService(repository)

role_service = Annotated[RoleService, Depends(get_role_service)]

async def get_link_service(repository: link_repository, p_repository: project_repository, redis: RedisDep) -> LinkService:
    return LinkService(repository, p_repository, redis)

link_service = Annotated[LinkService, Depends(get_link_service)]


async def get_task_service(repository: task_repository) -> TaskService:
    return TaskService(repository)

task_service = Annotated[TaskService, Depends(get_task_service)]

