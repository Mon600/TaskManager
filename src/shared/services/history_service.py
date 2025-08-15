from src.shared.schemas.FilterSchemas import HistoryFilter
from src.shared.mongo.repositories.mongo_repositroy import MongoRepository


class HistoryService:
    def __init__(self, mongo: MongoRepository):
        self.mongo = mongo


    async def get_history(self, project_id: int):
        result = await self.mongo.get_all(project_id)
        return result


    async def get_filtered_history(self, project_id: int, filters: HistoryFilter):
        result = await self.mongo.get_with_filters(project_id, filters)
        return result
