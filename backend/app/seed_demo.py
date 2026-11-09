from datetime import date
from decimal import Decimal

from app.db import SesionLocal
from app.esquemas.auth import RegistroEntrada
from app.modelos.categoria import Categoria
from app.modelos.conversacion import Conversacion
from app.modelos.enums import RolUsuario, TipoMovimiento
from app.modelos.medio_pago import MedioPago
from app.modelos.mensaje import Mensaje
from app.modelos.movimiento import Movimiento
from app.modelos.origen import Origen
from app.modelos.usuario import Usuario
from app.seed import cargar_catalogos, cargar_documentos_referencia
from app.servicios.analisis import mes_anterior
from app.servicios.auth import registrar_usuario

CORREO_DEMO = "nicolas.vera@gmail.com"
CONTRASENA_DEMO = "UsuarioDemo2026"
CORREO_ADMIN = "nicolas.vera+admin@gmail.com"
CONTRASENA_ADMIN = "AdminDemo2026"

# Fija (no la fecha real de hoy) a propósito: si se generara relativa a "hoy", el mes más
# reciente de los datos de prueba sería el mes en curso el día de la demo — y cualquier
# movimiento que se cargue en vivo durante la demo (con fecha de ese mismo día) se mezclaría con
# los datos sinteticos del mes actual. Dejando el límite fijo en octubre, lo que se cargue en
# vivo (noviembre en adelante) queda siempre separado de los datos de prueba.
FECHA_LIMITE_DEMO = date(2026, 10, 31)

# Cantidades calibradas (ver docs/PLAN.md, Fase 12) para que, en el mes actual (indice 5, el mas
# reciente), se disparen a la vez: HU-09 (Restaurantes supera 30% su promedio de los 3 meses
# previos), HU-13 (el mes con la compra puntual de Indumentaria queda marcado como anomalo) y
# HU-12 (la serie de egresos totales muestra una tendencia creciente).
SUPERMERCADO = [40000, 43000, 46000, 49000, 52000, 55000]
TRANSPORTE = [8000] * 6
RESTAURANTES = [8000, 9000, 10000, 11000, 9000, 16000]
SUELDO = [250000] * 6
INDUMENTARIA_EXTRA = {3: 40000}  # 3 meses antes del actual: compra puntual grande -> mes anomalo


def _crear_usuario_si_falta(
    sesion, nombre: str, correo: str, contrasena: str, rol: RolUsuario = RolUsuario.USUARIO
) -> Usuario:
    usuario = sesion.query(Usuario).filter_by(correo=correo).one_or_none()
    if usuario is not None:
        return usuario
    usuario = registrar_usuario(
        sesion, RegistroEntrada(nombre=nombre, correo=correo, contrasena=contrasena)
    )
    if rol != RolUsuario.USUARIO:
        usuario.rol = rol
        sesion.commit()
    return usuario


def _id_por_nombre(sesion, modelo, nombre: str) -> int:
    return sesion.query(modelo).filter_by(nombre=nombre).one().id


def _meses_hasta_hoy(hoy: date, cantidad: int = 6) -> list[tuple[int, int]]:
    meses = []
    anio, mes = hoy.year, hoy.month
    for _ in range(cantidad):
        meses.append((anio, mes))
        anio, mes = mes_anterior(anio, mes)
    meses.reverse()
    return meses


