from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.modelos.enums import TipoComprobante


class Comprobante(Base):
    __tablename__ = "comprobantes"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)
    tipo: Mapped[TipoComprobante] = mapped_column(
        Enum(TipoComprobante, name="tipo_comprobante"), nullable=False
    )
    ruta_archivo: Mapped[str] = mapped_column(String(500), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
