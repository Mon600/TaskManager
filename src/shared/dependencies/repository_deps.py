from typing import Annotated

from fastapi import Depends

from src.project.management_service.repositories.link_repository import LinkRepository
from src.project.management_service.repositories.project_member_repository import ProjectMemberRepository
from src.project.management_service.repositories.project_repository import ProjectRepository
from src.project.management_service.repositories.role_repository import RoleRepository
from src.project.statistics_service.repositories.statistic_repository import StatisticRepository
from src.project.management_service.repositories.task_repository import TaskRepository
from src.project.auth_service.repositories.token_repository import TokenRepository
from src.shared.db.repositories.user_repository import UserRepository
from src.shared.dependencies.db_deps import SessionDep
from src.project.management_service.mongo.repositories.mongo_repositroy import MongoRepository


async def get_user_repository(session: SessionDep) -> UserRepository:
    return UserRepository(session)


user_repository = Annotated[UserRepository, Depends(get_user_repository)]


async def get_project_repository(session: SessionDep) -> ProjectRepository:
    return ProjectRepository(session)


project_repository = Annotated[ProjectRepository, Depends(get_project_repository)]


async def get_role_repository(session: SessionDep) -> RoleRepository:
    return RoleRepository(session)


role_repository = Annotated[RoleRepository, Depends(get_role_repository)]


async def get_link_repository(session: SessionDep) -> LinkRepository:
    return LinkRepository(session)


link_repository = Annotated[LinkRepository, Depends(get_link_repository)]


async def get_token_repository(session: SessionDep) -> TokenRepository:
    return TokenRepository(session)


token_repository = Annotated[TokenRepository, Depends(get_token_repository)]


async def get_task_repository(session: SessionDep) -> TaskRepository:
    return TaskRepository(session)


task_repository = Annotated[TaskRepository, Depends(get_task_repository)]


async def get_members_repository(session: SessionDep) -> ProjectMemberRepository:
    return ProjectMemberRepository(session)


members_repository = Annotated[ProjectMemberRepository, Depends(get_members_repository)]


async def get_mongo_repository() -> MongoRepository:
    return MongoRepository()


mongo_repository = Annotated[MongoRepository, Depends(get_mongo_repository)]


async def get_stat_repository(session: SessionDep) -> StatisticRepository:
    return StatisticRepository(session)


stat_repository = Annotated[StatisticRepository, Depends(get_stat_repository)]