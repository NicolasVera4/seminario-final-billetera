from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(title="Qash")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origenes.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
