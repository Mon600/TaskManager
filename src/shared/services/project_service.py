import datetime

from redis.asyncio import Redis

from src.project.management_service.mongo.db.models import History, UserJoinActionData, ChangeDefaultRoleData, \
    DeleteUserActionData, ChangeProjectActionData
from src.shared.db.repositories.project_repository import ProjectRepository
from src.shared.models.Project_schemas import ProjectData, ProjectDataGet, ProjectFromMember, ProjectWithRoles, \
    ProjectMember, ProjectMemberExtend
from src.shared.models.Role_schemas import RoleSchema, RoleSchemaWithId


class ProjectService:
    def __init__(self, repository: ProjectRepository, redis: Redis):
        self.repository = repository
        self.redis = redis
        self.month_map = {
            'января': '01', 'февраля': '02', 'марта': '03',
            'апреля': '04', 'мая': '05', 'июня': '06',
            'июля': '07', 'августа': '08', 'сентября': '09',
            'октября': '10', 'ноября': '11', 'декабря': '12'
        }

    async def parse_datetime_ru(self, date_str):
        for month in self.month_map.keys():
            if month in date_str.lower():
                date_str = date_str.replace(month.title(), self.month_map[month])
                date_str = date_str.replace(',', '')
                break
        return datetime.datetime.strptime(date_str, "%d %m %Y %H:%M")

    async def create_project(self, data: ProjectData, user_id: int):
        data_dict = data.model_dump()
        project_id = await self.repository.new_project(data_dict, user_id)
        return project_id

    async def get_project_by_id(self, project_id: int) -> ProjectData | None:
        data = await self.repository.get_by_id(project_id)
        if not data is None:
            data_dict = ProjectData.model_validate(data).model_dump()
            return data_dict
        return data

    async def get_project_info(self, project_id: int, user_id: int):
        """Запросы к БД"""
        data = await self.repository.get_project_info(project_id)
        member = await self.repository.get_project_member(user_id, project_id)

        """Валидация данных"""
        member_dict = ProjectMember.model_validate(member).model_dump()
        data['project'] = ProjectDataGet.model_validate(data['project'], strict=False).model_dump()

        """Структурирование данных"""
        project = data['project']
        tasks = project.pop('tasks_rel')
        members_count = data['members_count']
        tasks_count = data['tasks_count']
        completed_tasks_count = data['completed_tasks_count']

        return {'project_info': {
                                'project': project,
                                'tasks': tasks,
                                'members_count': members_count,
                                'tasks_count': tasks_count,
                                'completed_tasks_count': completed_tasks_count
                                },
                'member': member_dict}


    async def get_projects_by_user_id(self, user_id: int) -> list | None:
        projects = await self.repository.get_projects_by_user_id(user_id)
        if not projects:
            return []
        res = [
            ProjectFromMember.model_validate(
                project[0]
            ).model_dump() | {"member_count": project[1]}
            for project in projects]
        return res

    async def get_project_roles(self, project_id: int):
        roles = await self.repository.get_roles_by_project_id(project_id)
        roles_dict = ProjectWithRoles.model_validate(roles)
        return roles_dict.model_dump()


    async def is_user_project_member(self, project_id: int, user_id: int):
        is_member = await self.repository.get_member_by_user_id(project_id, user_id)
        schema = ProjectMember.model_validate(is_member).model_dump()
        return schema

    async def edit_project(self, proeject_id: int, new_data: ProjectData, user: dict):
        try:
            data_dict = new_data.model_dump()
            res = await self.repository.update_project(proeject_id, data_dict)
            keys = ['name', 'description', 'status']
            old_data_dict = dict(zip(keys, res[1::]))
            record = History(project_id=proeject_id,
                    user= user,
                    action=ChangeProjectActionData(
                        old_data=old_data_dict,
                        new_data=data_dict))
            await record.insert()
            return {"new_data": new_data, "old_data": old_data_dict}
        except Exception as e:
            print(e)
            return None

    async def add_member(self, project: dict, user: dict):
        user_id = user['id']
        record = History(project_id=project['id'], user=user, action=UserJoinActionData())
        if project['end_at'] == 'бессрочна' or project['end_at'] is None:
            if project['project_rel']['status'] == 'open':
                project_data = project['project_rel']
                data_for_save = {
                    'project_id': project_data['id'],
                    'role_id': project_data['default_role_id'],
                    'user_id': user_id
                }
                await self.repository.add_member(data_for_save)
                await record.insert()
                return True
            return False
        try:
            res = await self.parse_datetime_ru(project['end_at'])
            if res > datetime.datetime.now() and project['project_rel']['status'] == 'open':
                project_data = project['project_rel']
                data_for_save = {
                    'project_id': project_data['id'],
                    'role_id': project_data['default_role_id'],
                    'user_id': user_id
                }
                await self.repository.add_member(data_for_save)
                await record.insert()
                return True
            return False
        except Exception as e:
            print(f"Ошибка при парсинге даты: {e}")
            return None

    async def get_project_members(self, project_id: int) -> list[ProjectMemberExtend] | None:
        try:
            res = await self.repository.get_members(project_id)
            return res
        except Exception as e:
            print(f"Ошибка: {e}")
            return None

    async def change_default_role(self, project_id: int, role_id: int, user: dict):
        try:
            res = await self.repository.change_default_role(project_id, role_id)
            roles_dict = [RoleSchemaWithId.model_validate(role).model_dump() for role in res]
            new_role = roles_dict[1]
            old_role = roles_dict[0]
            record = History(user=user,
                             project_id=project_id,
                             action=ChangeDefaultRoleData(
                                                        new_data=new_role,
                                                        old_data=old_role
                                                        )
                             )
            await record.insert()
            return {'old_role': old_role, 'new_role': new_role}
        except Exception as e:
            print(f"Ошибка {e}")
            return None

    async def delete_member(self, project_id: int, member_id: int, user: dict, reason: str = ''):
        try:
            res = await self.repository.delete_member(project_id, member_id)
            deleted_member = ProjectMemberExtend.model_validate(res).model_dump()
            record = History(user=user,
                    project_id=project_id,
                    action=DeleteUserActionData(
                        reason=reason,
                        deleted_user=deleted_member
                                                )
                    )
            await record.insert()
            return deleted_member
        except Exception as e:
            print(f"Ошибка {e}")
            return None