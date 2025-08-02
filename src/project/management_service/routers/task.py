from fastapi import APIRouter, Depends, Body
from fastapi.params import Query
from fastapi_csrf_protect import CsrfProtect
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.shared.decorators.decorators import PermissionsChecker
from src.shared.dependencies.service_deps import auth_service, project_service, task_service
from src.shared.dependencies.user_deps import current_user
from src.shared.models.FilterSchemas import TaskFilter
from src.shared.models.Task_schemas import TaskSchema, TaskGetSchema, UpdateTaskSchema
from src.shared.models.pagination import PaginationDep
from src.shared.mongo.db.models import ChangeTaskActionData
from src.shared.ws.socket import sio

router = APIRouter(prefix='/tasks', tags=['Tasks'])


@router.post('/project/{project_id}/create')
@PermissionsChecker("create_tasks")
async def create_task(user: current_user,
                      project: project_service,
                      project_id: int,
                      data: TaskSchema,
                      service: task_service,
                      csrf_protect: CsrfProtect = Depends(),
                      )-> TaskGetSchema:
    # await csrf_protect.validate_csrf(request)
    res = await service.create_task(data)
    if res:
        await sio.emit('update_tasks_list', data=res, to=f'project_{project_id}')
        return res
    else:
        raise HTTPException(status_code=500, detail='error')


@router.put('/project/{project_id}/update/{task_id}')
@PermissionsChecker("update_tasks")
async def update_task(request: Request,
                      user: current_user,
                      project: project_service,
                      project_id: int,
                      task_id: int,
                      service: task_service,
                      data: UpdateTaskSchema,
                      csrf_protect: CsrfProtect = Depends()
                      ) -> ChangeTaskActionData:
    # await csrf_protect.validate_csrf(request)
    res = await service.update_task(data, task_id, project_id, user)
    if res:
        await sio.emit('update_tasks_list', data=res.new_data, to=f'project_{project_id}')
        return res
    return res


@router.delete('/project/{project_id}/delete/{task_id}')
@PermissionsChecker("delete_tasks")
async def delete_task(request: Request,
                      user: current_user,
                      project: project_service,
                      project_id: int,
                      task_id:int,
                      service: task_service,
                      csrf_protect: CsrfProtect = Depends())-> JSONResponse:
    await csrf_protect.validate_csrf(request)
    res = await service.delete_task(task_id)
    if res:
        await sio.emit('delete_task', data={'task_id': task_id}, to=f'project_{project_id}')
        return JSONResponse({'ok': True}, status_code=204)
    return JSONResponse({"ok": False}, status_code=500)


@router.get('/project/{project_id}/get/{task_id}')
@PermissionsChecker("update_tasks")
async def get_task(user: current_user,
                  project: project_service,
                  project_id: int,
                  task_id:int,
                  service: task_service) -> TaskGetSchema:
    task = await service.get_task(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="Not found")
    return task


async def get_tasks():
    pass

@router.get('/project/{project_id}/get-filtered-tasks')
async def get_tasks_with_filter(user: current_user,
                                project: project_service,
                                project_id: int,
                                service: task_service,
                                filters: TaskFilter = Query()):
    res = await service.get_filtered_tasks(project_id, filters)
    if res:
        return res
    else:
        raise HTTPException(status_code=404, detail="Not found")


@router.put('/{task_id}/complete')
async def set_task_status(request: Request,
                          user: current_user,
                          project: project_service,
                          task_id: int,
                          service: task_service):
    updated_task = await service.change_status_task(task_id)
    if updated_task:
        return updated_task
    else:
        raise HTTPException(status_code=500, detail='Error')


@router.get('/project/{project_id}/tasks')
async def get_tasks(service: task_service, project_id: int, pagination: PaginationDep) -> list[TaskGetSchema]:
    tasks = task_service.get_tasks(project_id, pagination.limit, pagination.offset)
    return tasks
