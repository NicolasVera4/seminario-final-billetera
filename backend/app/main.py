from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.rutas import admin, archivos, auth, catalogos, chat, dashboard, movimientos, salud, voz

app = FastAPI(title="Qash")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origenes.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(salud.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(movimientos.router, prefix="/api")
app.include_router(catalogos.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(archivos.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(voz.router, prefix="/api")
