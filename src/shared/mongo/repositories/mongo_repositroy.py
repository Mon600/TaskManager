from typing import Dict, Any

from src.shared.schemas.FilterSchemas import HistoryFilter
from src.shared.mongo.db.models import BaseActionData, History
from src.shared.schemas.User_schema import UserSchema


class MongoRepository:

    @staticmethod
    async def add_to_db(action: BaseActionData,
                        project_id: int,
                        user: UserSchema):
        record = History(user=user,
                         project_id=project_id,
                         action=action)
        await record.insert()
        return True


    @staticmethod
    async def get_all(project_id: int):
        result = await History.find({'project_id': project_id}).to_list()
        return result

    @staticmethod
    async def get_with_filters(project_id: int, filters: HistoryFilter):
        history_filter = {'project_id': project_id}
        if user_id := filters.from_user:
            history_filter.update({'user.id': user_id})
        if start_interval := filters.time_interval_start:
            history_filter.update({'action.timestamp': {'$gte': start_interval}})
        if end_interval := filters.time_interval_end:
            history_filter.update({'action.timestamp': {'$lte': end_interval}})
        if action_type := filters.action_type:
            history_filter.update({'action.action_type': {"$in": action_type}})
        result = await History.find(history_filter).to_list()
        return result

