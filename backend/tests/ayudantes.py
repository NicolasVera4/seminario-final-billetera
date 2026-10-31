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
