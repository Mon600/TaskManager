import logging

from asyncpg import PostgresError
from sqlalchemy.exc import SQLAlchemyError

from src.shared.db.repositories.role_repository import RoleRepository
from src.shared.mongo.db.models import ChangeUserRoleActionData, DeleteRoleActionData, \
    EditRoleActionData, CreateRoleActionData
from src.shared.schemas.Project_schemas import ProjectMemberSchemaExtend
from src.shared.schemas.Role_schemas import RoleSchema
from src.shared.schemas.User_schema import UserSchema
from src.shared.services.audit_service import AuditService


class RoleService:
    def __init__(self, repository: RoleRepository, audit: AuditService):
        self.repository = repository
        self.audit = audit
        self.logger = logging.getLogger(__name__)

    async def new_role(self, project_id: int, user: UserSchema, role: RoleSchema) -> CreateRoleActionData:
        try:
            role = await self.repository.add_role(project_id, role)
            try:
                data = CreateRoleActionData(created_role=role)
                await self.audit.log(project_id, user, data)
                return data
            except ValueError as e:
                self.logger.warning(f"Ошибка: {str(e)}")
                raise e
        except (SQLAlchemyError, PostgresError) as e:
            self.logger.warning(f'Ошибка: {e}')
            raise e

    async def get_roles(self, project_id: int):
        try:
            res = await self.repository.get_roles(project_id)
            return res
        except (SQLAlchemyError, PostgresError) as e:
            self.logger.warning(f'Ошибка: {e}')
            raise e

    async def role_update(self,
                          role_id: int,
                          role: RoleSchema,
                          user: UserSchema,
                          project_id: int) -> EditRoleActionData:
        try:
            old_data = await self.repository.update_role_info(role_id, new_data=role)
            if old_data:
                try:
                    data = EditRoleActionData(
                        role_id=role_id,
                        old_data=old_data,
                        new_data=role
                    )
                    await self.audit.log(project_id, user, data)
                    return data
                except ValueError as e:
                    self.logger.warning(f"Ошибка: {str(e)}")
                    raise  e
            else:
                raise KeyError('Role not Found.')
        except ValueError as e:
            self.logger.warning(f"Ошибка: {e}")
            raise e

    async def role_delete(self, role_id: int, project_id: int, user: UserSchema):
        try:
            deleted_role = await self.repository.delete_role(role_id, project_id)
            try:
                data = DeleteRoleActionData(deleted_role=deleted_role, role_id=role_id)
                await self.audit.log(project_id, user, data)
                return data
            except ValueError as e:
                self.logger.warning(f"Ошибка: {str(e)}")
                raise e
        except (SQLAlchemyError, PostgresError) as e:
            self.logger.warning(f"Ошибка: {e}")
            raise e

    async def new_member_role(self,
                              member_id: int,
                              project_id: int,
                              role_id: int,
                              user: UserSchema) -> ChangeUserRoleActionData:
        try:
            res = await self.repository.update_member_role(member_id, project_id, role_id)

            old_data = ProjectMemberSchemaExtend.model_validate(res['old_data'])
            changed_user = old_data.user_rel
            old_role = old_data.role_rel

            new_role = RoleSchema.model_validate(res['new_data']).model_dump()
            data = ChangeUserRoleActionData(changed_role_user=changed_user,
                                            old_data=old_role,
                                            new_data=new_role)
            await self.audit.log(project_id, user, data)
            return data
        except ValueError as e:
            self.logger.warning(f'Ошибка: {e}')
            raise e
        except (SQLAlchemyError, PostgresError) as e:
            self.logger.warning(f'Ошибка: {e}')
            raise e
