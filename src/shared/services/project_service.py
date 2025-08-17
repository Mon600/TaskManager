import datetime
import logging
from typing import Dict, Any

import pymongo.errors
from asyncpg import PostgresError
from redis.asyncio import Redis
from sqlalchemy.exc import SQLAlchemyError

from src.shared.db.repositories.project_repository import ProjectRepository
from src.shared.db.repositories.role_repository import RoleRepository
from src.shared.mongo.db.models import DeleteUserActionData, ChangeDefaultRoleData, ChangeProjectActionData, \
    UserJoinActionData
from src.shared.schemas.Project_schemas import ProjectData, ProjectDataGet, ProjectFromMember, ProjectMemberSchemaExtend
from src.shared.schemas.Role_schemas import RoleSchemaWithId, RoleSchema
from src.shared.schemas.User_schema import UserSchema
from src.shared.services.audit_service import AuditService


class ProjectService:
    def __init__(self,
                 project_repository: ProjectRepository,
                 audit: AuditService,
                 redis: Redis):
        self.project_repository = project_repository
        self.audit = audit
        self.redis = redis
        self.month_map = {
            'января': '01', 'февраля': '02', 'марта': '03',
            'апреля': '04', 'мая': '05', 'июня': '06',
            'июля': '07', 'августа': '08', 'сентября': '09',
            'октября': '10', 'ноября': '11', 'декабря': '12'
        }
        self.logger = logging.getLogger(__name__)

    async def parse_datetime_ru(self, date_str):
        for month in self.month_map.keys():
            if month in date_str.lower():
                date_str = date_str.replace(month.title(), self.month_map[month])
                date_str = date_str.replace(',', '')
                break
        return datetime.datetime.strptime(date_str, "%d %m %Y %H:%M")

    async def _is_link_valid(self, link_data: Dict[str, Any]) -> bool:
        end_at = link_data.get('end_at')

        if end_at in ('бессрочна', None):
            return True

        try:
            expiration_time = await self.parse_datetime_ru(end_at)
            return expiration_time > datetime.datetime.now()
        except Exception as e:
            self.logger.warning("Не удалось распарсить дату окончания ссылки '%s': %s", end_at, e)
            return False

    async def create_project(self, data: ProjectData, user_id: int):
        try:
            data_dict = data.model_dump()
            project_id = await self.project_repository.new_project(data_dict, user_id)
            return project_id
        except SQLAlchemyError as e:
            self.logger.warning(f'Ошибка: {e}')
            raise e

    async def get_project_by_id(self, project_id: int) -> ProjectData | None:
        data = await self.project_repository.get_by_id(project_id)
        if not data is None:
            data_dict = ProjectData.model_validate(data).model_dump()
            return data_dict
        return data

    async def get_project_info(self, project_id: int):
        data = await self.project_repository.get_project_info(project_id)

        project = data['project']
        members_count = data['members_count']


        return {
            'project': project,
            'members_count': members_count,
        }


    async def get_projects_by_user_id(self, user_id: int) -> list | None:
        projects = await self.project_repository.get_projects_by_user_id(user_id)
        if not projects:
            return []
        res = [
            ProjectFromMember.model_validate(
                project[0]
            ).model_dump() | {"member_count": project[1]}
            for project in projects]
        return res

    # async def get_project_roles(self, project_id: int):
    #     roles = await self.role_repository.get_roles(project_id)
    #     roles_dict = ProjectWithRoles.model_validate(roles)
    #     return roles_dict.model_dump()

    async def edit_project(self, project_id: int, new_data: ProjectData, user: UserSchema) -> ChangeProjectActionData:
        try:
            data_dict = new_data.model_dump()
            res = await self.project_repository.update_project(project_id, data_dict)

            data = ChangeProjectActionData.model_validate({'new_data': new_data, "old_data": res})
            await self.audit.log(project_id, user, data)
            return data
        except ValueError as e:
            self.logger.warning(e)
            raise e
        except Exception as e:
            self.logger.warning(e)
            raise e

    async def add_member(self, link_data: Dict[str, Any], user: UserSchema) -> bool:

        user_id = user['id']
        project_rel = link_data.get('project_rel')

        if not project_rel:
            self.logger.warning("Отсутствует 'project_rel' в данных ссылки")
            return False

        project_id = project_rel.get('id')
        if not project_id:
            self.logger.warning("Отсутствует ID проекта в project_rel")
            return False

        if project_rel.get('status') != 'open':
            return False

        if not await self._is_link_valid(link_data):
            return False

        data_for_save = {
            'project_id': project_id,
            'role_id': project_rel['default_role_id'],
            'user_id': user_id,
        }

        try:
            await self.members_repository.add_member(data_for_save)

            await self.audit.log(project_id, user, UserJoinActionData())
            return True

        except Exception as e:
            self.logger.error("Ошибка при добавлении участника в проект %s: %s", project_id, e)
            return False

    async def get_project_members(self, project_id: int) -> list[ProjectMemberSchemaExtend] | None:
        try:
            res = await self.project_repository.get_members(project_id)
            return res
        except Exception as e:
            print(f"Ошибка: {e}")
            return None

    async def change_default_role(self, project_id: int, role_id: int, user: UserSchema) -> ChangeDefaultRoleData:
        try:
            roles = await self.project_repository.change_default_role(project_id, role_id)

            new_role = roles[1]
            old_role = roles[0]

            data = ChangeDefaultRoleData(
                new_data = new_role,
                old_data =  old_role)
            await self.audit.log(project_id, user, data)
            return data
        except ValueError as e:
            self.logger.warning(f"Ошибка: {e}")
            raise e
        except (PostgresError, SQLAlchemyError) as e:
            self.logger.warning(f"Ошибка: {e}")
            raise e



