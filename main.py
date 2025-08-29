from contextlib import asynccontextmanager
from src.db.db_config import init_db
from fastapi import FastAPI
from src.app import endpoints


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(endpoints.router)
