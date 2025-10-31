from functools import partial

from asyncpg import PostgresError
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from src.project.management_service.mongo.db.models import EditRoleActionData, CreateRoleActionData
from src.shared.dependencies.service_deps import role_service
from src.shared.dependencies.user_deps import current_user, required_rights
from src.shared.schemas.Role_schemas import RoleSchema, RoleSchemaWithId

router = APIRouter(prefix='/roles', tags=['Roles'])


@router.get('/project/{project_id}/roles')
async def get_roles(user: current_user,
                    project_id: int,
                    service: role_service) -> list[RoleSchemaWithId]:
    try:
        res = await service.get_roles(project_id)
        return res
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=e)


@router.post("/project/{project_id}/new")
async def add_role(project_id: int,
                   service: role_service,
                   data: RoleSchema,
                   member=Depends(partial(required_rights, rights=["change_roles"]))) -> CreateRoleActionData:
    try:
        action = await service.new_role(project_id, member.user, data)
        return action
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=e)


@router.put("/project/{project_id}/role/{role_id}/update")
async def update_role(project_id: int,
                      data: RoleSchema,
                      role_id: int,
                      service: role_service,
                      member=Depends(partial(required_rights, rights=["change_roles"]))) -> EditRoleActionData:
    try:
        action = await service.role_update(role_id, data, member.user, project_id)
        return action
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/project/{project_id}/role/{role_id}/delete")
async def delete_role(project_id: int,
                      role_id: int,
                      service: role_service,
                      member=Depends(partial(required_rights, rights=['change_roles']))):
    try:
        result = await service.role_delete(role_id, project_id, member.user)
        return result
    except (SQLAlchemyError, PostgresError) as e:
        raise HTTPException(status_code=500, detail=e)


@router.put("/{project_id}/member/{member_id}/update-role/{role_id}")
async def change_member_role(project_id: int,
                             member_id: int,
                             role_id: int,
                             service: role_service,
                             member=Depends(partial(required_rights, rights=["change_roles"]))):
    try:
        res = await service.new_member_role(member_id, project_id, role_id, member.user)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
