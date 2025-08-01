import logging
from contextlib import asynccontextmanager

import socketio
import uvicorn
from fastapi import FastAPI

from fastapi_csrf_protect import CsrfProtect
from starlette.middleware.cors import CORSMiddleware

from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, JSONResponse
from starlette.staticfiles import StaticFiles

from src.project.management_service.mongo.db.database import db
from src.project.management_service.routers.project import router as project_router
from src.project.management_service.routers.link import router as link_router
from src.project.management_service.routers.role import router as role_router
from src.project.management_service.routers.task import router as task_router
from src.shared.config import CsrfConfig, origins, get_middleware_secret

from src.shared.dependencies.service_deps import auth_service, project_service, task_service
from src.shared.dependencies.user_deps import current_user
from src.shared.middlewares.token_middleware import RefreshTokenMiddleware
from src.shared.ws.socket import sio


@asynccontextmanager
async def lifespan(app: FastAPI):

    await db.connect("mongodb://localhost:27017", 'history-db')#указать имя и url базы Mongo
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
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

# app.mount("/static", StaticFiles(directory="static"), name="static")


app.include_router(project_router)
app.include_router(task_router)
app.include_router(link_router)
app.include_router(role_router)

@app.get("/")
async def main_page(request: Request,
                    auth: auth_service,
                    user: current_user,
                    project: project_service):
    if user is None:
        return RedirectResponse("http://127.0.0.1:8002/auth")
    projects = await project.get_projects_by_user_id(user['id'])
    context = {
        "request": request,
        "user": user,
        "projects": projects
    }

    return JSONResponse(context)


if __name__ == "__main__":
    uvicorn.run(socketio_app, host='127.0.0.1', port=8000)