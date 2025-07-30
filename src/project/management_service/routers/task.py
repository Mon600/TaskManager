from fastapi import APIRouter, Depends, Body
from fastapi_csrf_protect import CsrfProtect
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.shared.db.models import TaskStatus
from src.shared.decorators.decorators import PermissionsChecker
from src.shared.dependencies.service_deps import auth_service, project_service, task_service
from src.shared.dependencies.user_deps import current_user
from src.shared.models.Task_schemas import TaskSchema, TaskSchemaExtend, TaskGetSchema
from src.shared.ws.socket import sio

router = APIRouter(prefix='/tasks', tags=['Tasks'])


@router.post('/project/{project_id}/create')
@PermissionsChecker("create_tasks")
async def create_task(request: Request,
                      user: current_user,
                      auth: auth_service,
                      project: project_service,
                      project_id: int,
                      data: TaskSchema,
                      service: task_service,
                      csrf_protect: CsrfProtect = Depends(),
                      )-> TaskGetSchema:
    await csrf_protect.validate_csrf(request)
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
                      auth: auth_service,
                      project: project_service,
                      project_id: int,
                      task_id: int,
                      service: task_service,
                      data = Body(),
                      csrf_protect: CsrfProtect = Depends()
                      ):
    await csrf_protect.validate_csrf(request)
    res = await service.update_task(data, task_id, project_id)
    if res:
        await sio.emit('update_tasks_list', data=res, to=f'project_{project_id}')
        return JSONResponse(content=res, status_code=200)
    return JSONResponse({"ok": False}, status_code=500)


@router.delete('/project/{project_id}/delete/{task_id}')
@PermissionsChecker("delete_tasks")
async def delete_task(request: Request,
                      user: current_user,
                      auth: auth_service,
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
async def get_task(request: Request,
                      user: current_user,
                      auth: auth_service,
                      project: project_service,
                      project_id: int,
                      task_id:int,
                      service: task_service) -> TaskGetSchema:
    task = await service.get_task(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="Not found")
    return task


@router.put('/{task_id}/complete')
async def set_task_status(request: Request,
                          user: current_user,
                          auth: auth_service,
                          project: project_service,
                          task_id: int,
                          status: TaskStatus,
                          service: task_service):
    updated_task = await service.change_status_task(task_id, status)
    if updated_task:
        return updated_task
    else:
        raise HTTPException(status_code=500, detail='Error')

