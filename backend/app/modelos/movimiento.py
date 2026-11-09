from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.modelos.enums import TipoMovimiento


class Movimiento(Base):
    __tablename__ = "movimientos"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)
    monto: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    tipo: Mapped[TipoMovimiento] = mapped_column(
        Enum(TipoMovimiento, name="tipo_movimiento"), nullable=False
    )
    descripcion: Mapped[str] = mapped_column(String(500), nullable=False)
    moneda: Mapped[str] = mapped_column(String(3), default="ARS", nullable=False)

    categoria_id: Mapped[int | None] = mapped_column(ForeignKey("categorias.id"), nullable=True)
    categoria_sugerida: Mapped[str | None] = mapped_column(String(100), nullable=True)
    medio_pago_id: Mapped[int | None] = mapped_column(ForeignKey("medios_pago.id"), nullable=True)
    origen_id: Mapped[int] = mapped_column(ForeignKey("origenes.id"), nullable=False)
    comprobante_id: Mapped[int | None] = mapped_column(ForeignKey("comprobantes.id"), nullable=True)
    conversacion_id: Mapped[int | None] = mapped_column(
        ForeignKey("conversaciones.id"), nullable=True
    )
    mensaje_id: Mapped[int | None] = mapped_column(ForeignKey("mensajes.id"), nullable=True)

    cuota_numero: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cuota_total: Mapped[int | None] = mapped_column(Integer, nullable=True)

    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
