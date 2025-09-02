from fastapi import FastAPI
from src.app import endpoints

app = FastAPI()

app.include_router(endpoints.router)
