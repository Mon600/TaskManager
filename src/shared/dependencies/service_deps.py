from typing import Annotated

from fastapi import Depends

from src.shared.dependencies.redis_deps import RedisDep
from src.shared.dependencies.repository_deps import user_repository, project_repository, role_repository, \
    link_repository, \
    token_repository, task_repository, mongo_repository, members_repository, stat_repository
from src.project.management_service.services.audit_service import AuditService
from src.project.auth_service.services.auth_service import AuthService
from src.project.management_service.services.link_service import LinkService
from src.project.management_service.services.members_service import MembersService
from src.project.management_service.services.project_service import ProjectService
from src.project.management_service.services.role_service import RoleService
from src.project.statistics_service.services.statistic_service import StatisticService
from src.project.management_service.services.task_service import TaskService
from src.shared.services.user_service import UserService


async def get_auth_service(repository: user_repository,
                           tokens_repository: token_repository,
                           redis: RedisDep
                           ) -> AuthService:
    return AuthService(repository, tokens_repository, redis)

auth_service = Annotated[AuthService, Depends(get_auth_service)]


async def get_audit_service(mongo: mongo_repository) -> AuditService:
    return AuditService(mongo)


audit_service = Annotated[AuditService, Depends(get_audit_service)]

async def get_user_service(redis: RedisDep, repository: user_repository) -> UserService:
    return UserService(redis, repository)

user_service = Annotated[UserService, Depends(get_user_service)]

async def get_project_service(redis: RedisDep,
                              p_repository: project_repository,
                              audit: audit_service) -> ProjectService:
    return ProjectService(p_repository, audit, redis)

project_service = Annotated[ProjectService, Depends(get_project_service)]

async def get_link_service(repository: link_repository,
                           service: project_service,
                           redis: RedisDep,
                           audit: audit_service
                           ) -> LinkService:
    return LinkService(repository, service, redis, audit)

link_service = Annotated[LinkService, Depends(get_link_service)]

async def get_members_service(repository: members_repository, links: link_service, audit: audit_service) -> MembersService:
    return MembersService(repository, links, audit)

members_service = Annotated[MembersService, Depends(get_members_service)]



async def get_role_service(repository: role_repository, audit: audit_service) -> RoleService:
    return RoleService(repository, audit)

role_service = Annotated[RoleService, Depends(get_role_service)]




async def get_task_service(repository: task_repository, audit: audit_service) -> TaskService:
    return TaskService(repository, audit)

task_service = Annotated[TaskService, Depends(get_task_service)]


async def get_stat_service(repository: stat_repository):
    return StatisticService(repository)


stat_service = Annotated[StatisticService, Depends(get_stat_service)]



