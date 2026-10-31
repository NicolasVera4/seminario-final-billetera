from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class MedioPago(Base):
    __tablename__ = "medios_pago"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
