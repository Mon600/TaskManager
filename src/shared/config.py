import logging
import os
from typing import Dict

from dotenv import load_dotenv

from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine
from sqlalchemy.orm import DeclarativeBase


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_db_url() -> str:
    return (f'postgresql+asyncpg://'
            f'{os.getenv("DB_USER")}:'
            f'{os.getenv("DB_PASSWORD")}@'
            f'{os.getenv("DB_HOST")}:'
            f'{os.getenv("DB_PORT")}/'
            f'{os.getenv("DB_NAME")}')


def get_mongo_db_url() -> str:
    return os.getenv("MONGO_URL")

def get_mongo_db_name() -> str:
    return os.getenv("MONGO_DB_NAME")


def get_engine() -> AsyncEngine:
    db_url = get_db_url()
    engine = create_async_engine(url=db_url)
    return engine

async_session = async_sessionmaker(get_engine(), expire_on_commit=False)

def get_secrets() -> Dict[str, str]:
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    return {"CLIENT_ID": client_id, "CLIENT_SECRET": client_secret}

async def get_auth_data() -> Dict[str, str]:
    return {
        "secret_key": os.getenv("SECRET_KEY"),
        "algorithm": os.getenv("ALGORITHM"),
        "expire_access": int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")),
        "expire_refresh": int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES"))
    }

def get_middleware_secret() -> str:
    return os.getenv('MIDDLEWARE_SECRET')

class Base(DeclarativeBase):
    pass


class CsrfConfig(BaseSettings):
  secret_key: str = os.getenv("CSRF_SECRET")
  token_key: str = "csrf_token"
  header_name: str = "X-CSRFToken"

origins = [
    "http://localhost:3000"
    "http://127.0.0.1:3000"
]

