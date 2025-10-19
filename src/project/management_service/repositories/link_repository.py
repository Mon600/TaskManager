import datetime

from sqlalchemy import select, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.shared.db.models import ProjectLink, User
from src.shared.db.repositories.base_repository import BaseRepository
from src.shared.schemas.Link_schemas import LinkSchemaExtend


class LinkRepository(BaseRepository):
    def __init__(self, db: AsyncSession):
        super().__init__(ProjectLink, db)

    async def get_by_code(self, code: str, current_date: datetime.datetime):
        stmt = (select(ProjectLink)
        .where(
            ProjectLink.link == code,
            or_(
                ProjectLink.end_at > current_date,
                ProjectLink.end_at == None
            ))
            .options(
                selectinload(ProjectLink.project_rel)
            )
        )
        res = await self.session.execute(stmt)
        return res.scalars().one_or_none()

    async def get_by_project_id(self, project_id: int, nowdate: datetime.datetime):
        stmt = select(ProjectLink).where(
            ProjectLink.project_id == project_id,
            ((ProjectLink.end_at > nowdate) | (ProjectLink.end_at == None))
        ).options(
            selectinload(ProjectLink.creator_rel).load_only(User.id, User.username)
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def delete_all_links(self, project_id) -> list[LinkSchemaExtend]:
        stmt = delete(ProjectLink).where(ProjectLink.project_id == project_id).returning(ProjectLink)
        res = await self.session.execute(stmt)
        links_db = res.scalars().all()
        links_schema = [LinkSchemaExtend.model_validate(link) for link in links_db]
        await self.session.commit()
        return links_schema

    async def delete_by_code(self, link_code: str, project_id: int) -> LinkSchemaExtend:
        stmt = (delete(ProjectLink)
                .where(
            ProjectLink.link == link_code,
            ProjectLink.project_id == project_id
        )
                .returning(ProjectLink)
                )
        result = await self.session.execute(stmt)
        await self.session.commit()
        link_db = result.scalars().one()
        link_schema = LinkSchemaExtend.model_validate(link_db)
        return link_schema
