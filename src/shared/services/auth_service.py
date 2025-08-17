import datetime
import json
import logging

import redis
from authlib.integrations.starlette_client import OAuth
from jose import JWTError
from redis.asyncio import Redis
from sqlalchemy.exc import SQLAlchemyError

from src.shared.db.repositories.token_repository import TokenRepository
from src.shared.jwt.jwt import create_token, decode_token
from src.shared.db.repositories.user_repository import UserRepository
from src.shared.schemas.Token_schemas import TokenModel
from src.shared.schemas.User_schema import UserSchema
from src.shared.config import get_secrets


class AuthService:
    def __init__(self, repository: UserRepository, tokens_repository: TokenRepository, redis: Redis):
        self.secrets = get_secrets()
        self.oauth = OAuth()
        self.repository = repository
        self.tokens_repository = tokens_repository
        self.redis = redis
        self.logger = logging.getLogger(__name__)
        self.oauth.register(
            name='github',
            client_id=self.secrets['CLIENT_ID'],
            client_secret=self.secrets['CLIENT_SECRET'],
            authorize_url='https://github.com/login/oauth/authorize',
            access_token_url='https://github.com/login/oauth/access_token',
            api_base_url='https://api.github.com/',
            client_kwargs={'scope': 'user:email user:user'},

        )

    async def get_token(self, user_id: int) -> dict | None:
        data = {"user_id": user_id}
        access_token = await create_token(data)
        refresh_token = await create_token(data, token_type="refresh")
        data = await decode_token(refresh_token['token'])
        exp = datetime.datetime.fromtimestamp(data['exp'])
        data_for_save = {'id': refresh_token['token_id'], 'token': refresh_token['token'], 'exp': exp }
        await self.tokens_repository.create(data_for_save)
        if access_token and refresh_token:
            try:
                await self.redis.set(refresh_token['token_id'], refresh_token['token'], ex= 43200 * 60)
            except redis.exceptions.ConnectionError as e:
                self.logger.warning(f"Redis недоступен: {e}")
            return {"access_token": access_token['token'], "refresh_token": refresh_token["token_id"]}
        return  None


    async def register_user(self, user_json: dict, email_json: dict) -> tuple | None:
        for email in email_json:
            if email['primary']:
                user_email = email['email']
                break
        else:
            user_email = None
        user_schema = UserSchema(id = user_json['id'],
                                 username=user_json['login'],
                                 email=user_email,
                                 avatar_url=user_json['avatar_url'])

        res = await self.repository.create_or_update(user_schema)
        if res:
            return res
        else:
            return None


    async def get_user_data(self, user_id: int) -> UserSchema | None:
        user_data = await self.repository.get_by_id(int(user_id))
        if user_data:
            return user_data
        else:
            return None


    async def refresh(self, refresh_token: str) -> dict | None:
        data = None

        try:
            data = await self.redis.get(refresh_token)
            if data is not None:
                data = json.loads(data)
        except redis.exceptions.ConnectionError as e:
            self.logger.warning(f"Ошибка Redis: {e}")

        if data is None:
            try:
                db_record = await self.tokens_repository.get_by_id(refresh_token)
                if not db_record:
                    return None

                data_schema = TokenModel.model_validate(db_record)
                if data_schema.exp < datetime.datetime.now():
                    return None

                data = data_schema.token
            except SQLAlchemyError as e:
                self.logger.warning(f"Ошибка при работе с БД: {e}")
                return None

        try:
            token_data = await decode_token(data)
            if token_data.get("type") != "refresh":
                return None

            user_id = token_data["user_id"]
            access_token = await create_token({"user_id": user_id})
            return access_token

        except JWTError as e:
            self.logger.warning(f"Ошибка при декодировании токена: {e}")
            return None


    async def logout(self, refresh_token_id):
        try:
            refresh_token = await self.redis.get(refresh_token_id)
            if refresh_token:
                payload = await decode_token(refresh_token)
                user_id = payload['user_id']
                await self.redis.delete(f"current_user{user_id}")
            await self.redis.delete(refresh_token_id)
        except redis.exceptions.ConnectionError as e:
            self.logger.warning(f'Redis недоступен: {e}')






