from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.db.models import User
from src.shared.db.repositories.base_repository import BaseRepository
from src.shared.models.User_schema import UserSchema


class UserRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(User,session)

    async def create_or_update(self, user: UserSchema):
        user_dict = user.model_dump()
        stmt = (
            insert(User)
            .values(**user_dict)
            .on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "username": user.username,
                    "avatar_url": user.avatar_url
                }
            )
            .returning(User.id, User.username, User.avatar_url, User.email)
        )
        user = await self.session.execute(stmt)
        result = user.one()
        await self.session.commit()
        return result