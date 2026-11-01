from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.esquemas.chat import ChatEntrada, ChatSalida, MensajeSalida
from app.esquemas.movimientos import BorradorMovimientoSalida, Catalogo
from app.modelos.categoria import Categoria
from app.modelos.conversacion import Conversacion
from app.modelos.enums import RolMensaje
from app.modelos.medio_pago import MedioPago
from app.modelos.mensaje import Mensaje
from app.modelos.usuario import Usuario
from app.proveedores.llm import ErrorInterpretacion, ProveedorLLM
from app.servicios.reloj import Reloj

MENSAJE_FALTA_MONTO = "Me falta el monto. ¿Cuánto fue?"
MENSAJE_MOVIMIENTO_INTERPRETADO = "Encontré este movimiento, revisalo y confirmalo."
MENSAJE_ERROR_INTERPRETACION = "No pude entender ese mensaje. ¿Podés reformularlo?"
CANTIDAD_MENSAJES_HISTORIAL = 10


def procesar_mensaje(
    sesion: Session,
    usuario: Usuario,
    proveedor_llm: ProveedorLLM,
    reloj: Reloj,
    datos: ChatEntrada,
) -> ChatSalida:
    conversacion = _obtener_o_crear_conversacion(sesion, usuario, datos)
    _guardar_mensaje(sesion, conversacion, RolMensaje.USUARIO, datos.texto)

    categorias, medios_pago, catalogo = obtener_catalogo(sesion)
    hoy = reloj.ahora().date()

    borrador = None
    try:
        interpretacion = proveedor_llm.clasificar_e_interpretar(datos.texto, hoy, catalogo)
    except ErrorInterpretacion:
        texto_respuesta = MENSAJE_ERROR_INTERPRETACION
    else:
        movimiento = interpretacion.movimiento
        es_registro_completo = (
            interpretacion.intencion == "REGISTRO"
            and movimiento is not None
            and movimiento.monto is not None
            and "monto" not in interpretacion.faltantes
        )
        if es_registro_completo:
            categoria_id, categoria_sugerida = resolver_categoria(categorias, movimiento.categoria)
            medio_pago_id = resolver_medio_pago(medios_pago, movimiento.medio_pago)
            borrador = BorradorMovimientoSalida(
                monto=movimiento.monto,
                fecha=movimiento.fecha or hoy,
                tipo=movimiento.tipo,
                descripcion=movimiento.descripcion or datos.texto,
                categoria_id=categoria_id,
                categoria_sugerida=categoria_sugerida,
                medio_pago_id=medio_pago_id,
            )
            texto_respuesta = MENSAJE_MOVIMIENTO_INTERPRETADO
        elif interpretacion.intencion == "REGISTRO":
            texto_respuesta = MENSAJE_FALTA_MONTO
        else:
            historial = _ultimos_mensajes(sesion, conversacion, CANTIDAD_MENSAJES_HISTORIAL)
            texto_respuesta = proveedor_llm.responder(datos.texto, None, [], historial)

    mensaje_asistente = _guardar_mensaje(sesion, conversacion, RolMensaje.ASISTENTE, texto_respuesta)
    sesion.commit()

    return ChatSalida(
        conversacion_id=conversacion.id,
        mensaje=MensajeSalida.model_validate(mensaje_asistente),
        borrador=borrador,
    )


def obtener_catalogo(sesion: Session) -> tuple[list[Categoria], list[MedioPago], Catalogo]:
    categorias = sesion.execute(select(Categoria)).scalars().all()
    medios_pago = sesion.execute(select(MedioPago)).scalars().all()
    catalogo = Catalogo(
        categorias=[c.nombre for c in categorias],
        medios_pago=[m.nombre for m in medios_pago],
    )
    return categorias, medios_pago, catalogo


def resolver_categoria(categorias: list[Categoria], nombre: str | None) -> tuple[int | None, str | None]:
    """Devuelve (categoria_id, categoria_sugerida). Si nombre no esta en el catalogo, categoria_id es None."""
    if not nombre:
        return None, None
    nombre_normalizado = nombre.strip().lower()
    for categoria in categorias:
        if categoria.nombre.strip().lower() == nombre_normalizado:
            return categoria.id, None
    return None, nombre


def resolver_medio_pago(medios_pago: list[MedioPago], nombre: str | None) -> int | None:
    """Devuelve el id del medio de pago, o None si esta ausente o no esta en el catalogo."""
    if not nombre:
        return None
    nombre_normalizado = nombre.strip().lower()
    for medio in medios_pago:
        if medio.nombre.strip().lower() == nombre_normalizado:
            return medio.id
    return None


def _obtener_o_crear_conversacion(sesion: Session, usuario: Usuario, datos: ChatEntrada) -> Conversacion:
    if datos.conversacion_id is not None:
        conversacion = sesion.get(Conversacion, datos.conversacion_id)
        if conversacion is None or conversacion.usuario_id != usuario.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversación no encontrada."
            )
        return conversacion

    titulo = datos.texto.strip()[:40] or None
    conversacion = Conversacion(usuario_id=usuario.id, titulo=titulo)
    sesion.add(conversacion)
    sesion.flush()
    return conversacion


def _guardar_mensaje(sesion: Session, conversacion: Conversacion, rol: RolMensaje, contenido: str) -> Mensaje:
    mensaje = Mensaje(conversacion_id=conversacion.id, rol=rol, contenido=contenido)
    sesion.add(mensaje)
    sesion.flush()
    sesion.refresh(mensaje)
    return mensaje


def _ultimos_mensajes(sesion: Session, conversacion: Conversacion, limite: int) -> list[Mensaje]:
    mensajes = sesion.execute(
        select(Mensaje)
        .where(Mensaje.conversacion_id == conversacion.id)
        .order_by(Mensaje.creado_en.desc())
        .limit(limite)
    ).scalars().all()
    return list(reversed(mensajes))
