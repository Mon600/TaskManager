from pymongo.asynchronous.database import AsyncDatabase

from src.shared.db.models import TaskStatus
from src.shared.db.repositories.task_repository import TaskRepository
from src.shared.models.Assigneed_schemas import AssigneesModel
from src.shared.models.Task_schemas import TaskGetSchema, BaseTaskSchema, TaskSchema


class TaskService:
    def __init__(self, repository: TaskRepository):
        self.repository = repository


    async def get_tasks(self, project_id: int) -> list[TaskGetSchema]:
        all_tasks = await self.repository.get_tasks(project_id)
        res = [TaskGetSchema.model_validate(task).model_dump() for task in all_tasks]
        return res


    async def create_task(self, data: TaskSchema) -> TaskGetSchema | bool:
        task = data.model_dump()
        assignees = task.pop('assignees')
        res = await self.repository.create_task(task, assignees)
        if res:
            returning_data = await self.repository.get_task(res)
            return returning_data
        return False


    async def update_task(self, data: TaskSchema,task_id: int,  project_id: int):
        task = data.model_dump()
        assignees = task.pop('assignees')
        try:
            updated_assignees = await self.repository.update_assignees(task_id, assignees, project_id)
            updated_assignees_schema = [AssigneesModel.model_validate(assignee) for assignee in updated_assignees]
            if updated_assignees:
                updated_task = await self.repository.update_task(task_id, task)
                updated_task.append(updated_assignees_schema)
                task_keys = [
                    'id', 'project_id', 'name', 'description',
                    'deadline', 'started_at', 'completed_at', 'priority',
                    'is_ended', 'status', 'assignees_rel']
                task_dict = dict(zip(task_keys, updated_task))
                returning_data = TaskGetSchema.model_validate(task_dict)
                return returning_data.model_dump()
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


    async def change_status_task(self, task_id, status: TaskStatus):
        try:
            res = await self.repository.update_task(task_id, {"status": status})
            if res:
                return BaseTaskSchema.model_validate(res)
            else:
                return None
        except Exception as e:
            print(f"Ошибка {e}")
            return False


