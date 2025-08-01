
from sqlalchemy import select, update, delete, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.shared.db.models import Task, TaskAssignee, ProjectMember
from src.shared.db.repositories.base_repository import BaseRepository
from src.shared.models.FilterSchemas import TaskFilter, SortField, SortDirection


class TaskRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(Task, session)


    async def create_task(self, task_data: dict, assignees: list):
        try:
            new_task = Task(**task_data)
            self.session.add(new_task)
            await self.session.flush()
            new_assignees = [
                TaskAssignee(**{
                    "task_id": new_task.id,
                    "project_member_id": member_id
                })
                for member_id in assignees
            ]
            self.session.add_all(new_assignees)
            await self.session.commit()
            return new_task.id
        except Exception as e:
            print(f'Ошибка добавления записи в базу данных {e}')
            return False

    async def get_tasks(self , project_id):
        stmt = (select(Task).where(Task.project_id == project_id, Task.status == 'processing').options(selectinload(Task.assignees_rel)
                                                                          .load_only(TaskAssignee.project_member_id)
                                                                          .selectinload(TaskAssignee.project_member_rel)
                                                                                   .selectinload(ProjectMember.user_rel)))
        result = await self.session.execute(stmt)
        all_tasks = result.scalars().all()
        return all_tasks

    async def get_filtered_tasks(self, project_id: int, filters: TaskFilter):
        sorted_fields = {
            SortField.STATUS: Task.status,
            SortField.DEADLINE: Task.deadline,
            SortField.PRIORITY: Task.priority,
            SortField.CREATED: Task.started_at,
        }
        stmt = select(Task).where(Task.project_id == project_id)

        if not filters.status is None:
            stmt = stmt.where(Task.status.in_(filters.status))
        if filters.priority:
            stmt = stmt.where(Task.priority.in_(filters.priority))
        if filters.deadline_after:
            stmt = stmt.where(Task.deadline >= filters.deadline_after)
        if filters.deadline_before:
            stmt = stmt.where(Task.deadline <= filters.deadline_before)
        if filters.created_after:
            stmt = stmt.where(Task.started_at >= filters.created_after)
        if filters.created_before:
            stmt = stmt.where(Task.started_at <= filters.created_before)
        if filters.sort_by:
            if filters.sort_dir == SortDirection.ASC:
                stmt = stmt.order_by(asc(sorted_fields[filters.sort_by]))
            stmt = stmt.order_by(desc(sorted_fields[filters.sort_by]))
        stmt = stmt.options(
                            selectinload(Task.assignees_rel)
                            .load_only(TaskAssignee.project_member_id)
                            .selectinload(TaskAssignee.project_member_rel)
                            .selectinload(ProjectMember.user_rel)
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()




    async def get_task(self, task_id:int):
        stmt = (select(Task)
                .where(Task.id == task_id)
                .options(
                        selectinload(Task.assignees_rel)
                        .load_only(TaskAssignee.project_member_id)
                        .selectinload(TaskAssignee.project_member_rel)
                        .selectinload(ProjectMember.user_rel)
                        )
                )
        task = await self.session.execute(stmt)
        return task.scalars().one_or_none()

    async def update_assignees(self,task_id, assignees: list, project_id: int):
        if assignees:
            member_check_stmt = select(ProjectMember.id).where(
                ProjectMember.id.in_(assignees),
                ProjectMember.project_id == project_id
            )
            result = await self.session.execute(member_check_stmt)
            existing_members = {row[0] for row in result.fetchall()}
            invalid_members = set(assignees) - existing_members
            if invalid_members:
                raise ValueError(f"Users {list(invalid_members)} are not members of this project")
        assignees_stmt = select(TaskAssignee.project_member_id).where(TaskAssignee.task_id == task_id)
        res = await self.session.execute(assignees_stmt)
        current_assignees = list(res.scalars().all())
        data_to_add = set(assignees) - set(current_assignees)
        data_to_delete =  list(set(current_assignees) - set(assignees))
        if data_to_delete:
            delete_stmt = (delete(TaskAssignee)
                           .where(
                                  TaskAssignee.task_id == task_id,
                                  TaskAssignee.project_member_id.in_(data_to_delete)
                                  )
                           )
            await self.session.execute(delete_stmt)
        if data_to_add:
            assignees_list = [TaskAssignee(task_id=task_id, project_member_id=member_id) for member_id in data_to_add]
            self.session.add_all(assignees_list)
        await self.session.commit()
        final_assignees_stmt = (
            select(TaskAssignee)
            .where(TaskAssignee.task_id == task_id)
            .options(
                selectinload(TaskAssignee.project_member_rel)
                .selectinload(ProjectMember.user_rel)
            )
        )
        final_res = await self.session.execute(final_assignees_stmt)
        task_assignees = final_res.scalars().all()
        return task_assignees



    async def update_task(self,task_id):
        stmt = (update(Task)
                .where(Task.id == task_id)
                .values(status = 'completed')
                .returning(Task.id,
                           Task.project_id,
                           Task.name,
                           Task.description,
                           Task.deadline,
                           Task.started_at,
                           Task.completed_at,
                           Task.priority,
                           Task.is_ended,
                           Task.status)
                )

        res = await self.session.execute(stmt)
        await self.session.commit()
        return list(res.first())
