from typing import Annotated, AsyncGenerator

from beanie import init_beanie
from fastapi import Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.asynchronous.database import AsyncDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from src.project.management_service.mongo.db.database import db
from src.project.management_service.mongo.db.models import History
from src.shared.config import async_session


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