def _cargar_movimientos_demo(sesion, usuario: Usuario, hoy: date) -> None:
    sesion.query(Movimiento).filter_by(usuario_id=usuario.id).delete()
    sesion.flush()

    origen_id = _id_por_nombre(sesion, Origen, "Texto")
    medio_pago_id = _id_por_nombre(sesion, MedioPago, "Débito")
    categoria_sueldo = _id_por_nombre(sesion, Categoria, "Sueldo")
    categoria_supermercado = _id_por_nombre(sesion, Categoria, "Supermercado")
    categoria_transporte = _id_por_nombre(sesion, Categoria, "Transporte")
    categoria_restaurantes = _id_por_nombre(sesion, Categoria, "Restaurantes")
    categoria_indumentaria = _id_por_nombre(sesion, Categoria, "Indumentaria")

    def _agregar(monto, fecha, tipo, descripcion, categoria_id):
        sesion.add(
            Movimiento(
                usuario_id=usuario.id,
                monto=Decimal(monto),
                fecha=fecha,
                tipo=tipo,
                descripcion=descripcion,
                categoria_id=categoria_id,
                medio_pago_id=medio_pago_id,
                origen_id=origen_id,
            )
        )

    for indice, (anio, mes) in enumerate(_meses_hasta_hoy(hoy)):
        _agregar(SUELDO[indice], date(anio, mes, 1), TipoMovimiento.INGRESO, "Sueldo", categoria_sueldo)
        _agregar(
            SUPERMERCADO[indice], date(anio, mes, 10), TipoMovimiento.EGRESO,
            "Compras del supermercado", categoria_supermercado,
        )
        _agregar(
            TRANSPORTE[indice], date(anio, mes, 12), TipoMovimiento.EGRESO, "Transporte", categoria_transporte
        )
        _agregar(
            RESTAURANTES[indice], date(anio, mes, 15), TipoMovimiento.EGRESO,
            "Restaurantes", categoria_restaurantes,
        )
        if indice in INDUMENTARIA_EXTRA:
            _agregar(
                INDUMENTARIA_EXTRA[indice], date(anio, mes, 20), TipoMovimiento.EGRESO,
                "Compra de indumentaria", categoria_indumentaria,
            )

    sesion.commit()


def _limpiar_conversaciones(sesion, usuario: Usuario) -> None:
    """`make seed-demo` es re-ejecutable y pensado para dejar la cuenta demo en un estado
    limpio — pero solo borraba movimientos. Si en un ensayo se probó el chat (texto, voz,
    comprobantes), esas conversaciones quedaban colgadas de una corrida a la siguiente. Se llama
    después de `_cargar_movimientos_demo` (que ya borró los movimientos del usuario): si se
    llamara antes, borrar un mensaje referenciado por un movimiento todavía vivo violaría la
    foreign key."""
    ids_conversaciones = [
        fila.id for fila in sesion.query(Conversacion.id).filter_by(usuario_id=usuario.id).all()
    ]
    if not ids_conversaciones:
        return
    sesion.query(Mensaje).filter(Mensaje.conversacion_id.in_(ids_conversaciones)).delete(
        synchronize_session=False
    )
    sesion.query(Conversacion).filter(Conversacion.id.in_(ids_conversaciones)).delete(
        synchronize_session=False
    )
    sesion.commit()


def cargar_demo(sesion=None, cliente_chroma=None, embedder=None) -> None:
    from app.proveedores.embeddings import obtener_embedder
    from app.proveedores.vectorial import obtener_cliente_chroma

    sesion_propia = sesion is None
    if sesion_propia:
        sesion = SesionLocal()
    cliente_chroma = cliente_chroma or obtener_cliente_chroma()
    embedder = embedder or obtener_embedder()
    try:
        cargar_catalogos(sesion)
        cargar_documentos_referencia(sesion, cliente_chroma, embedder)
        usuario_demo = _crear_usuario_si_falta(sesion, "Usuario Demo", CORREO_DEMO, CONTRASENA_DEMO)
        _crear_usuario_si_falta(
            sesion, "Administrador", CORREO_ADMIN, CONTRASENA_ADMIN, RolUsuario.ADMINISTRADOR
        )
        _cargar_movimientos_demo(sesion, usuario_demo, FECHA_LIMITE_DEMO)
        _limpiar_conversaciones(sesion, usuario_demo)
    finally:
        if sesion_propia:
            sesion.close()


if __name__ == "__main__":
    cargar_demo()
    print(f"Usuario demo: {CORREO_DEMO} / {CONTRASENA_DEMO}")
    print(f"Administrador: {CORREO_ADMIN} / {CONTRASENA_ADMIN}")
