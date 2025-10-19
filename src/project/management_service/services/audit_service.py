import logging

import pymongo.errors

from src.project.management_service.mongo.db.models import BaseActionData
from src.project.management_service.mongo.repositories.mongo_repositroy import MongoRepository
from src.shared.schemas.FilterSchemas import HistoryFilter
from src.shared.schemas.User_schema import UserSchema


class AuditService:
    def __init__(self, mongo: MongoRepository):
        self.mongo = mongo
        self.logger = logging.getLogger(__name__)

    async def log(self,
                  project_id: int,
                  user: UserSchema,
                  data: BaseActionData):
        try:
            await self.mongo.add_to_db(data, project_id, user)
        except pymongo.errors.PyMongoError as e:
            self.logger.warning(f"Ошибка: {str(e)}")
            raise e

    async def get_audit(self, project_id: int):
        result = await self.mongo.get_all(project_id)
        return result

    async def get_filtered_audit(self, project_id: int, filters: HistoryFilter):
        result = await self.mongo.get_with_filters(project_id, filters)
        return result
