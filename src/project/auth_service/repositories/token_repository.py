from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.db.models import RefreshToken
from src.shared.db.repositories.base_repository import BaseRepository


class TokenRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(RefreshToken, session)
