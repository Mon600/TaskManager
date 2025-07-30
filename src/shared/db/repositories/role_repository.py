from sqlalchemy import select, desc, update
from sqlalchemy.ext.asyncio import AsyncSession

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


    async def update_role(self, member_id: int, project_id: int, role_id: int) -> bool:
        try:
            query = (update(ProjectMember)
                     .where(
                            ProjectMember.project_id == project_id,
                            ProjectMember.id == member_id)
                     .values(role_id = role_id))
            await self.session.execute(query)
            await self.session.commit()
            return True
        except Exception as e :
            print(e)
            await self.session.rollback()
            return False