from typing import Dict, Any

from sqlalchemy import select, desc, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.shared.db.models import Role, ProjectMember
from src.shared.db.repositories.base_repository import BaseRepository



class RoleRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(Role, session)


    async def add_role(self, project_id: int,role: dict):
        role = Role(project_id=project_id, **role)
        self.session.add(role)
        await self.session.commit()
        return True


    async def get_roles(self, project_id: int):
        stmt = select(Role).where(Role.project_id == project_id).order_by(desc(Role.priority))
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def update_role_info(self, role_id: int, new_data: Dict[str, Any]):
        old_data_stmt = select(Role).where(Role.id == role_id)
        old_data_res = await self.session.execute(old_data_stmt)
        old_data = old_data_res.scalars().one_or_none()

        stmt = update(Role).where(Role.id == role_id).values(**new_data)
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
        old_data =  res_old_data.scalars().one_or_none()
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
