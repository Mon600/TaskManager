import datetime
from typing import Dict, Any

from sqlalchemy import select, update, delete, asc, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.shared.db.models import Task, TaskAssignee, ProjectMember
from src.shared.db.repositories.base_repository import BaseRepository
from src.shared.schemas.Assigneed_schemas import AssigneesModel
from src.shared.schemas.FilterSchemas import TaskFilter, SortField, SortDirection
from src.shared.schemas.Task_schemas import EditableTaskData, TaskGetSchema, BaseTaskSchema, CreateTaskSchema


class TaskRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(Task, session)


    async def create_task(self,
                          task_data: dict,
                          assignees: list[int],
                          project_id: int) -> int:

            new_task = Task(**task_data, project_id=project_id)
            self.session.add(new_task)
            await self.session.commit()
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


    async def get_tasks(self , project_id: int, limit: int = 20, offset: int = 0):


        stmt = (select(Task)
                .where(Task.project_id == project_id)#, Task.status == 'processing')
                .options(
            selectinload(Task.assignees_rel)
            .load_only(TaskAssignee.project_member_id)
            .selectinload(TaskAssignee.project_member_rel)
            .selectinload(ProjectMember.user_rel)
        )
                .offset(offset)
                .limit(limit)
        )

        tasks_db = await self.session.execute(stmt)
        all_tasks = tasks_db.scalars().all()

        count_stmt = (
            select(
                func.count(Task.id).label("total_count"),
                func.count(Task.id).filter(Task.status == 'completed').label("completed_count")
            )
            .where(Task.project_id == project_id)
        )

        count_db = await self.session.execute(count_stmt)
        counters = count_db.first()
        print(counters)
        return {
            'tasks': all_tasks,
            'total_tasks_count': counters[0],
            'completed_tasks_count': counters[1]
        }

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


    async def get_task(self, task_id:int) -> TaskGetSchema:
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
        task_db =  task.scalars().one_or_none()
        task_schema = TaskGetSchema.model_validate(task_db)
        return task_schema


    async def update_assignees(self,task_id, assignees: list, project_id: int) -> Dict[str, list[AssigneesModel]]:
        if assignees:
            member_check_stmt = select(ProjectMember.id).where(
                ProjectMember.id.in_(assignees),
                ProjectMember.project_id == project_id
            )
            result = await self.session.scalars(member_check_stmt)
            existing_members = set(result.all())

            invalid_members = set(assignees) - existing_members
            if invalid_members:
                raise ValueError(f"Users {list(invalid_members)} are not members of this project")

        assignees_stmt = select(TaskAssignee).where(TaskAssignee.task_id == task_id).options(
                selectinload(TaskAssignee.project_member_rel)
                .selectinload(ProjectMember.user_rel)
            )
        res = await self.session.execute(assignees_stmt)
        old_assignees_db = res.scalars().all()
        old_assignees = [AssigneesModel.model_validate(assignee) for assignee in old_assignees_db]
        current_assignees_ids = set(assignee.project_member_id for assignee in old_assignees_db)
        data_to_add = set(assignees) - current_assignees_ids
        data_to_delete =  list(current_assignees_ids - set(assignees))

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
        task_assignees_db = final_res.scalars().all()
        task_assignees = [AssigneesModel.model_validate(assignee) for assignee in task_assignees_db]
        return {
            'new_assignees': task_assignees,
            'old_assignees': old_assignees
        }


    async def update_task(self, task_id, data: Dict[str, Any]) -> Dict[str, BaseTaskSchema]:
        old_task_stmt = select(Task
        ).where(Task.id == task_id)
        old_task_res = await self.session.execute(old_task_stmt)
        old_task = old_task_res.scalars().first()
        old_data_schema = BaseTaskSchema.model_validate(old_task)
        stmt = (update(Task)
                .where(Task.id == task_id)
                .values(**data)
                .returning(Task)
                )

        res = await self.session.execute(stmt)
        new_data = res.scalars().first()
        new_data_schema = BaseTaskSchema.model_validate(new_data)
        await self.session.commit()
        return {
            'new_task_data': old_data_schema,
            'old_task_data': new_data_schema
        }


    async def complete_task(self, task_id: int, current_date: datetime.date) -> TaskGetSchema:
        stmt = (update(Task)
                .where(Task.id == task_id, Task.status != 'completed')
                .values(
                    status='completed',
                    completed_at=current_date
                        )
                .returning(Task)
                )
        res = await self.session.execute(stmt)
        await self.session.commit()
        task_db = res.scalars().one_or_none()
        task_schema = TaskGetSchema.model_validate(task_db)
        return task_schema

    async def delete_task(self, task_id: int) -> TaskGetSchema:
        stmt = (
            delete(Task)
            .where(Task.id == task_id)
            .returning(Task)
                )
        result = await self.session.execute(stmt)
        task_db = result.scalars().one()
        task_schema = TaskGetSchema.model_validate(task_db)
        return task_schema


