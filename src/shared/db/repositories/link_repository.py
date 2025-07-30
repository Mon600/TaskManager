import datetime

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.shared.db.models import ProjectLink, User
from src.shared.db.repositories.base_repository import BaseRepository



class LinkRepository(BaseRepository):
    def __init__(self, db: AsyncSession):
        super().__init__(ProjectLink, db)


    async def get_by_code(self, code: str):
        stmt = select(ProjectLink).where(ProjectLink.link == code).options(
            selectinload(ProjectLink.project_rel)
        )
        res = await self.session.execute(stmt)
        return res.scalars().one()


    async def get_by_project_id(self, project_id: int, nowdate: datetime.datetime):
       stmt = select(ProjectLink).where(
                                        ProjectLink.project_id == project_id ,
                                                    ((ProjectLink.end_at > nowdate) | (ProjectLink.end_at == None))
                                        ).options(
                                            selectinload(ProjectLink.creator_rel).load_only(User.id, User.username)
                                                 )
       res = await self.session.execute(stmt)
       return res.scalars().all()

    async def delete_all_links(self, project_id):
        stmt = delete(ProjectLink).where(ProjectLink.project_id == project_id)
        await self.session.execute(stmt)
        await self.session.commit()
        return True

    async def delete_by_code(self, link_code: str):
        stmt = delete(ProjectLink).where(ProjectLink.link == link_code).returning(ProjectLink.project_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalars().one()
