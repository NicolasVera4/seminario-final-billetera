from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class DocumentoReferencia(Base):
    __tablename__ = "documentos_referencia"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    cantidad_fragmentos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
