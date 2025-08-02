from fastapi import APIRouter, Depends, HTTPException
from fastapi_csrf_protect import CsrfProtect
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.shared.decorators.decorators import PermissionsChecker
from src.shared.dependencies.service_deps import auth_service, project_service, role_service
from src.shared.dependencies.user_deps import current_user
from src.shared.models.Role_schemas import RoleSchema, RoleSchemaWithId

router = APIRouter(prefix='/roles', tags=['Roles'])


@router.get('/project/{project_id}')
@PermissionsChecker("change_roles")
async def get_roles(user: current_user,
                   project: project_service,
                   project_id: int,
                   service: role_service) -> list[RoleSchemaWithId]:
    res = await service.get_roles(project_id)
    if res is None:
        raise HTTPException(status_code=500, detail='Ошибка')
    return res



@router.post("/project/{project_id}/new")
@PermissionsChecker("change_roles")
async def add_role(user: current_user,
                   project: project_service,
                   project_id: int,
                   service: role_service,
                   data: RoleSchema,
                   csrf_protect: CsrfProtect = Depends()):
    try:
        # await csrf_protect.validate_csrf(request)
        await service.new_role(project_id, data)
        return JSONResponse({"ok": True}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)


@router.put("/project/{project_id}/role/{role_id}/update")
@PermissionsChecker("change_roles")
async def update_role(request: Request,
                      user: current_user,
                      project: project_service,
                      project_id: int,
                      data: RoleSchema,
                      role_id: int,
                      service: role_service,
                      csrf_protect: CsrfProtect = Depends()):
    try:
        await csrf_protect.validate_csrf(request)
        await service.role_update(role_id, data, user, project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)



@router.delete("/project/{project_id}/role/{role_id}/delete")
@PermissionsChecker("change_roles")
async def delete_role(request: Request,
                      user: current_user,
                      project: project_service,
                      project_id: int,
                      role_id: int,
                      service: role_service,
                      csrf_protect: CsrfProtect = Depends()):
    try:
        await csrf_protect.validate_csrf(request)
        await service.role_delete(role_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)


@router.put("/{project_id}/member/{member_id}/update-role/{role_id}")
@PermissionsChecker("change_roles")
async def change_role(request: Request,
                      user: current_user,
                      project: project_service,
                      project_id: int,
                      member_id: int,
                      role_id: int,
                      service: role_service,
                      csrf_protect: CsrfProtect = Depends()
                      ):
    # await csrf_protect.validate_csrf(request)
    res =  await service.new_member_role(member_id, project_id, role_id, user)
    if res:
        return res
    return None
