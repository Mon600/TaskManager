import logging

from asyncpg import PostgresError
from redis.asyncio import Redis
from sqlalchemy.exc import SQLAlchemyError

from src.shared.db.repositories.project_repository import ProjectRepository
from src.shared.mongo.db.models import ChangeDefaultRoleData, ChangeProjectActionData
from src.shared.schemas.Project_schemas import ProjectData, ProjectFromMember, ProjectMemberSchemaExtend, ProjectRel
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


    async def create_project(self, data: ProjectData, user_id: int):
        try:
            data_dict = data.model_dump()
            project_id = await self.project_repository.new_project(data_dict, user_id)
            return project_id
        except SQLAlchemyError as e:
            self.logger.warning(f'Ошибка: {e}')
            raise e

    async def get_project_by_id(self, project_id: int) -> ProjectRel | None:
        data = await self.project_repository.get_by_id(project_id)
        if not data is None:
            project_rel_schema = ProjectRel.model_validate(data)
            return project_rel_schema
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



