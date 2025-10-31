from functools import partial

from asyncpg import PostgresError
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from src.project.management_service.mongo.db.models import LinkDeleteActionData, UserJoinActionData
from src.shared.dependencies.service_deps import link_service, members_service
from src.shared.dependencies.user_deps import current_user, required_rights
from src.shared.schemas.Link_schemas import LinkSchema, GetLinksSchema, GetLinkSchema

router = APIRouter(prefix='/links', tags=['Links'])


@router.post('/{project_id}/generate')
async def generate_url(service: link_service,
                       data: LinkSchema,
                       project_id: int,
                       member=Depends(partial(required_rights, rights=['generate_url']))):
    link = await service.generate(data, project_id, member.user)
    return {"ok": True, "detail": link}


@router.get('/invite/{code}')
async def invite_page(user: current_user,
                      service: link_service,
                      code: str) -> GetLinkSchema:
    try:
        link_info = await service.get_project_by_code(code)
        if link_info.project_rel.status != 'open':
            raise HTTPException(status_code=403, detail="No access")
        return link_info
    except KeyError:
        raise HTTPException(status_code=404, detail="Ссылка не найдена или устарела.")
    except (SQLAlchemyError, PostgresError):
        raise HTTPException(status_code=500, detail="Ошибка сервера. Попробуйте позже")


@router.post('/invite/{code}/accept')
async def accept_invite(user: current_user,
                        service: members_service,
                        code: str) -> UserJoinActionData:
    try:
        action = await service.add_member(code, user)
        return action
        # return RedirectResponse(f"http://127.0.0.1:800/project/{action.project_data.id}", status_code=303)
    except IntegrityError:
        raise HTTPException(status_code=403, detail="Вы уже участник проекта")
    except KeyError:
        raise HTTPException(status_code=410, detail='link is expired')
    except ValueError:
        raise HTTPException(status_code=409, detail='Invalid data')
    except (SQLAlchemyError, PostgresError):
        raise HTTPException(status_code=500, detail='Ошибка сервера')


@router.get('/{project_id}/links')
async def project_links(service: link_service,
                        project_id: int,
                        member=Depends(
                            partial(
                                required_rights,
                                rights=["manage_links"]
                            ))) -> list[GetLinksSchema]:
    try:
        links = await service.get_links(project_id)
        if not links:
            raise HTTPException(404, f'No links for project with id {project_id}')
        return links
    except (PostgresError, SQLAlchemyError):
        raise HTTPException(500, 'Ошибка сервера.')


@router.delete("/{project_id}/clear", status_code=200)
async def delete_all_links(service: link_service,
                           project_id: int,
                           member=Depends(
                               partial(
                                   required_rights,
                                   rights=["manage_links"]
                               ))):
    try:
        result = await service.delete_all_links(project_id, member.user)
        return result
    except KeyError:
        raise HTTPException(404, "Links no found")


@router.delete('/{project_id}/{link_code}/delete')
async def delete_link_by_code(project_id: int,
                              service: link_service,
                              link_code: str,
                              member=Depends(
                                  partial(
                                      required_rights,
                                      rights=["manage_links"]
                                  ))
                              ) -> LinkDeleteActionData:
    try:
        action = await service.delete_link_by_code(link_code, project_id, member.user)
        return action
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
