from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modelos.categoria import Categoria
from app.modelos.movimiento import Movimiento
from app.servicios.analisis import MovimientoAnalisis


def obtener_movimientos_analisis(
    sesion: Session, usuario_id: int, desde: date | None = None, hasta: date | None = None
) -> list[MovimientoAnalisis]:
    """Trae los movimientos de un usuario (con el nombre de categoria resuelto) listos
    para las funciones puras de analisis.py. `desde`/`hasta` son inclusivos."""
    consulta = (
        select(Movimiento, Categoria.nombre)
        .outerjoin(Categoria, Movimiento.categoria_id == Categoria.id)
        .where(Movimiento.usuario_id == usuario_id)
    )
    if desde is not None:
        consulta = consulta.where(Movimiento.fecha >= desde)
    if hasta is not None:
        consulta = consulta.where(Movimiento.fecha <= hasta)

    filas = sesion.execute(consulta).all()
    return [
        MovimientoAnalisis(
            fecha=movimiento.fecha,
            tipo=movimiento.tipo,
            categoria=nombre_categoria,
            categoria_id=movimiento.categoria_id,
            monto=movimiento.monto,
        )
        for movimiento, nombre_categoria in filas
    ]
