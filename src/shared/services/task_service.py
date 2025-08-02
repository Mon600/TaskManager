import datetime
from typing import Dict, Any

from pymongo.asynchronous.database import AsyncDatabase

from src.shared.db.models import TaskStatus, TaskPriority
from src.shared.db.repositories.task_repository import TaskRepository
from src.shared.models.Assigneed_schemas import AssigneesModel
from src.shared.models.FilterSchemas import TaskFilter
from src.shared.models.Task_schemas import TaskGetSchema, BaseTaskSchema, TaskSchema, UpdateTaskSchema
from src.shared.mongo.db.models import ChangeTaskActionData
from src.shared.mongo.repositories.mongo_repositroy import MongoRepository


class TaskService:
    def __init__(self, repository: TaskRepository, mongo: MongoRepository):
        self.repository = repository
        self.mongo = mongo

    @staticmethod
    async def format_task_data(data, assignees: list[AssigneesModel]):

        task_keys = [
            'id', 'project_id', 'name', 'description',
            'deadline', 'started_at', 'completed_at', 'priority',
            'is_ended', 'status']
        if len(task_keys) == len(data):
            task_dict = dict(zip(task_keys, data))
            task_dict['assignees_rel'] = assignees
            return TaskGetSchema.model_validate(task_dict).model_dump()
        else:
            return None


    async def get_tasks(self, project_id: int, limit: int = 20, offset: int = 0) -> list[TaskGetSchema]:
        all_tasks = await self.repository.get_tasks(project_id, limit, offset)
        res = [TaskGetSchema.model_validate(task).model_dump() for task in all_tasks]
        return res

    async def get_filtered_tasks(self,
                                 project_id: int,
                                 filters: TaskFilter):
        tasks = await self.repository.get_filtered_tasks(project_id, filters)
        res = [TaskGetSchema.model_validate(task).model_dump() for task in tasks]
        return res



    async def create_task(self, data: TaskSchema) -> TaskGetSchema | bool:
        task = data.model_dump()
        assignees = task.pop('assignees')
        res = await self.repository.create_task(task, assignees)
        if res:
            returning_data = await self.repository.get_task(res)
            return returning_data
        return False


    async def update_task(self, data: UpdateTaskSchema, task_id: int,  project_id: int, user: Dict[str, Any]):
        task = data.model_dump()
        new_assignees = task.pop('assignees')

        try:
            assignees = await self.repository.update_assignees(task_id, new_assignees, project_id)
            new_assignees_schema = [AssigneesModel.model_validate(assignee) for assignee in assignees['new_assignees']]
            old_assignees_schema = [AssigneesModel.model_validate(assignee) for assignee in assignees['old_assignees']]

            if assignees:
                tasks = await self.repository.update_task(task_id, task)
                new_task = tasks['new_task_data']
                old_task = tasks['old_task_data']

                new_task_dict = await self.format_task_data(new_task, new_assignees_schema)
                old_task_dict = await self.format_task_data(old_task, old_assignees_schema)
                if new_task_dict and old_task_dict:
                    action = ChangeTaskActionData(new_data=new_task_dict, old_data=old_task_dict)
                    await self.mongo.add_to_db(action, project_id, user)

                    return action
            return None
        except Exception as e:
            print("Ошибка:", e)
            return False


    async def delete_task(self, task_id) -> bool:
        try:
            res = await self.repository.delete_by_id(task_id)
            return res
        except Exception as e:
            print(f"Ошибка: {e}")
            return False


    async def change_status_task(self, task_id):
        try:
            res = await self.repository.update_task(task_id)
            if res:
                keys = ['id',
                        'project_id',
                        'name',
                        'description',
                        'deadline',
                        'started_at',
                        'completed_at',
                        'priority',
                        'is_ended',
                        'status']
                result = dict(zip(keys, res))
                print(result)
                return BaseTaskSchema.model_validate(result)
            else:
                return None
        except Exception as e:
            print(f"Ошибка {e}")
            return False


