from datetime import timedelta

from tests.ayudantes import loguear, registrar

MENSAJE_ERROR_LOGIN = "El correo o la contraseña no son correctos."


def test_hu02_ca1_mensaje_unico_correo_inexistente(cliente):
    respuesta = loguear(cliente, correo="no-existe@mail.com", contrasena="cualquiera123")

    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == MENSAJE_ERROR_LOGIN


def test_hu02_ca1_mensaje_unico_contrasena_incorrecta(cliente):
    registrar(cliente)

    respuesta = loguear(cliente, contrasena="incorrecta123")

    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == MENSAJE_ERROR_LOGIN


def test_hu02_ca2_datos_correctos_devuelve_token(cliente):
    registrar(cliente)

    respuesta = loguear(cliente)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["token_type"] == "bearer"
    assert cuerpo["access_token"]


def test_bloqueo_tras_5_fallos_consecutivos(cliente):
    registrar(cliente)

    for _ in range(5):
        respuesta = loguear(cliente, contrasena="mala")

    assert respuesta.status_code in (401, 423)

    respuesta_bloqueada = loguear(cliente)
    assert respuesta_bloqueada.status_code == 423


def test_desbloqueo_a_los_15_minutos(cliente, reloj):
    registrar(cliente)

    for _ in range(5):
        loguear(cliente, contrasena="mala")

    reloj.avanzar(timedelta(minutes=15, seconds=1))

    respuesta = loguear(cliente)

    assert respuesta.status_code == 200


def test_reset_del_contador_tras_login_exitoso(cliente, reloj):
    registrar(cliente)

    for _ in range(4):
        loguear(cliente, contrasena="mala")

    exitoso = loguear(cliente)
    assert exitoso.status_code == 200

    for _ in range(4):
        loguear(cliente, contrasena="mala")

    aun_no_bloqueada = loguear(cliente)
    assert aun_no_bloqueada.status_code == 200
