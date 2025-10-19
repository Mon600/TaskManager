import uvicorn
from fastapi import FastAPI
from src.project.statistics_service.routers.statistic_router import router as stat

app = FastAPI()

app.include_router(stat)


if __name__ == "__main__":
    uvicorn.run(app, port=8003)