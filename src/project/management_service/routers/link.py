

from fastapi import APIRouter, Depends, HTTPException
from fastapi_csrf_protect import CsrfProtect
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse

from src.shared.decorators.decorators import PermissionsChecker
from src.shared.dependencies.service_deps import project_service, auth_service, link_service
from src.shared.dependencies.user_deps import current_user
from src.shared.models.Link_schemas import LinkSchema, GetLinksSchema


router = APIRouter(prefix='/links', tags=['Links'])

@router.post('/{project_id}/generate')
@PermissionsChecker('generate_url')
async def generate_url(request: Request,
                       auth: auth_service,
                      user: current_user,
                      project: project_service,
                      service: link_service,
                      data: LinkSchema,
                      project_id: int,
                      csrf_protect: CsrfProtect = Depends()
                      ) -> JSONResponse:

    # await csrf_protect.validate_csrf(request)
    link = await service.generate(data, project_id, user)
    return JSONResponse(link, status_code=201)


@router.get('/invite/{code}')
async def invite_page(request: Request,
                      auth: auth_service,
                      user: current_user,
                      service: link_service,
                      code: str):
    res = await service.get_project_by_code(code)
    project = res['project_rel']
    expiry_date = res['end_at']
    if project['status'] != 'open':
        pass
    context = {
        'request': request,
        'user': user,
        'project': project,
        'expiry_date': expiry_date,
        'code': code,
        'title': "Приглашение присоединиться к проекту"
    }
    return JSONResponse(context)

@router.post('/invite/{code}/accept')
async def accept_invite(request: Request,
                        auth: auth_service,
                        user: current_user,
                        p_service: project_service,
                        l_service: link_service,
                        code: str
                        ):
    project = await l_service.get_project_by_code(code)
    new_member = await p_service.add_member(project, user['id'])
    if new_member is None:
        raise HTTPException(status_code=410, detail='link is expired')
    elif new_member:
        return RedirectResponse(f'/project/{project['project_rel']['id']}', status_code=303)

    else:
        return RedirectResponse('/', status_code=303)


@router.get('/{project_id}/links')
async def project_links(request: Request,
                        auth: auth_service,
                        user: current_user,
                        service: link_service,
                        project_id: int
                        ) -> list[GetLinksSchema]:
    links = await service.get_links(project_id)
    if links:
        return links
    raise HTTPException(status_code=500, detail='Ошибка')


@router.delete("/{project_id}/clear")
async def delete_all_links(request: Request,
                           auth: auth_service,
                           user: current_user,
                           service: link_service,
                           project_id: int
                           ):
    result = await service.delete_all_links(project_id, user)
    if result:
        return JSONResponse({'ok': True}, status_code=200)
    else:
        return JSONResponse({'ok': False}, status_code=500)

@router.delete('/{link_code}/delete')
async def delete_link_by_code(request: Request,
                              auth: auth_service,
                              user: current_user,
                              service: link_service,
                              link_code: str):
    result = await service.delete_link_by_code(link_code, user)
    if result:
        return JSONResponse({'ok': True}, status_code=200)
    else:
        return JSONResponse({'ok': False}, status_code=500)