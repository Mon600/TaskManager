import logging
from typing import Dict, Any


from asyncpg import PostgresError
from sqlalchemy.exc import SQLAlchemyError

from src.shared.db.repositories.role_repository import RoleRepository
from src.shared.schemas.Project_schemas import ProjectMemberExtend
from src.shared.schemas.Role_schemas import RoleSchema
from src.shared.mongo.db.models import ChangeRoleActionData, ChangeUserRoleActionData
from src.shared.mongo.repositories.mongo_repositroy import MongoRepository
from src.shared.schemas.User_schema import UserSchema


class RoleService:
    def __init__(self, repository: RoleRepository, mongo: MongoRepository):
        self.repository = repository
        self.mongo = mongo
        self.logger = logging.getLogger(__name__)

    async def new_role(self, project_id: int, role: RoleSchema):
        try:
            role_dict = role.model_dump()
            await self.repository.add_role(project_id, role_dict)
            return True
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

    async def role_update(self, role_id: int, role: RoleSchema, user: Dict[str, Any], project_id: int) -> Dict[str, Any]:
        role_dict = role.model_dump()
        try:
            old_data = await self.repository.update_role_info(role_id, new_data=role_dict)
            if old_data:
                action = ChangeRoleActionData(role_id=role_id, old_data=old_data, new_data=role_dict)
                await self.mongo.add_to_db(action, project_id, user)
                return {'ok': True, 'detail': 'Role successfully updated'}
            else:
                raise KeyError('Role not Found.')
        except ValueError as e:
            self.logger.warning(f"Ошибка: {e}")
            raise e


    async def role_delete(self, role_id: int):
        try:
            await self.repository.delete_by_id(role_id)

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

            old_data = ProjectMemberExtend.model_validate(res['old_data'])
            changed_user = old_data.user_rel.model_dump()
            old_role = old_data.role_rel.model_dump()

            new_role = RoleSchema.model_validate(res['new_data']).model_dump()
            action = ChangeUserRoleActionData(changed_role_user=changed_user,
                                              old_data=old_role,
                                              new_data=new_role)
            await self.mongo.add_to_db(action, project_id, user)
            return action
        except ValueError as e:
            self.logger.warning(f'Ошибка: {e}')
            raise e
        except (SQLAlchemyError, PostgresError) as e:
            self.logger.warning(f'Ошибка: {e}')
            raise e