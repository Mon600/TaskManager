from fastapi import APIRouter, Form, HTTPException, Depends
from fastapi_csrf_protect import CsrfProtect
from starlette.requests import Request
from starlette.responses import RedirectResponse, JSONResponse
from src.shared.decorators.decorators import PermissionsChecker
from src.shared.dependencies.user_deps import current_user
from src.shared.models.Project_schemas import ProjectData, ProjectMemberExtend
from src.shared.dependencies.service_deps import project_service, auth_service



router = APIRouter(prefix="/project", tags=['Project',])


@router.get("/create")
async def create_project(request: Request,
                         user: current_user,
                         auth: auth_service,
                         csrf_protect: CsrfProtect = Depends()):
    if user is None:
        return RedirectResponse("http://127.0.0.1:8002/auth")
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    context = {"request": request,
               "user": user,
               "csrf_token": csrf_token,
               "title": "Создать проект"}

    response = JSONResponse(context)
    csrf_protect.set_csrf_cookie(signed_token, response)
    return response


@router.post("/create")
async def create_project(request: Request,
                         user: current_user,
                         auth: auth_service,
                         service: project_service,
                         data: ProjectData,
                         csrf_protect: CsrfProtect = Depends()):
    await csrf_protect.validate_csrf(request)
    try:
        project_id = await service.create_project(data, user['id'])
        return RedirectResponse(f"/project/{project_id}", status_code=302)
    except Exception as e:
        return RedirectResponse("/")


@router.get("/{project_id}")
async def project_page(request: Request,
                       user: current_user,
                       auth: auth_service,
                       project: project_service,
                       project_id: int,
                       csrf_protect: CsrfProtect = Depends()
                       ):

    if user is None:
        return RedirectResponse("http://127.0.0.1:8002/auth/")
    project_data = await project.get_project_info(project_id, 158022215)#user['id'])
    if project_data['member'] is None:
        raise HTTPException(status_code=404, detail="Not found")

    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    context= {"request": request,
               "project_data": project_data['project_info'],
               "member": project_data['member'],
               "project_id": project_id,
               "user": user,
               "title": project_data['project_info']['project']['name'],
               "csrf_token": csrf_token
               }
    response = JSONResponse(context)
    csrf_protect.set_csrf_cookie(signed_token, response)
    return response


@router.put("/{project_id}/edit")
@PermissionsChecker("update_project")
async def edit_project(request: Request,
                     user: current_user,
                     auth: auth_service,
                     project: project_service,
                     project_id: int,
                     new_data: ProjectData,
                     # csrf_protect: CsrfProtect = Depends()
                    ):
    # await csrf_protect.validate_csrf(request)
    project_info = await project.edit_project(project_id, new_data, user)
    return project_info


@router.get("/{project_id}/members")
async def get_members(request: Request,
                      user: current_user,
                      auth: auth_service,
                      project: project_service,
                      project_id: int) -> list[ProjectMemberExtend]:
    members = await project.get_project_members(project_id)
    if members is None:
        raise HTTPException(status_code=404, detail='Not found')
    return members


@router.put("/{project_id}/change_default_role/{role_id}")
@PermissionsChecker('manage_roles')
async def update_default_role(request: Request,
                              user: current_user,
                              auth: auth_service,
                              project: project_service,
                              project_id: int,
                              role_id: int) -> JSONResponse:
    roles_data = await project.change_default_role(project_id, role_id, user)
    if roles_data:
        return JSONResponse(roles_data, status_code=200)
    else:
        raise HTTPException(500, detail='Server error. Try again later.')


@router.delete("/{project_id}/delete-member/{member_id}")
@PermissionsChecker('delete_users')
async def delete_member_from_project(request: Request,
                                      user: current_user,
                                      auth: auth_service,
                                      project: project_service,
                                      project_id: int,
                                      member_id: int,
                                      reason: str = '') -> JSONResponse:
    deleted_member = await project.delete_member(project_id, member_id, user, reason)
    if deleted_member:
        return JSONResponse({"deleted_member": deleted_member}, status_code=200)
    else:
        raise HTTPException(500, detail='Server error. Try again later.')









