from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(settings.database_url)
SesionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def obtener_sesion() -> Session:
    sesion = SesionLocal()
    try:
        yield sesion
    finally:
        sesion.close()
