import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles

from src.project.auth_service.routers.auth import router as auth
from src.shared.config import origins, get_middleware_secret

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=get_middleware_secret())

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get('/')
async def redirect():
    return RedirectResponse('/auth')


if __name__ == "__main__":
    uvicorn.run(app, host='127.0.0.1', port=8002)