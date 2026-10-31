from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.esquemas.movimientos import (
    CatalogosSalida,
    HistorialSalida,
    MovimientoEntrada,
    MovimientoSalida,
    ResultadoValidacionSalida,
)
from app.modelos.categoria import Categoria
from app.modelos.enums import TipoMovimiento
from app.modelos.medio_pago import MedioPago
from app.modelos.movimiento import Movimiento
from app.modelos.origen import Origen
from app.modelos.usuario import Usuario
from app.servicios.reloj import Reloj
from app.servicios.validacion import validar, validar_campos


def obtener_catalogos(sesion: Session) -> CatalogosSalida:
    categorias = sesion.execute(select(Categoria).order_by(Categoria.nombre)).scalars().all()
    medios_pago = sesion.execute(select(MedioPago).order_by(MedioPago.nombre)).scalars().all()
    origenes = sesion.execute(select(Origen).order_by(Origen.nombre)).scalars().all()
    return CatalogosSalida(categorias=categorias, medios_pago=medios_pago, origenes=origenes)


def _ids_validos(sesion: Session) -> tuple[set[int], set[int]]:
    categorias_validas = set(sesion.execute(select(Categoria.id)).scalars().all())
    medios_pago_validos = set(sesion.execute(select(MedioPago.id)).scalars().all())
    return categorias_validas, medios_pago_validos


def _movimientos_existentes(sesion: Session, usuario: Usuario) -> list[tuple]:
    filas = sesion.execute(
        select(Movimiento.fecha, Movimiento.monto, Movimiento.descripcion).where(
            Movimiento.usuario_id == usuario.id
        )
    ).all()
    return [(fecha, monto, descripcion) for fecha, monto, descripcion in filas]


def validar_borrador(
    sesion: Session, usuario: Usuario, datos: MovimientoEntrada, reloj: Reloj
) -> ResultadoValidacionSalida:
    categorias_validas, medios_pago_validos = _ids_validos(sesion)
    existentes = _movimientos_existentes(sesion, usuario)
    resultado = validar(
        monto=datos.monto,
        fecha=datos.fecha,
        descripcion=datos.descripcion,
        categoria_id=datos.categoria_id,
        medio_pago_id=datos.medio_pago_id,
        hoy=reloj.ahora().date(),
        categorias_validas=categorias_validas,
        medios_pago_validos=medios_pago_validos,
        existentes=existentes,
    )
    return ResultadoValidacionSalida(errores=resultado.errores, advertencias=resultado.advertencias)


def guardar_movimientos(
    sesion: Session, usuario: Usuario, datos: list[MovimientoEntrada], reloj: Reloj
) -> list[MovimientoSalida]:
    categorias_validas, medios_pago_validos = _ids_validos(sesion)
    hoy = reloj.ahora().date()

    for item in datos:
        errores = validar_campos(
            item.monto,
            item.fecha,
            item.categoria_id,
            item.medio_pago_id,
            hoy,
            categorias_validas,
            medios_pago_validos,
        )
        if errores:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={"mensaje": "Hay movimientos con datos invalidos.", "errores": errores},
            )

    origenes_por_nombre = {o.nombre: o.id for o in sesion.execute(select(Origen)).scalars().all()}

    movimientos_creados = []
    for item in datos:
        movimiento = Movimiento(
            usuario_id=usuario.id,
            monto=item.monto,
            fecha=item.fecha,
            tipo=item.tipo,
            descripcion=item.descripcion,
            categoria_id=item.categoria_id,
            medio_pago_id=item.medio_pago_id,
            origen_id=origenes_por_nombre[item.origen],
            conversacion_id=item.conversacion_id,
            comprobante_id=item.comprobante_id,
            cuota_numero=item.cuota_numero,
            cuota_total=item.cuota_total,
        )
        sesion.add(movimiento)
        movimientos_creados.append(movimiento)

    sesion.flush()
    for movimiento in movimientos_creados:
        sesion.refresh(movimiento)
    sesion.commit()

    return [MovimientoSalida.model_validate(m) for m in movimientos_creados]


def listar_movimientos(
    sesion: Session,
    usuario: Usuario,
    desde: date | None,
    hasta: date | None,
    categoria_id: int | None,
    tipo: TipoMovimiento | None,
    medio_pago_id: int | None,
    q: str | None,
    pagina: int,
    por_pagina: int,
) -> HistorialSalida:
    raise NotImplementedError
