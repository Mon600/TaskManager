import logging
import os

from celery import Celery
from dotenv import load_dotenv

from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from starlette.templating import Jinja2Templates

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_db_url():
    return (f'postgresql+asyncpg://'
            f'{os.getenv("DB_USER")}:'
            f'{os.getenv("DB_PASSWORD")}@'
            f'{os.getenv("DB_HOST")}:'
            f'{os.getenv("DB_PORT")}/'
            f'{os.getenv("DB_NAME")}')


def get_engine():
    db_url = get_db_url()
    engine = create_async_engine(url=db_url)
    return engine

async_session = async_sessionmaker(get_engine(), expire_on_commit=False)

def get_secrets():
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    return {"CLIENT_ID": client_id, "CLIENT_SECRET": client_secret}

async def get_auth_data():
    return {
        "secret_key": os.getenv("SECRET_KEY"),
        "algorithm": os.getenv("ALGORITHM"),
        "expire_access": int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")),
        "expire_refresh": int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES"))
    }


async def get_middleware_secret():
    return os.getenv('MIDDLEWARE_SECRET')

class Base(DeclarativeBase):
    pass


class CsrfConfig(BaseSettings):
  secret_key: str = "3cy8kXHijHDsORojUHQ0eOyVCbu7dzbiRwgwBy4ugy67CTYJvuErSVDy3EX2PDiO"
  token_key: str = "csrf_token"
  header_name: str = "X-CSRFToken"

origins = [
    "http://localhost:3000"
    "http://127.0.0.1:3000"
]

