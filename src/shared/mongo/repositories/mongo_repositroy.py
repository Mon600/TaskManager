from typing import Dict, Any

from src.shared.mongo.db.models import BaseActionData, History


class MongoRepository:

    async def add_to_db(self,
                        action: BaseActionData,
                        project_id: int,
                        user: Dict[str, Any]):
        record = History(user=user,
                         project_id=project_id,
                         action=action)
        await record.insert()
        return True