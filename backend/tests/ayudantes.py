NOMBRE_DEFECTO = "Luciano Vera"
CORREO_DEFECTO = "luciano.vera@mail.com"
CONTRASENA_DEFECTO = "contrasena123"


def datos_registro(nombre=NOMBRE_DEFECTO, correo=CORREO_DEFECTO, contrasena=CONTRASENA_DEFECTO):
    return {"nombre": nombre, "correo": correo, "contrasena": contrasena}


def registrar(cliente, nombre=NOMBRE_DEFECTO, correo=CORREO_DEFECTO, contrasena=CONTRASENA_DEFECTO):
    return cliente.post("/api/auth/registro", json=datos_registro(nombre, correo, contrasena))


def loguear(cliente, correo=CORREO_DEFECTO, contrasena=CONTRASENA_DEFECTO):
    return cliente.post("/api/auth/login", json={"correo": correo, "contrasena": contrasena})


def registrar_y_loguear(cliente, nombre=NOMBRE_DEFECTO, correo=CORREO_DEFECTO, contrasena=CONTRASENA_DEFECTO):
    registrar(cliente, nombre, correo, contrasena)
    return loguear(cliente, correo, contrasena).json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def id_categoria(sesion, nombre):
    from app.modelos.categoria import Categoria

    return sesion.query(Categoria).filter_by(nombre=nombre).one().id


def id_medio_pago(sesion, nombre):
    from app.modelos.medio_pago import MedioPago

    return sesion.query(MedioPago).filter_by(nombre=nombre).one().id


def id_origen(sesion, nombre):
    from app.modelos.origen import Origen

    return sesion.query(Origen).filter_by(nombre=nombre).one().id


def id_usuario(sesion, correo=CORREO_DEFECTO):
    from app.modelos.usuario import Usuario

    return sesion.query(Usuario).filter_by(correo=correo).one().id


def crear_movimiento(
    sesion,
    usuario_id,
    monto="1000",
    fecha=None,
    tipo="EGRESO",
    descripcion="Movimiento de prueba",
    categoria="Otros",
    medio_pago="Efectivo",
    origen="Texto",
):
    from datetime import date
    from decimal import Decimal

    from app.modelos.movimiento import Movimiento

    movimiento = Movimiento(
        usuario_id=usuario_id,
        monto=Decimal(monto),
        fecha=fecha or date(2026, 10, 31),
        tipo=tipo,
        descripcion=descripcion,
        categoria_id=id_categoria(sesion, categoria) if categoria else None,
        medio_pago_id=id_medio_pago(sesion, medio_pago) if medio_pago else None,
        origen_id=id_origen(sesion, origen),
    )
    sesion.add(movimiento)
    sesion.flush()
    sesion.refresh(movimiento)
    return movimiento
