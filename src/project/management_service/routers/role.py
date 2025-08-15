from asyncpg import PostgresError
from fastapi import APIRouter, Depends, HTTPException
from fastapi_csrf_protect import CsrfProtect
from sqlalchemy.exc import SQLAlchemyError
from starlette.requests import Request
from starlette.responses import JSONResponse


from src.shared.dependencies.service_deps import role_service, get_project_service
from src.shared.dependencies.user_deps import current_user, user_role
from src.shared.schemas.Role_schemas import RoleSchema, RoleSchemaWithId

router = APIRouter(prefix='/roles', tags=['Roles'])


@router.get('/project/{project_id}')

async def get_roles(user: current_user,
                   project_id: int,
                   service: role_service) -> list[RoleSchemaWithId]:
    try:
        res = await service.get_roles(project_id)
        return res
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=e)


@router.post("/project/{project_id}/new")
async def add_role(user: current_user,
                   project_id: int,
                   service: role_service,
                   data: RoleSchema,
                   csrf_protect: CsrfProtect = Depends()):
    try:
        # await csrf_protect.validate_csrf(request)
        await service.new_role(project_id, data)
        return {"ok": True}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=e)


@router.put("/project/{project_id}/role/{role_id}/update")
async def update_role(request: Request,
                      user: current_user,
                      project_id: int,
                      role: user_role,
                      data: RoleSchema,
                      role_id: int,
                      service: role_service,
                      csrf_protect: CsrfProtect = Depends()):
    try:
        # await csrf_protect.validate_csrf(request)
        res = await service.role_update(role_id, data, user, project_id)
        return res
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))




@router.delete("/project/{project_id}/role/{role_id}/delete")
async def delete_role(request: Request,
                      user: current_user,
                      project_id: int,
                      role: user_role,
                      role_id: int,
                      service: role_service,
                      csrf_protect: CsrfProtect = Depends()):
    await csrf_protect.validate_csrf(request)
    if role.change_roles:
        try:
            await service.role_delete(role_id)
        except (SQLAlchemyError, PostgresError) as e:
            raise HTTPException(status_code=500, detail=e)
    else:
        raise HTTPException(status_code=403, detail='No access')


@router.put("/{project_id}/member/{member_id}/update-role/{role_id}")

async def change_role(request: Request,
                      user: current_user,
                      role: user_role,
                      project_id: int,
                      member_id: int,
                      role_id: int,
                      service: role_service,
                      csrf_protect: CsrfProtect = Depends()
                      ):
    # await csrf_protect.validate_csrf(request)
    if role.change_roles:
        try:
            res = await service.new_member_role(member_id, project_id, role_id, user)
            return res
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=403, detail='No access')
