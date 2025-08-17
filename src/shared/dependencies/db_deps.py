from typing import Annotated, AsyncGenerator

import pymongo.errors
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


from src.shared.config import async_session
from src.shared.mongo.db.database import Database, database


async def get_session() -> AsyncGenerator:
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_mongo() -> AsyncGenerator:
    yield database.db


MongoDep = Annotated[Database, Depends(get_mongo)]



