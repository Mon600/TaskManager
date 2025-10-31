from functools import partial
from typing import Dict, Union

import pymongo.errors
from asyncpg import PostgresError
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.exc import SQLAlchemyError
from starlette.requests import Request

from src.project.management_service.mongo.db.models import ChangeDefaultRoleData, ChangeProjectActionData, \
    DeleteUserActionData
from src.shared.dependencies.service_deps import project_service, members_service
from src.shared.dependencies.user_deps import current_user, required_rights
from src.shared.schemas.Project_schemas import ProjectData, ProjectMemberSchemaExtend, ProjectDataGet

router = APIRouter(prefix="/project", tags=['Project', ])


@router.post("/create")
async def create_project(request: Request,
                         user: current_user,
                         service: project_service,
                         data: ProjectData):
    try:
        project_id = await service.create_project(data, user.id)
        return {'ok': True, 'detail': f"Project with id {project_id} successfully created!"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}")
async def project_page(user: current_user,
                       project: project_service,
                       project_id: int) -> Dict[str, Union[ProjectDataGet, int]]:
    project_data = await project.get_project_info(project_id)
    return project_data


@router.put("/{project_id}/edit")
async def edit_project(project: project_service,
                       project_id: int,
                       new_data: ProjectData,
                       member=Depends(partial(
                           required_rights,
                           rights=['update_project']
                       ))) -> ChangeProjectActionData:
    try:
        project_info = await project.edit_project(project_id, new_data, member.user)
        return project_info
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Ошибка валидации: старые и новые данные совпадают.")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка на стороне сервера. Попробуйте позже.")


@router.get("/{project_id}/members")
async def get_members(service: project_service,
                      project_id: int) -> list[ProjectMemberSchemaExtend]:
    members = await service.get_project_members(project_id)
    if members is None:
        raise HTTPException(status_code=404, detail='Not found')
    return members


@router.put("/{project_id}/change_default_role/{role_id}")
async def update_default_role(service: project_service,
                              project_id: int,
                              role_id: int,
                              member=Depends(partial(
                                  required_rights,
                                  rights=['change_roles']
                              ))) -> ChangeDefaultRoleData:
    try:
        roles_data = await service.change_default_role(project_id, role_id, member.user)
        return roles_data
    except ValueError as e:
        raise HTTPException(400, detail="Cтарые и новые данные совпадают")
    except (SQLAlchemyError, PostgresError) as e:
        raise HTTPException(500, detail=str(e))


@router.delete("/{project_id}/delete-member/{member_id}")
async def delete_member_from_project(project: members_service,
                                     project_id: int,
                                     member_id: int,
                                     reason: str = '',
                                     member=Depends(partial(
                                         required_rights,
                                         rights=['delete_users']
                                     ))) -> DeleteUserActionData:
    try:
        deleted_member = await project.delete_member(project_id, member_id, member.user, reason)
        return deleted_member
    except (SQLAlchemyError, pymongo.errors.OperationFailure) as e:
        raise HTTPException(status_code=500, detail=str(e))
