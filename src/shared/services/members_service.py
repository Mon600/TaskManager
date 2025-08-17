import logging

import pymongo.errors
from sqlalchemy.exc import SQLAlchemyError

from src.shared.db.repositories.project_member_repository import ProjectMemberRepository
from src.shared.mongo.db.models import DeleteUserActionData
from src.shared.schemas.Project_schemas import ProjectMemberSchema
from src.shared.schemas.User_schema import UserSchema
from src.shared.services.audit_service import AuditService


class MembersService:
    def __init__(self, repository: ProjectMemberRepository, audit: AuditService):
        self.repository = repository
        self.audit = audit
        self.logger = logging.getLogger(__name__)


    async def is_user_project_member(self, project_id: int, user_id: int):
        is_member = await self.repository.get_member_by_user_id(project_id, user_id)
        schema = ProjectMemberSchema.model_validate(is_member)
        return schema


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