from datetime import timedelta

MENSAJE_ERROR_LOGIN = "El correo o la contraseña no son correctos."


def _registrar(cliente, correo="luciano.vera@mail.com", contrasena="contrasena123"):
    cliente.post(
        "/api/auth/registro",
        json={"nombre": "Luciano Vera", "correo": correo, "contrasena": contrasena},
    )


def test_hu02_ca1_mensaje_unico_correo_inexistente(cliente):
    respuesta = cliente.post(
        "/api/auth/login", json={"correo": "no-existe@mail.com", "contrasena": "cualquiera123"}
    )

    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == MENSAJE_ERROR_LOGIN


def test_hu02_ca1_mensaje_unico_contrasena_incorrecta(cliente):
    _registrar(cliente)

    respuesta = cliente.post(
        "/api/auth/login", json={"correo": "luciano.vera@mail.com", "contrasena": "incorrecta123"}
    )

    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == MENSAJE_ERROR_LOGIN


def test_hu02_ca2_datos_correctos_devuelve_token(cliente):
    _registrar(cliente)

    respuesta = cliente.post(
        "/api/auth/login", json={"correo": "luciano.vera@mail.com", "contrasena": "contrasena123"}
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["token_type"] == "bearer"
    assert cuerpo["access_token"]


def test_bloqueo_tras_5_fallos_consecutivos(cliente):
    _registrar(cliente)

    for _ in range(5):
        respuesta = cliente.post(
            "/api/auth/login", json={"correo": "luciano.vera@mail.com", "contrasena": "mala"}
        )

    assert respuesta.status_code in (401, 423)

    respuesta_bloqueada = cliente.post(
        "/api/auth/login", json={"correo": "luciano.vera@mail.com", "contrasena": "contrasena123"}
    )
    assert respuesta_bloqueada.status_code == 423


def test_desbloqueo_a_los_15_minutos(cliente, reloj):
    _registrar(cliente)

    for _ in range(5):
        cliente.post("/api/auth/login", json={"correo": "luciano.vera@mail.com", "contrasena": "mala"})

    reloj.avanzar(timedelta(minutes=15, seconds=1))

    respuesta = cliente.post(
        "/api/auth/login", json={"correo": "luciano.vera@mail.com", "contrasena": "contrasena123"}
    )

    assert respuesta.status_code == 200


def test_reset_del_contador_tras_login_exitoso(cliente, reloj):
    _registrar(cliente)

    for _ in range(4):
        cliente.post("/api/auth/login", json={"correo": "luciano.vera@mail.com", "contrasena": "mala"})

    exitoso = cliente.post(
        "/api/auth/login", json={"correo": "luciano.vera@mail.com", "contrasena": "contrasena123"}
    )
    assert exitoso.status_code == 200

    for _ in range(4):
        cliente.post("/api/auth/login", json={"correo": "luciano.vera@mail.com", "contrasena": "mala"})

    aun_no_bloqueada = cliente.post(
        "/api/auth/login", json={"correo": "luciano.vera@mail.com", "contrasena": "contrasena123"}
    )
    assert aun_no_bloqueada.status_code == 200
