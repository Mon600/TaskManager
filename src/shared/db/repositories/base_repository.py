from tkinter.tix import Select

from pydantic import BaseModel
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession



class BaseRepository:
    def __init__(self, model, session: AsyncSession):
        self.session = session
        self.model = model

    async def get_by_id(self, id: int | str):
        query = select(self.model).where(self.model.id == id)
        result = await self.session.execute(query)
        res = result.scalars().one_or_none()
        return res


    async def get_all(self):
        try:
            query = select(self.model)
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e :
            print(e)
            await self.session.rollback()
            return False

    async def create(self, data):
        try:
            if not isinstance(data, dict):
                data = data.model_dump()
            new_model = self.model(**data)
            self.session.add(new_model)
            await self.session.commit()
            return True
        except Exception as e :
            print(e)
            await self.session.rollback()
            return False

    async def delete_by_id(self, id: int):
        try:
            query = delete(self.model).where(self.model.id == id)
            await self.session.execute(query)
            await self.session.commit()
            return True
        except Exception as e :
            print(e)
            await self.session.rollback()
            return False

    async def update_by_id(self, id: int, data: dict):
        try:
            query = update(self.model).where(self.model.id == id).values(**data)
            await self.session.execute(query)
            await self.session.commit()
            return True
        except Exception as e :
            print(e)
            await self.session.rollback()
            return False






