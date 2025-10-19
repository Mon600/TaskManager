from typing import Dict, Any

from sqlalchemy import select, desc, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.shared.db.models import Role, ProjectMember
from src.shared.db.repositories.base_repository import BaseRepository
from src.shared.schemas.Project_schemas import ProjectMemberSchemaExtend
from src.shared.schemas.Role_schemas import RoleSchema


class RoleRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(Role, session)


    async def add_role(self, project_id: int, data: RoleSchema):
        data_dict = data.model_dump()
        role = Role(project_id=project_id, **data_dict)
        self.session.add(role)
        await self.session.commit()
        role_schema = RoleSchema.model_validate(role)
        return role_schema


    async def delete_role(self, role_id: int, project_id: int):
        stmt = (delete(Role)
                .where(
            Role.id == role_id,
            Role.project_id == project_id
        )
                .returning(Role)
                )
        result = await self.session.execute(stmt)
        role_db = result.scalars().one_or_none()
        print(role_db)
        role_schema = RoleSchema.model_validate(role_db)
        return role_schema

    async def get_roles(self, project_id: int):
        stmt = select(Role).where(Role.project_id == project_id).order_by(desc(Role.priority))
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def update_role_info(self, role_id: int, new_data: RoleSchema):
        old_data_stmt = select(Role).where(Role.id == role_id)
        old_data_res = await self.session.execute(old_data_stmt)
        old_data = old_data_res.scalars().one_or_none()
        if not old_data is None:
            old_data_dict = RoleSchema.model_validate(old_data)
        data_dict = new_data.model_dump()
        stmt = update(Role).where(Role.id == role_id).values(**data_dict)
        await self.session.execute(stmt)
        await self.session.commit()
        return old_data


    async def update_member_role(self, member_id: int, project_id: int, role_id: int):
        old_data_stmt = (select(ProjectMember)
                    .where(
                        ProjectMember.id == member_id,
                        ProjectMember.project_id == project_id)
                    .options(
                        selectinload(ProjectMember.role_rel),
                        selectinload(ProjectMember.user_rel)
                            )
                        )
        res_old_data = await self.session.execute(old_data_stmt)
        old_data = res_old_data.scalars().one_or_none()
        old_data_dict = ProjectMemberSchemaExtend.model_validate(old_data)
        if old_data_dict.role_id == role_id:
            raise ValueError("Old role and new role the same")
        stmt = (update(ProjectMember)
                 .where(
                        ProjectMember.project_id == project_id,
                        ProjectMember.id == member_id)
                 .values(role_id = role_id))
        await self.session.execute(stmt)
        await self.session.commit()

        new_data_stmt = select(Role).where(Role.id == role_id, Role.project_id == project_id)
        res_new_data = await self.session.execute(new_data_stmt)
        new_data = res_new_data.scalars().one_or_none()

        return {'old_data': old_data, "new_data": new_data}
