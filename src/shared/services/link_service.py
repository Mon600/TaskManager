import datetime
import json
import secrets
from typing import Optional, Dict, Any

from asyncpg.pgproto.pgproto import timedelta
from babel.dates import format_datetime
from pymongo.asynchronous.database import AsyncDatabase
from redis.asyncio import Redis

from src.project.management_service.mongo.db.models import History, LinkGenerateActionData, LinkDeleteActionData
from src.shared.db.repositories.link_repository import LinkRepository
from src.shared.db.repositories.project_repository import ProjectRepository
from src.shared.models.Link_schemas import LinkSchema, GetLinkSchema
from src.shared.models.Project_schemas import ProjectRel
from src.shared.models.User_schema import UserSchema



class LinkService:
    def __init__(self, repository: LinkRepository, p_repository: ProjectRepository, redis: Redis):
        self.p_repository = p_repository
        self.repository = repository
        self.redis = redis


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
        except Exception as e:
            print(f"Redis недоступен: {e}")


    async def generate(self, data: LinkSchema, project_id: int, user: dict) -> Optional[Dict[str, Any]]:
        user_id = user['id']
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
            record = History(
                project_id=project_id,
                user=user,
                action=LinkGenerateActionData(link=link)
            )
            await record.insert()

            return {
                "link": link,
                "ended_at": format_end_at
            }
        except Exception as e:
            print(f"Ошибка при генерации ссылки: {e}")
            return None


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
        except Exception as e:
            print(f"Ошибка {e}")
            return False

    async def delete_all_links(self, project_id, user):
        try:
            await self.repository.delete_all_links(project_id)
            record = History(
                project_id=project_id,
                user=user,
                action=LinkDeleteActionData(
                    is_all=True))
            await record.insert()
            return True
        except Exception as e:
            print(f"Ошибка {e}")
            return False


    async def delete_link_by_code(self, link_code: str, user: dict):
        try:
            project_id = await self.repository.delete_by_code(link_code)
            record = History(
                project_id=project_id,
                user=user,
                action=LinkDeleteActionData(
                    link=link_code))
            await record.insert()
            return True
        except Exception as e:
            print(f"Ошибка {e}")
            return False

