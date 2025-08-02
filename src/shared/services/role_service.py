from typing import Dict, Any


from src.shared.db.repositories.role_repository import RoleRepository
from src.shared.models.Project_schemas import ProjectMemberExtend
from src.shared.models.Role_schemas import RoleSchema
from src.shared.mongo.db.models import ChangeRoleActionData, ChangeUserRoleActionData
from src.shared.mongo.repositories.mongo_repositroy import MongoRepository


class RoleService:
    def __init__(self, repository: RoleRepository, mongo: MongoRepository):
        self.repository = repository
        self.mongo = mongo

    async def new_role(self, project_id: int, role: RoleSchema):
        try:
            role_dict = role.model_dump()
            await self.repository.add_role(project_id, role_dict)
        except Exception as e:
            print(e)

    async def get_roles(self, project_id: int):
        try:
            res = await self.repository.get_roles(project_id)
            return res
        except Exception as e:
            print(e)
            return None

    async def role_update(self, role_id: int, role: RoleSchema, user: Dict[str, Any], project_id: int):
        try:
            role_dict = role.model_dump()
            old_data = await self.repository.update_role_info(role_id, new_data=role_dict)
            if old_data:
                old_data_dict = RoleSchema.model_validate(old_data).model_dump()
                action = ChangeRoleActionData(role_id=role_id, old_data=old_data_dict, new_data=role_dict)
                await self.mongo.add_to_db(action, project_id, user)
                return True
            return False
        except Exception as e:
            print(e)

    async def role_delete(self, role_id: int):
        try:
            await self.repository.delete_by_id(role_id)
        except Exception as e:
            print(e)

    async def new_member_role(self, member_id: int, project_id: int, role_id: int, user: Dict[str, Any]):
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
        except Exception as e:
            raise e