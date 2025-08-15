import asyncio
from contextlib import asynccontextmanager

import socketio
import uvicorn
from alembic.command import history
from fastapi import FastAPI, Depends

from fastapi_csrf_protect import CsrfProtect
from redis.asyncio import Redis
from starlette.middleware.cors import CORSMiddleware

from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse, JSONResponse

from src.shared.dependencies.redis_deps import RedisDep, get_redis
from src.shared.mongo.db.database import db
from src.project.management_service.routers.project import router as project_router
from src.project.management_service.routers.link import router as link_router
from src.project.management_service.routers.role import router as role_router
from src.project.management_service.routers.task import router as task_router
from src.project.management_service.routers.history import router as history_router
from src.project.management_service.routers.broker_router import router as broker
from src.shared.config import CsrfConfig, origins, get_middleware_secret

from src.shared.dependencies.service_deps import project_service
from src.shared.dependencies.user_deps import current_user
from src.shared.middlewares.token_middleware import RefreshTokenMiddleware
from src.shared.ws.socket import sio


@asynccontextmanager
async def lifespan(app: FastAPI):

    await db.connect("mongodb://localhost:27017", 'history-db')#указать имя и url базы Mongo
    print("🚀 Приложение запущено")
    yield

    # await db.close()
    print("👋 Приложение остановлено")

app = FastAPI(lifespan=lifespan)

socketio_app = socketio.ASGIApp(sio, other_asgi_app=app)


@CsrfProtect.load_config
def get_csrf_config():
    return CsrfConfig()


app.add_middleware(SessionMiddleware, secret_key=get_middleware_secret())
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RefreshTokenMiddleware)




app.include_router(project_router)
app.include_router(task_router)
app.include_router(link_router)
app.include_router(role_router)
app.include_router(history_router)
app.include_router(broker)

@app.get("/")
async def main_page(user: current_user,
                    service: project_service):
    if user is None:
        return RedirectResponse("http://127.0.0.1:8002/auth")
    projects = await service.get_projects_by_user_id(user.id)
    context = {
        "user": user,
        "projects": projects
    }

    return context


if __name__ == "__main__":
    uvicorn.run(socketio_app, host='127.0.0.1', port=8000)