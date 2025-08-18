import logging

import pymongo.errors
from asyncpg import PostgresError
from sqlalchemy.exc import SQLAlchemyError

from src.shared.db.repositories.project_member_repository import ProjectMemberRepository
from src.shared.mongo.db.models import DeleteUserActionData, UserJoinActionData
from src.shared.schemas.Link_schemas import GetLinkSchema
from src.shared.schemas.Project_schemas import ProjectMemberSchema
from src.shared.schemas.User_schema import UserSchema
from src.shared.services.audit_service import AuditService
from src.shared.services.link_service import LinkService


class MembersService:
    def __init__(self, repository: ProjectMemberRepository, links: LinkService, audit: AuditService):
        self.repository = repository
        self.audit = audit
        self.link_service = links
        self.logger = logging.getLogger(__name__)


    async def is_user_project_member(self, project_id: int, user_id: int):
        is_member = await self.repository.get_member_by_user_id(project_id, user_id)
        schema = ProjectMemberSchema.model_validate(is_member)
        return schema

    async def add_member(self, code: str, user: UserSchema) -> UserJoinActionData:
        user_id = user.id
        link_info = await self.link_service.get_project_by_code(code)
        if not link_info:
            raise KeyError("Not found")
        project = link_info.project_rel
        project_id = project.id

        if project.status != 'open':
            raise AttributeError("Project is close")

        data_for_save = {
            'project_id': project.id,
            'role_id': project.default_role_id,
            'user_id': user_id,
        }

        try:
            await self.repository.add_member(data_for_save)
            data = UserJoinActionData(project_data=project)
            await self.audit.log(project.id, user, data)
            return data
        except (SQLAlchemyError, PostgresError) as e:
            self.logger.error(f"Ошибка БД {e}")
            raise e
        except ValueError as e:
            self.logger.error(f"Ошибка валидации {project_id}, {e}")
            raise e


    async def delete_member(self,
                            project_id: int,
                            member_id: int,
                            user: UserSchema,
                            reason: str = '') -> DeleteUserActionData:
        try:
            deleted_member = await self.repository.delete_member(project_id, member_id)
            data=DeleteUserActionData(
                 reason=reason,
                 deleted_user=deleted_member
            )
            await self.audit.log(project_id, user, data)
            return data
        except (SQLAlchemyError, pymongo.errors.OperationFailure) as e:
            self.logger.warning(f"Ошибка {e}")
            raise e