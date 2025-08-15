import pymongo.errors
from fastapi import APIRouter, Form, HTTPException, Depends
from fastapi_csrf_protect import CsrfProtect
from sqlalchemy.exc import SQLAlchemyError
from starlette.requests import Request
from starlette.responses import RedirectResponse, JSONResponse

from src.shared.dependencies.user_deps import current_user, user_role
from src.shared.schemas.Project_schemas import ProjectData, ProjectMemberExtend
from src.shared.dependencies.service_deps import project_service, task_service, get_project_service
from src.shared.mongo.db.models import ChangeDefaultRoleData

router = APIRouter(prefix="/project", tags=['Project',])


@router.get("/create")
async def create_project(request: Request,
                         user: current_user,
                         csrf_protect: CsrfProtect = Depends()):
    if user is None:
        return RedirectResponse("http://127.0.0.1:8002/auth")
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    context = {"request": request,
               "user": user,
               "csrf_token": csrf_token,
               "title": "Создать проект"}

    # csrf_protect.set_csrf_cookie(signed_token, response)
    return context


@router.post("/create")
async def create_project(request: Request,
                         user: current_user,
                         service: project_service,
                         data: ProjectData,
                         csrf_protect: CsrfProtect = Depends()):
    # await csrf_protect.validate_csrf(request)
    try:
        project_id = await service.create_project(data, user.id)
        return {'ok': True, 'detail': f"Project with id {project_id} successfully created! "}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}")
async def project_page(user: current_user,
                       project: project_service,
                       project_id: int,
                       csrf_protect: CsrfProtect = Depends()
                       ):

    if user is None:
        return RedirectResponse("http://127.0.0.1:8002/auth/")
    project_data = await project.get_project_info(project_id, user['id'])

    if project_data['member'] is None:
        raise HTTPException(status_code=404, detail="Not found")

    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    context= {"project_data": project_data['project_info'],

               "project_id": project_id,
               "user": user,
               "title": project_data['project_info']['project']['name'],
               "csrf_token": csrf_token
               }

    # csrf_protect.set_csrf_cookie(signed_token, response)
    return context


@router.put("/{project_id}/edit")
async def edit_project(request: Request,
                       user: current_user,
                       role: user_role,
                       project: project_service,
                       project_id: int,
                       new_data: ProjectData,
                     # csrf_protect: CsrfProtect = Depends()
                    ):
    # await csrf_protect.validate_csrf(request)
    if role.update_project:
        try:
            project_info = await project.edit_project(project_id, new_data, user)
            return project_info
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=403, detail='No access')


@router.get("/{project_id}/members")
async def get_members(project: project_service,
                      project_id: int
                      ) -> list[ProjectMemberExtend]:
    members = await project.get_project_members(project_id)
    if members is None:
        raise HTTPException(status_code=404, detail='Not found')
    return members


@router.put("/{project_id}/change_default_role/{role_id}")
async def update_default_role(request: Request,
                              user: current_user,
                              role: user_role,
                              project: project_service,
                              project_id: int,
                              role_id: int) -> ChangeDefaultRoleData:
    if role.change_roles:
        try:
            roles_data = await project.change_default_role(project_id, role_id, user)
            return roles_data
        except ValueError as e:
            raise HTTPException(400, detail=str(e))
        except Exception as e:
            raise HTTPException(500, detail=str(e))
    else:
        raise HTTPException(status_code=403, detail='No access')


@router.delete("/{project_id}/delete-member/{member_id}")
async def delete_member_from_project(request: Request,
                                    user: current_user,
                                    role: user_role,
                                    project: project_service,
                                    project_id: int,
                                    member_id: int,
                                    reason: str = '') -> ProjectMemberExtend:
    if role.delete_users:
        try:
            deleted_member = await project.delete_member(project_id, member_id, user, reason)
            return deleted_member
        except (SQLAlchemyError, pymongo.errors.OperationFailure) as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=403, detail='No access')
