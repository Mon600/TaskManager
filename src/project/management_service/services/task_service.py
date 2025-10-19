import datetime
import logging
from typing import Dict, Any

from asyncpg import PostgresError
from sqlalchemy.exc import SQLAlchemyError

from src.project.management_service.repositories.task_repository import TaskRepository
from src.project.management_service.mongo.db.models import ChangeTaskActionData, CompleteTaskActionData, CreateTaskActionData, \
    DeleteTaskActionData
from src.shared.schemas.FilterSchemas import TaskFilter
from src.shared.schemas.Task_schemas import TaskGetSchema, UpdateTaskSchema, \
    CreateTaskSchema
from src.shared.schemas.User_schema import UserSchema
from src.project.management_service.services.audit_service import AuditService


class TaskService:
    def __init__(self, repository: TaskRepository, service: AuditService):
        self.repository = repository
        self.audit = service

        self.logger = logging.getLogger(__name__)

    async def get_tasks(self, project_id: int, limit: int = 20, offset: int = 0) -> Dict[str, Any] | None:
        try:
            data_db = await self.repository.get_tasks(project_id, limit, offset)
            tasks = data_db['tasks']
            tasks_count = data_db['total_tasks_count']
            completed_tasks_count = data_db['completed_tasks_count']
            return {'tasks': tasks,
                    'tasks_count': tasks_count,
                    "completed_tasks_count": completed_tasks_count}
        except (SQLAlchemyError, PostgresError) as e:
            self.logger.warning(f'Ошибка {e}')
            raise e

    async def get_filtered_tasks(self,
                                 project_id: int,
                                 filters: TaskFilter):
        try:
            tasks = await self.repository.get_filtered_tasks(project_id, filters)
            return tasks
        except (SQLAlchemyError, PostgresError) as e:
            self.logger.warning(f'Ошибка {e}')
            raise e

    async def create_task(self, task_data: CreateTaskSchema, project_id: int, user: UserSchema) -> CreateTaskActionData:
        task = task_data.model_dump()
        assignees: list[int] = task.pop('assignees')
        try:
            task_id = await self.repository.create_task(task, assignees, project_id)

            task = await self.repository.get_task(task_id, project_id)
            data = CreateTaskActionData(created_task=task)
            await self.audit.log(project_id, user, data)
            return data
        except (SQLAlchemyError, PostgresError) as e:
            self.logger.warning(f'Ошибка {e}')
            raise e

    async def update_task(self,
                          data: UpdateTaskSchema,
                          task_id: int, project_id: int,
                          user: UserSchema) -> ChangeTaskActionData:
        task = data.model_dump()
        new_assignees = task.pop('assignees')

        try:
            assignees = await self.repository.update_assignees(task_id, new_assignees, project_id)
            new_assignees_schema = assignees['new_assignees']
            old_assignees_schema = assignees['old_assignees']
            tasks = await self.repository.update_task(task_id, task)

            new_task = tasks['new_task_data']
            old_task = tasks['old_task_data']
            if not (old_task or new_task):
                raise KeyError("No tasks with received parameters")
            new_task_result_schema = TaskGetSchema(
                **new_task.model_dump(),
                assignees_rel=new_assignees_schema
            )
            old_task_result_schema = TaskGetSchema(
                **old_task.model_dump(),
                assignees_rel=old_assignees_schema
            )

            if new_task == old_task:
                raise ValueError('Old data and new data the same')
            data = ChangeTaskActionData.model_validate({
                "new_data": new_task_result_schema,
                "old_data": old_task_result_schema
            })
            await self.audit.log(project_id, user, data)
            return data
        except ValueError as e:
            self.logger.warning(f"Ошибка: {e}")
            raise e
        except (SQLAlchemyError, PostgresError) as e:
            self.logger.warning(f"Ошибка: {e}")
            raise e

    async def delete_task(self, task_id: int, project_id: int, user: UserSchema) -> DeleteTaskActionData:
        try:
            deleted_task = await self.repository.delete_task(task_id)
            data = DeleteTaskActionData(deleted_task=deleted_task)
            await self.audit.log(project_id, user, data)
            return data
        except (SQLAlchemyError, PostgresError) as e:
            self.logger.warning(f"Ошибка: {e}")
            raise e

    async def change_status_task_to_completed(self,
                                              task_id: int,
                                              project_id: int,
                                              user: UserSchema) -> CompleteTaskActionData:
        try:
            completed_at = datetime.date.today()
            completed_task = await self.repository.complete_task(task_id, completed_at)
            data = CompleteTaskActionData(completed_task=completed_task)
            await self.audit.log(project_id, user, data)
            return data
        except KeyError as e:
            self.logger.warning(f"Ошибка: {str(e)}")
            raise e
        except (SQLAlchemyError, PostgresError) as e:
            self.logger.warning(f"Ошибка: {e}")
            raise e

    async def get_task(self, task_id: int, project_id: int) -> TaskGetSchema:
        try:
            task = await self.repository.get_task(task_id, project_id)
            return task
        except KeyError as  e:
            self.logger.warning(f"Ошибка: {e}")
            raise e
        except (SQLAlchemyError, PostgresError) as e:
            self.logger.warning(f"Ошибка {e}")
            raise e
