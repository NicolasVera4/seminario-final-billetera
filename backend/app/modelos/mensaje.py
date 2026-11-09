from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.modelos.enums import RolMensaje


class Mensaje(Base):
    __tablename__ = "mensajes"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversacion_id: Mapped[int] = mapped_column(
        ForeignKey("conversaciones.id"), nullable=False, index=True
    )
    rol: Mapped[RolMensaje] = mapped_column(Enum(RolMensaje, name="rol_mensaje"), nullable=False)
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    fuentes: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    transcripto: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
