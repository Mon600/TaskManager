from typing import Dict, Any, Union

from asyncpg import PostgresError
from fastapi import APIRouter, Depends
from fastapi.params import Query
from fastapi_csrf_protect import CsrfProtect
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException
from starlette.requests import Request

from src.shared.dependencies.service_deps import task_service
from src.shared.dependencies.user_deps import current_user, user_role, project_context
from src.shared.schemas.FilterSchemas import TaskFilter
from src.shared.schemas.Task_schemas import TaskSchema, TaskGetSchema, UpdateTaskSchema, BaseTaskSchema, \
    CreateTaskSchema
from src.shared.schemas.pagination import PaginationDep
from src.shared.mongo.db.models import ChangeTaskActionData, CreateTaskActionData, DeleteTaskActionData
from src.shared.ws.socket import sio

router = APIRouter(prefix='/tasks', tags=['Tasks'])


@router.post('/project/{project_id}/create')
async def create_task(project_id: int,
                      project_member: project_context,
                      data: CreateTaskSchema,
                      service: task_service,
                      csrf_protect: CsrfProtect = Depends(),
                      )-> CreateTaskActionData:
    # await csrf_protect.validate_csrf(request)
    if project_member.member.role_rel.create_tasks:
        try:
            action = await service.create_task(data, project_id, project_member.user)
            await sio.emit('update_tasks_list', data=action.created_task, to=f'project_{project_id}')
            return action
        except (SQLAlchemyError, PostgresError) as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=403, detail="No access")


@router.put('/project/{project_id}/update/{task_id}')
async def update_task(
                      project_member: project_context,
                      project_id: int,
                      task_id: int,
                      service: task_service,
                      data: UpdateTaskSchema,
                      csrf_protect: CsrfProtect = Depends()
                      ) -> TaskGetSchema:
    # await csrf_protect.validate_csrf(request)
    if project_member.member.role_rel.update_tasks:
        res = await service.update_task(data, task_id, project_id, project_member.user)
        if res:
            if isinstance(res, BaseTaskSchema):
                await sio.emit('update_tasks_list', data=res, to=f'project_{project_id}')
            return res
        return res
    else:
        raise HTTPException(status_code=403, detail="No access")

@router.delete('/project/{project_id}/delete/{task_id}')
async def delete_task(request: Request,
                      project_member: project_context,
                      project_id: int,
                      task_id: int,
                      service: task_service,
                      csrf_protect: CsrfProtect = Depends()) -> DeleteTaskActionData:
    # await csrf_protect.validate_csrf(request)
    if project_member.member.role_rel.delete_tasks:
        try:
            action = await service.delete_task(task_id, project_id, project_member.user)
            await sio.emit('delete_task', data={'task_id': task_id}, to=f'project_{project_id}')
            return action
        except (SQLAlchemyError, PostgresError) as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=403, detail="No access")



@router.get('/project/{project_id}/get/{task_id}')
async def get_task(user: current_user,
                  project_id: int,
                  task_id:int,
                  service: task_service) -> TaskGetSchema:
    task = await service.get_task(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="Not found")
    return task


@router.get('/project/{project_id}/get-filtered-tasks')
async def get_tasks_with_filter(user: current_user,
                                project_id: int,
                                service: task_service,
                                filters: TaskFilter = Query()) -> list[TaskGetSchema]:
    res = await service.get_filtered_tasks(project_id, filters)
    if res:
        return res
    else:
        raise HTTPException(status_code=404, detail="Not found")


@router.put('/{project_id}/{task_id}/complete')
async def complete_task(request: Request,
                        project_member: project_context,
                        task_id: int,
                        service: task_service) -> BaseTaskSchema:
    try:
        updated_task = await service.change_status_task_to_completed(task_id)
        if updated_task is None:
            raise HTTPException(status_code=404, detail="Задача с таким ID не найдена или уже выполнена.")
        return updated_task
    except (SQLAlchemyError, PostgresError) as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get('/project/{project_id}/tasks')
async def get_tasks(service: task_service,
                    project_id: int,
                    pagination: PaginationDep) -> dict[str, Union[list[TaskGetSchema], int]]:
    try:
        tasks = await service.get_tasks(project_id, pagination.limit, pagination.offset)
        return tasks
    except (SQLAlchemyError, PostgresError) as e:
        raise HTTPException(status_code=500, detail=str(e))
