from datetime import UTC, datetime, timedelta

from app.esquemas.movimientos import Interpretacion
from app.modelos.usuario import Usuario
from tests.ayudantes import auth, id_usuario, promover_a_administrador, registrar_y_loguear


def _token_admin(cliente, sesion_bd, correo="admin@mail.com"):
    registrar_y_loguear(cliente, nombre="Admin", correo=correo)
    promover_a_administrador(sesion_bd, correo)
    return cliente.post("/api/auth/login", json={"correo": correo, "contrasena": "contrasena123"}).json()[
        "access_token"
    ]


def test_listar_documentos_requiere_rol_administrador(cliente):
    token = registrar_y_loguear(cliente)

    respuesta = cliente.get("/api/admin/documentos", headers=auth(token))

    assert respuesta.status_code == 403


def test_cargar_documento_requiere_rol_administrador(cliente):
    token = registrar_y_loguear(cliente)

    respuesta = cliente.post(
        "/api/admin/documentos",
        params={"titulo": "Tips"},
        files={"archivo": ("tips.txt", b"contenido", "text/plain")},
        headers=auth(token),
    )

    assert respuesta.status_code == 403


def test_admin_carga_un_documento_de_texto(cliente, sesion_bd):
    token = _token_admin(cliente, sesion_bd)

    respuesta = cliente.post(
        "/api/admin/documentos",
        params={"titulo": "Tips de ahorro"},
        files={"archivo": ("tips.txt", "a" * 1700, "text/plain")},
        headers=auth(token),
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["titulo"] == "Tips de ahorro"
    assert cuerpo["cantidad_fragmentos"] >= 2


def test_admin_lista_los_documentos_cargados(cliente, sesion_bd):
    token = _token_admin(cliente, sesion_bd)
    cliente.post(
        "/api/admin/documentos",
        params={"titulo": "Tips"},
        files={"archivo": ("tips.txt", b"contenido breve", "text/plain")},
        headers=auth(token),
    )

    respuesta = cliente.get("/api/admin/documentos", headers=auth(token))

    assert respuesta.status_code == 200
    assert len(respuesta.json()) == 1
    assert respuesta.json()[0]["titulo"] == "Tips"


def test_admin_elimina_un_documento(cliente, sesion_bd):
    token = _token_admin(cliente, sesion_bd)
    creado = cliente.post(
        "/api/admin/documentos",
        params={"titulo": "Tips"},
        files={"archivo": ("tips.txt", b"contenido breve", "text/plain")},
        headers=auth(token),
    )
    documento_id = creado.json()["id"]

    respuesta = cliente.delete(f"/api/admin/documentos/{documento_id}", headers=auth(token))

    assert respuesta.status_code == 204
    assert cliente.get("/api/admin/documentos", headers=auth(token)).json() == []


def test_admin_desbloquea_un_usuario(cliente, sesion_bd):
    token_admin = _token_admin(cliente, sesion_bd)
    registrar_y_loguear(cliente, nombre="Usuaria A", correo="a@mail.com")

    usuario = sesion_bd.get(Usuario, id_usuario(sesion_bd, "a@mail.com"))
    usuario.intentos_fallidos = 5
    usuario.bloqueado_hasta = datetime.now(UTC) + timedelta(minutes=15)
    sesion_bd.flush()

    respuesta = cliente.patch(
        f"/api/admin/usuarios/{usuario.id}", json={"desbloquear": True}, headers=auth(token_admin)
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["bloqueado_hasta"] is None


def test_admin_da_de_baja_un_usuario(cliente, sesion_bd):
    token_admin = _token_admin(cliente, sesion_bd)
    registrar_y_loguear(cliente, nombre="Usuaria A", correo="a@mail.com")
    usuario_id = id_usuario(sesion_bd, "a@mail.com")

    respuesta = cliente.patch(
        f"/api/admin/usuarios/{usuario_id}", json={"activo": False}, headers=auth(token_admin)
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["activo"] is False


def test_editar_usuario_requiere_rol_administrador(cliente):
    token = registrar_y_loguear(cliente)

    respuesta = cliente.patch("/api/admin/usuarios/1", json={"activo": False}, headers=auth(token))

    assert respuesta.status_code == 403


def test_admin_no_puede_ver_movimientos(cliente, sesion_bd):
    token_admin = _token_admin(cliente, sesion_bd)

    respuesta = cliente.get("/api/movimientos", headers=auth(token_admin))

    assert respuesta.status_code == 403


def test_admin_no_puede_ver_el_dashboard(cliente, sesion_bd):
    token_admin = _token_admin(cliente, sesion_bd)

    respuesta = cliente.get("/api/dashboard", headers=auth(token_admin))

    assert respuesta.status_code == 403


def test_admin_no_puede_usar_el_chat(cliente, sesion_bd, proveedor_llm):
    token_admin = _token_admin(cliente, sesion_bd)
    proveedor_llm.respuesta_clasificar = Interpretacion(intencion="CONSULTA_DATOS", movimiento=None, faltantes=[])

    respuesta = cliente.post("/api/chat/mensajes", json={"texto": "hola"}, headers=auth(token_admin))

    assert respuesta.status_code == 403
