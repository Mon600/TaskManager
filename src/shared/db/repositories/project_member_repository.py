from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.shared.db.models import ProjectMember, Role
from src.shared.db.repositories.base_repository import BaseRepository


class ProjectMemberRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(ProjectMember, session)

    async def get_members(self, project_id: int):
        stmt = (select(ProjectMember)
                .where(ProjectMember.project_id == project_id)
                .options(
                        selectinload(ProjectMember.user_rel),
                        selectinload(ProjectMember.role_rel)
                        )
                )
        res = await self.session.execute(stmt)
        return res.scalars().all()

    #
    # async def get_project_member(self, user_id: int, project_id: int):
    #     try:
    #         stmt = (select(ProjectMember).where(
    #             ProjectMember.user_id == user_id,
    #             ProjectMember.project_id == project_id)
    #         .options(
    #             selectinload(ProjectMember.role_rel)
    #             )
    #         )
    #         data = await self.session.execute(stmt)
    #         return data.scalars().one_or_none()
    #     except Exception as e:
    #         await self.session.rollback()
    #         return None


    async def get_member_by_user_id(self, project_id: int, user_id: int):
        stmt = select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).options(
            selectinload(ProjectMember.role_rel)
        )
        res = await self.session.execute(stmt)
        return res.scalars().one_or_none()


    async def add_member(self, data: dict):
        if data['role_id'] is None:
            new_role = Role(name="Пользователь", project_id=data['project_id'])
            self.session.add(new_role)
            await self.session.flush()
            data['role_id'] = new_role.id
        new_member = ProjectMember(**data)
        self.session.add(new_member)
        await self.session.commit()


    async def delete_member(self, project_id: int, member_id: int):
        old_member_stmt = (select(ProjectMember)
                           .where(
                    ProjectMember.project_id == project_id,
                                ProjectMember.id == member_id
                                    )
                            .options(
                        selectinload(ProjectMember.user_rel),
                                selectinload(ProjectMember.role_rel)
                                    )
                            )
        res = await self.session.execute(old_member_stmt)
        deleted_user = res.scalars().one()

        stmt = (delete(ProjectMember)
                .where(
        ProjectMember.project_id == project_id,
                   ProjectMember.id == member_id
                        )
                )
        await self.session.execute(stmt)
        return deleted_user

