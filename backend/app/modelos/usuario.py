from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.modelos.enums import RolUsuario


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    correo: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    contrasena_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[RolUsuario] = mapped_column(
        Enum(RolUsuario, name="rol_usuario"), default=RolUsuario.USUARIO, nullable=False
    )
    intentos_fallidos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bloqueado_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
