

from fastapi import APIRouter, Depends, HTTPException
from fastapi_csrf_protect import CsrfProtect
from sqlalchemy.exc import SQLAlchemyError
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse

from src.shared.dependencies.service_deps import project_service, auth_service, link_service, get_project_service
from src.shared.dependencies.user_deps import current_user, user_role
from src.shared.schemas.Link_schemas import LinkSchema, GetLinksSchema


router = APIRouter(prefix='/links', tags=['Links'])


@router.post('/{project_id}/generate', status_code=201)
async def generate_url(user: current_user,
                      role: user_role,
                      service: link_service,
                      data: LinkSchema,
                      project_id: int,
                      csrf_protect: CsrfProtect = Depends()
                      ):

    # await csrf_protect.validate_csrf(request)
    if not role.generate_url:
        raise HTTPException(status_code=403, detail="No access")
    link = await service.generate(data, project_id, user)
    return {"ok": True, "detail": link}


@router.get('/invite/{code}')
async def invite_page(request: Request,
                      user: current_user,
                      service: link_service,
                      code: str):
    res = await service.get_project_by_code(code)
    project = res['project_rel']
    expiry_date = res['end_at']
    if project['status'] != 'open':
        pass
    context = {
        'user': user,
        'project': project,
        'expiry_date': expiry_date,
        'code': code,
        'title': "Приглашение присоединиться к проекту"
    }
    return context

@router.post('/invite/{code}/accept')
async def accept_invite(user: current_user,
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
async def project_links(user: current_user,
                        service: link_service,
                        project_id: int
                        ) -> list[GetLinksSchema]:
    links = await service.get_links(project_id)
    if links:
        return links
    raise HTTPException(status_code=500, detail='Ошибка')


@router.delete("/{project_id}/clear", status_code=200)
async def delete_all_links(user: current_user,
                           role: user_role,
                           service: link_service,
                           project_id: int
                           ):
    if not role.manage_links:
        raise HTTPException(status_code=403, detail='No access')
    result = await service.delete_all_links(project_id, user)
    if result:
        return{'ok': True}
    else:
        return {'ok': False}

@router.delete('/{link_code}/delete')
async def delete_link_by_code(user: current_user,
                              role: user_role,
                              service: link_service,
                              link_code: str):
    if not role.manage_links:
        raise HTTPException(status_code=403, detail='No access')
    try:
        await service.delete_link_by_code(link_code, user)
        return {'ok': True}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
