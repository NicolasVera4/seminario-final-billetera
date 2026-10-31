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
