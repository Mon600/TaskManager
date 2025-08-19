from asyncpg import PostgresError
from fastapi import APIRouter, Depends, HTTPException
from fastapi_csrf_protect import CsrfProtect
from sqlalchemy.exc import SQLAlchemyError
from starlette.requests import Request
from starlette.responses import JSONResponse


from src.shared.dependencies.service_deps import role_service, get_project_service
from src.shared.dependencies.user_deps import current_user, project_context
from src.shared.mongo.db.models import EditRoleActionData, CreateRoleActionData
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
async def add_role(context: project_context,
                   project_id: int,
                   service: role_service,
                   data: RoleSchema,
                   csrf_protect: CsrfProtect = Depends()) -> CreateRoleActionData:
    if not context:
        raise HTTPException(401, 'Not authorized')
    if not context.member.role_rel.change_roles: #сделать create_role!!!
        raise HTTPException(403, 'No access')
    try:
        # await csrf_protect.validate_csrf(request)
        action = await service.new_role(project_id, context.user, data)
        return action
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=e)


@router.put("/project/{project_id}/role/{role_id}/update")
async def update_role(context: project_context,
                      project_id: int,
                      data: RoleSchema,
                      role_id: int,
                      service: role_service,
                      csrf_protect: CsrfProtect = Depends()) -> EditRoleActionData:
    if not context:
        raise HTTPException(401, 'Not authorized')
    try:
        # await csrf_protect.validate_csrf(request)
        if context.member.role_rel.change_roles:
            action = await service.role_update(role_id, data, context.user, project_id)
            return action
        else:
            raise HTTPException(status_code=403, detail="No access")
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))




@router.delete("/project/{project_id}/role/{role_id}/delete")
async def delete_role(request: Request,
                      project_id: int,
                      project_member: project_context,
                      role_id: int,
                      service: role_service,
                      csrf_protect: CsrfProtect = Depends()):
    # await csrf_protect.validate_csrf(request)
    if project_member.member.role_rel.change_roles:
        try:
            result = await service.role_delete(role_id, project_id, project_member.user)
            return result
        except (SQLAlchemyError, PostgresError) as e:
            raise HTTPException(status_code=500, detail=e)
    else:
        raise HTTPException(status_code=403, detail='No access')


@router.put("/{project_id}/member/{member_id}/update-role/{role_id}")

async def change_member_role(request: Request,
                      project_member: project_context,
                      project_id: int,
                      member_id: int,
                      role_id: int,
                      service: role_service,
                      csrf_protect: CsrfProtect = Depends()
                      ):
    # await csrf_protect.validate_csrf(request)
    if project_member.member.role_rel.change_roles:
        try:
            res = await service.new_member_role(member_id, project_id, role_id, project_member.user)
            return res
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=403, detail='No access')
