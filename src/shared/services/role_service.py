from pymongo.asynchronous.database import AsyncDatabase

from src.shared.db.repositories.role_repository import RoleRepository
from src.shared.models.Role_schemas import RoleSchema


class RoleService:
    def __init__(self, repository: RoleRepository):

        self.repository = repository

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

    async def role_update(self, role_id: int, role: RoleSchema):
        try:
            role_dict = role.model_dump()
            await self.repository.update_by_id(role_id, data=role_dict)
        except Exception as e:
            print(e)

    async def role_delete(self, role_id: int):
        try:
            await self.repository.delete_by_id(role_id)
        except Exception as e:
            print(e)

    async def new_member_role(self, member_id: int, project_id: int, role_id: int):
        try:
            res = await self.repository.update_role(member_id, project_id, role_id)
            return res
        except Exception as e:
            raise e