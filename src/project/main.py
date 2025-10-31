import logging
from contextlib import asynccontextmanager

import socketio
import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from src.project.email_service.routers.email import router as email
from src.project.auth_service.routers.auth import router as auth
from src.project.management_service.routers.audit import router as audit
from src.project.management_service.routers.link import router as link_router
from src.project.management_service.routers.project import router as project_router
from src.project.management_service.routers.role import router as role_router
from src.project.management_service.routers.task import router as task_router
from src.project.statistics_service.routers.statistic_router import router as stat
from src.project.management_service.mongo.db.database import database
from src.shared.config import origins, get_middleware_secret
from src.shared.ws.socket import sio

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Приложение запущено 🚀")
    logger.info("Соединение с MongoDB...")
    await database.connect()
    logger.info("Соединение - ✅")
    logger.info("Инициализация MongoDB...")
    await database.init()
    logger.info("Инициализация - ✅")
    yield
    await database.close()
    logger.info("Соединение с MongoDB закрыто")
    print("👋 Приложение остановлено")


app = FastAPI(lifespan=lifespan)
socketio_app = socketio.ASGIApp(sio, other_asgi_app=app)

app.add_middleware(SessionMiddleware, secret_key=get_middleware_secret())

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth)
app.include_router(email)
app.include_router(project_router)
app.include_router(task_router)
app.include_router(link_router)
app.include_router(role_router)
app.include_router(audit)
app.include_router(stat)

if __name__ == "__main__":
    uvicorn.run(app, host='127.0.0.1', port=8000)