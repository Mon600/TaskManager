import datetime
import logging
from typing import Dict, Any

from redis.asyncio import Redis

from src.shared.db.repositories.project_member_repository import ProjectMemberRepository
from src.shared.db.repositories.project_repository import ProjectRepository
from src.shared.db.repositories.role_repository import RoleRepository
from src.shared.models.Project_schemas import ProjectData, ProjectDataGet, ProjectFromMember, ProjectWithRoles, \
    ProjectMember, ProjectMemberExtend
from src.shared.models.Role_schemas import RoleSchemaWithId
from src.shared.mongo.db.models import ChangeProjectActionData, UserJoinActionData, ChangeDefaultRoleData, \
    DeleteUserActionData
from src.shared.mongo.repositories.mongo_repositroy import MongoRepository


class ProjectService:
    def __init__(self,
                 project_repository: ProjectRepository,
                 role_repository: RoleRepository,
                 members_repository: ProjectMemberRepository,
                 mongo: MongoRepository,
                 redis: Redis):
        self.project_repository = project_repository
        self.role_repository = role_repository
        self.members_repository = members_repository
        self.mongo = mongo
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
        data_dict = data.model_dump()
        project_id = await self.project_repository.new_project(data_dict, user_id)
        return project_id

    async def get_project_by_id(self, project_id: int) -> ProjectData | None:
        data = await self.project_repository.get_by_id(project_id)
        if not data is None:
            data_dict = ProjectData.model_validate(data).model_dump()
            return data_dict
        return data

    async def get_project_info(self, project_id: int, user_id: int):
        data = await self.project_repository.get_project_info(project_id)
        member = await self.members_repository.get_member_by_user_id(project_id, user_id)

        member_dict = ProjectMember.model_validate(member).model_dump()
        data['project'] = ProjectDataGet.model_validate(data['project'], strict=False).model_dump()

        project = data['project']

        members_count = data['members_count']
        tasks_count = data['tasks_count']
        completed_tasks_count = data['completed_tasks_count']

        return {'project_info': {
            'project': project,
            'members_count': members_count,
            'tasks_count': tasks_count,
            'completed_tasks_count': completed_tasks_count
        },
            'member': member_dict}

    async def get_projects_by_user_id(self, user_id: int) -> list | None:
        projects = await self.members_repository.get_projects_by_user_id(user_id)
        if not projects:
            return []
        res = [
            ProjectFromMember.model_validate(
                project[0]
            ).model_dump() | {"member_count": project[1]}
            for project in projects]
        return res

    async def get_project_roles(self, project_id: int):
        roles = await self.role_repository.get_roles(project_id)  # Role_repository
        roles_dict = ProjectWithRoles.model_validate(roles)
        return roles_dict.model_dump()

    async def is_user_project_member(self, project_id: int, user_id: int):
        is_member = await self.members_repository.get_member_by_user_id(project_id, user_id)
        schema = ProjectMember.model_validate(is_member).model_dump()
        return schema

    async def edit_project(self, project_id: int, new_data: ProjectData, user: dict):
        try:
            data_dict = new_data.model_dump()
            res = await self.project_repository.update_project(project_id, data_dict)
            keys = ['name', 'description', 'status']
            old_data_dict = dict(zip(keys, res[1::]))

            action=ChangeProjectActionData(
                 old_data=old_data_dict,
                 new_data=data_dict)
            await self.mongo.add_to_db(action, project_id, user)
            return {"new_data": new_data, "old_data": old_data_dict}
        except Exception as e:
            self.logger.warning(e)
            return False

    async def add_member(self, link_data: Dict[str, Any], user: Dict[str, Any]) -> bool:

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

            action = UserJoinActionData()
            await self.mongo.add_to_db(action, project_id, user)
            return True

        except Exception as e:
            self.logger.error("Ошибка при добавлении участника в проект %s: %s", project_id, e)
            return False

    async def get_project_members(self, project_id: int) -> list[ProjectMemberExtend] | None:
        try:
            res = await self.project_repository.get_members(project_id)
            return res
        except Exception as e:
            print(f"Ошибка: {e}")
            return None

    async def change_default_role(self, project_id: int, role_id: int, user: dict):
        try:
            res = await self.project_repository.change_default_role(project_id, role_id)
            roles_dict = [RoleSchemaWithId.model_validate(role).model_dump() for role in res]
            new_role = roles_dict[1]
            old_role = roles_dict[0]

            action = ChangeDefaultRoleData(
                 new_data=new_role,
                 old_data=old_role
             )

            await self.mongo.add_to_db(action, project_id, user)
            return {'old_role': old_role, 'new_role': new_role}
        except Exception as e:
            print(f"Ошибка {e}")
            return None

    async def delete_member(self, project_id: int, member_id: int, user: dict, reason: str = ''):
        try:
            res = await self.members_repository.delete_member(project_id, member_id)
            deleted_member = ProjectMemberExtend.model_validate(res).model_dump()

            action=DeleteUserActionData(
                 reason=reason,
                 deleted_user=deleted_member
            )
            await self.mongo.add_to_db(action, project_id, user)
            return deleted_member
        except Exception as e:
            print(f"Ошибка {e}")
            return None
