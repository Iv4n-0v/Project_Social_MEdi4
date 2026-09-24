from fastapi import FastAPI

from services.analysis_service.database import create_tables
from services.analysis_service.routers.analysis import router


app = FastAPI(
    title="Analysis Service"
)


@app.on_event("startup")
def startup():
    create_tables()


app.include_router(router)