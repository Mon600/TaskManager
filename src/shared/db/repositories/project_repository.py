import logging
from tkinter.tix import Select

from sqlalchemy import select, func, update, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.shared.db.models import Project, ProjectMember, Role, Task, TaskAssignee
from src.shared.db.repositories.base_repository import BaseRepository
from src.shared.schemas.Project_schemas import ProjectData


class ProjectRepository(BaseRepository):
    def __init__(self, db: AsyncSession):
        super().__init__(Project, db)
        self.owner_permissions = {
            "create_tasks": True,
            "update_tasks": True,
            "delete_tasks": True,
            "change_roles": True,
            "update_project": True,
            "generate_url": True,
            "delete_users": True,
            "manage_links": True
        }
        self.loger = logging.getLogger(__name__)


    async def new_project(self, data: dict, user_id: int) -> bool:
        project = Project(**data, creator_user_id=user_id)
        self.session.add(project)
        await self.session.flush()
        owner_role = Role(**self.owner_permissions, project_id=project.id, name="Создатель", priority=10)
        self.session.add(owner_role)
        default_role = Role(project_id=project.id, name="Пользователь")
        self.session.add(default_role)
        await self.session.flush()
        project.default_role_id = default_role.id
        self.session.add(project)
        project_member = ProjectMember(
            user_id=user_id,
            project_id=project.id,
            role_id=owner_role.id
        )
        self.session.add(project_member)
        await self.session.commit()
        return project.id



    async def get_projects_by_user_id(self, user_id):
        # selectinload(ProjectMember.user_rel)
        stmt = select(ProjectMember).where(ProjectMember.user_id == user_id).options(
            selectinload(ProjectMember.project_rel)
            )

        member_count_subq = (
            select(
                ProjectMember.project_id,
                func.count(ProjectMember.user_id).label("member_count")
            )
            .group_by(ProjectMember.project_id)
            .subquery()
        )

        stmt = stmt.join(
            member_count_subq,
            ProjectMember.project_id == member_count_subq.c.project_id
        ).add_columns(member_count_subq.c.member_count)
        res = await self.session.execute(stmt)
        return res.all()

    async def get_project_info(self, project_id: int):
        try:
            member_count_subquery = (
                select(func.count(ProjectMember.id))
                .where(ProjectMember.project_id == Project.id)
                .scalar_subquery()
                .label("member_count")
            )

            tasks_count_subquery = (
                select(func.count(Task.id))
                .where(Task.project_id == Project.id)
                .scalar_subquery()
                .label("tasks_count")
            )

            completed_tasks_count_subquery = (
                select(func.count(Task.id))
                .where(
                    Task.project_id == Project.id,
                    Task.status == 'completed'
                )
                .scalar_subquery()
                .label("completed_tasks_count")
            )

            stmt = (
                select(
                    Project,
                    member_count_subquery,
                    tasks_count_subquery,
                    completed_tasks_count_subquery
                )
                .where(Project.id == project_id)
                .options(
                    joinedload(Project.creator_rel))

                    )
            result = await self.session.execute(stmt)
            res = result.one_or_none()

            if not res:
                return None
            project = res[0]
            project.member_count = res[1]
            project.tasks_count = res[2]
            project.completed_tasks_count = res[3]

            return {
                "project": project,
                "members_count": project.member_count,
                "tasks_count": project.tasks_count,
                "completed_tasks_count": project.completed_tasks_count
            }
        except Exception as e:
            self.loger.warn(f"Error in get_project_info: {e}")
            await self.session.rollback()
            return None


    async def update_project(self, project_id: int, new_data: dict):
        old_data_stmt = (select(Project)
                         .where(Project.id == project_id)
                         )
        old_data = await self.session.execute(old_data_stmt)
        old_data_res = old_data.scalars().one_or_none()
        old_data_dict = ProjectData.model_validate(old_data_res).model_dump()
        if old_data_dict == new_data:
            raise ValueError('Old data and new data the same')
        stmt = (update(Project)
                .where(Project.id == project_id)
                .values(**new_data)
                )
        await self.session.execute(stmt)
        await self.session.commit()
        return old_data_dict


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

    async def change_default_role(self, project_id: int, role_id: int):
        old_role_id_stmt = (select(Project.default_role_id)
                         .where(Project.id == project_id)
                        )

        res = await self.session.execute(old_role_id_stmt)
        old_role_id = res.scalars().one()
        if old_role_id == role_id:
            raise ValueError("This role already is default in project.")
        roles_stmt = select(Role).where(or_(Role.id == role_id, Role.id == old_role_id))

        res = await self.session.execute(roles_stmt)
        roles = list(res.scalars().all())


        stmt = (update(Project)
                .where(Project.id == project_id)
                .values(default_role_id = role_id)
                .returning()
                )

        await self.session.execute(stmt)
        await self.session.commit()
        return roles






