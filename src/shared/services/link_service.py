import datetime
import json
import logging
import secrets
from typing import Optional, Dict, Any

import redis.exceptions
from asyncpg import PostgresError
from asyncpg.pgproto.pgproto import timedelta
from babel.dates import format_datetime
from redis.asyncio import Redis
from sqlalchemy.exc import SQLAlchemyError

from src.shared.db.repositories.link_repository import LinkRepository
from src.shared.db.repositories.project_repository import ProjectRepository
from src.shared.mongo.db.models import LinkGenerateActionData, LinkDeleteActionData
from src.shared.schemas.Link_schemas import LinkSchema, GetLinkSchema
from src.shared.schemas.Project_schemas import ProjectRel
from src.shared.schemas.User_schema import UserSchema
from src.shared.services.audit_service import AuditService


class LinkService:
    def __init__(self,
                 repository: LinkRepository,
                 p_repository: ProjectRepository,
                 redis: Redis,
                 audit: AuditService):
        self.p_repository = p_repository
        self.repository = repository
        self.redis = redis
        self.audit = audit
        self.logger = logging.getLogger(__name__)


    @staticmethod
    def _calculate_expiration(ex: int) -> tuple[Optional[datetime], Optional[str]]:
        if ex >= 3600:
            end_at = datetime.datetime.now() + timedelta(seconds=ex)
            format_end_at = format_datetime(end_at, format='d MMMM, Y HH:mm', locale='ru')
            return end_at, format_end_at
        return None, "бессрочна"

    @staticmethod
    def _build_cache_data(project_data: dict, format_end_at: str) -> dict:
        if format_end_at == "бессрочна":
            return {"end_at": "бессрочна", "project_rel": project_data}
        return GetLinkSchema.model_validate({
            "end_at": format_end_at,
            "project_rel": project_data
        }).model_dump()

    async def _save_to_redis(self, code: str, cached_data: dict, ex: int) -> None:
        try:
            ttl = ex if ex >= 3600 else 3600
            await self.redis.set(code, json.dumps(cached_data), ex=ttl)
        except redis.exceptions.ConnectionError as e:
            self.logger.warning(f"Redis недоступен: {e}")


    async def generate(self, data: LinkSchema, project_id: int, user: UserSchema) -> Optional[Dict[str, Any]]:
        user_id = user.id
        try:
            project = await self.p_repository.get_by_id(project_id)
            if not project:
                raise ValueError("Invalid project id")

            project_data = ProjectRel.model_validate(project).model_dump()
            code = secrets.token_urlsafe(16)
            end_at, format_end_at = self._calculate_expiration(data.ex)
            cached_data = self._build_cache_data(project_data, format_end_at)

            await self._save_to_redis(code, cached_data, data.ex)

            link = f"http://127.0.0.1:8000/project/invite/{code}"
            data_for_save = {
                "project_id": project_id,
                "creator_id": user_id,
                "end_at": end_at,
                "link": code
            }

            await self.repository.create(data_for_save)
            try:
                data = LinkGenerateActionData(link=link)
                await self.audit.log(project_id, user, data)
                return {
                    "link": link,
                    "ended_at": format_end_at
                }
            except ValueError as e:
                self.logger.warning(f'Ошибка: {str(e)}')
                raise e
        except (SQLAlchemyError, PostgresError) as e:
            self.logger.warning(f"Ошибка при генерации ссылки: {e}")
            raise e


    async def get_project_by_code(self, code: str):
        try:
            data = await self.redis.get(code)
            data_dict = json.loads(data)
            return data_dict
        except:
            project = await self.repository.get_by_code(code)
            res = GetLinkSchema.model_validate(project, strict=False).model_dump()
            await self.redis.set(code, json.dumps(res), ex=3600)
            return res


    async def get_links(self, project_id: int):
        try:
            nowdate = datetime.datetime.now()
            links = await self.repository.get_by_project_id(project_id, nowdate)
            return links
        except (SQLAlchemyError, PostgresError) as e:
            self.logger.warning(f"Ошибка {e}")
            raise e

    async def delete_all_links(self, project_id, user: UserSchema):
        try:
            res = await self.repository.delete_all_links(project_id)
            if res:
                data = LinkDeleteActionData(is_all=True)
                await self.audit.log(project_id, user, data)
                return True
            return False
        except (SQLAlchemyError, PostgresError) as e:
            self.logger.warning(f"Ошибка {e}")
            raise e


    async def delete_link_by_code(self, link_code: str, project_id: int, user: UserSchema) -> LinkDeleteActionData:
        try:
            await self.repository.delete_by_code(link_code)
            try:
                data = LinkDeleteActionData(link=link_code)
                await self.audit.log(project_id, user, data)
                return data
            except ValueError as e:
                self.logger.warning(f'Ошибка: {e}')
                raise e
        except (SQLAlchemyError, PostgresError) as e:
            self.logger.warning(f"Ошибка {e}")
            raise e

