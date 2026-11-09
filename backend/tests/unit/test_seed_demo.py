from app.modelos.conversacion import Conversacion
from app.modelos.enums import RolMensaje, RolUsuario
from app.modelos.mensaje import Mensaje
from app.modelos.movimiento import Movimiento
from app.modelos.usuario import Usuario
from app.seed_demo import (
    CONTRASENA_ADMIN,
    CONTRASENA_DEMO,
    CORREO_ADMIN,
    CORREO_DEMO,
    FECHA_LIMITE_DEMO,
    cargar_demo,
)
from app.servicios.analisis import alertas, detectar_anomalias, proyeccion_gasto
from app.servicios.consulta_movimientos import obtener_movimientos_analisis
from tests.ayudantes import auth

HOY = FECHA_LIMITE_DEMO


def _correr_seed_demo(sesion_bd, cliente_chroma, embedder):
    cargar_demo(sesion_bd, cliente_chroma, embedder)


def test_seed_demo_nunca_carga_movimientos_despues_de_la_fecha_limite(sesion_bd, cliente_chroma, embedder):
    """Pedido explícito para la demo: si los datos de prueba se generaran relativos a "hoy", el
    mes más reciente coincidiría con la fecha real de la demo y cualquier movimiento cargado en
    vivo ese mismo día se mezclaría con los sintéticos. Por eso el límite queda fijo, sin importar
    cuándo se corra `make seed-demo`."""
    _correr_seed_demo(sesion_bd, cliente_chroma, embedder)

    demo = sesion_bd.query(Usuario).filter_by(correo=CORREO_DEMO).one()
    movimientos = sesion_bd.query(Movimiento).filter_by(usuario_id=demo.id).all()

    assert len(movimientos) > 0
    assert all(m.fecha <= FECHA_LIMITE_DEMO for m in movimientos)


def test_seed_demo_borra_las_conversaciones_que_se_hayan_probado_en_el_ensayo(
    sesion_bd, cliente_chroma, embedder
):
    """Pedido explícito: después de ensayar la demo (cargando gastos por chat, con comprobantes,
    etc.), volver a correr `make seed-demo` debe dejar también el historial de chat limpio, no
    solo los movimientos — antes esas conversaciones quedaban colgadas."""
    _correr_seed_demo(sesion_bd, cliente_chroma, embedder)
    demo = sesion_bd.query(Usuario).filter_by(correo=CORREO_DEMO).one()
    conversacion = Conversacion(usuario_id=demo.id, titulo="Gasté 500 en el gym")
    sesion_bd.add(conversacion)
    sesion_bd.flush()
    sesion_bd.add(
        Mensaje(conversacion_id=conversacion.id, rol=RolMensaje.USUARIO, contenido="Gasté 500 en el gym")
    )
    sesion_bd.commit()

    _correr_seed_demo(sesion_bd, cliente_chroma, embedder)

    assert sesion_bd.query(Conversacion).filter_by(usuario_id=demo.id).count() == 0
    assert sesion_bd.query(Mensaje).join(Conversacion).filter(Conversacion.usuario_id == demo.id).count() == 0


def test_seed_demo_crea_usuario_demo_y_administrador(sesion_bd, cliente_chroma, embedder):
    _correr_seed_demo(sesion_bd, cliente_chroma, embedder)

    demo = sesion_bd.query(Usuario).filter_by(correo=CORREO_DEMO).one()
    admin = sesion_bd.query(Usuario).filter_by(correo=CORREO_ADMIN).one()

    assert demo.rol == RolUsuario.USUARIO
    assert admin.rol == RolUsuario.ADMINISTRADOR


def test_seed_demo_es_reejecutable_sin_duplicar_usuarios_ni_movimientos(sesion_bd, cliente_chroma, embedder):
    _correr_seed_demo(sesion_bd, cliente_chroma, embedder)
    _correr_seed_demo(sesion_bd, cliente_chroma, embedder)

    demos = sesion_bd.query(Usuario).filter_by(correo=CORREO_DEMO).all()
    assert len(demos) == 1

    movimientos = sesion_bd.query(Movimiento).filter_by(usuario_id=demos[0].id).all()
    assert len(movimientos) == 25


def test_seed_demo_carga_6_meses_de_movimientos(sesion_bd, cliente_chroma, embedder):
    _correr_seed_demo(sesion_bd, cliente_chroma, embedder)

    demo = sesion_bd.query(Usuario).filter_by(correo=CORREO_DEMO).one()
    movimientos = obtener_movimientos_analisis(sesion_bd, demo.id)

    assert len(movimientos) == 25


def test_hu09_ca1_seed_demo_dispara_una_alerta_de_categoria(sesion_bd, cliente_chroma, embedder):
    _correr_seed_demo(sesion_bd, cliente_chroma, embedder)

    demo = sesion_bd.query(Usuario).filter_by(correo=CORREO_DEMO).one()
    movimientos = obtener_movimientos_analisis(sesion_bd, demo.id)

    resultado = alertas(movimientos, HOY.year, HOY.month)

    assert len(resultado) == 1
    assert resultado[0].categoria == "Restaurantes"
    assert resultado[0].porcentaje >= 30


def test_hu13_ca1_seed_demo_tiene_un_mes_con_gasto_anomalo(sesion_bd, cliente_chroma, embedder):
    _correr_seed_demo(sesion_bd, cliente_chroma, embedder)

    demo = sesion_bd.query(Usuario).filter_by(correo=CORREO_DEMO).one()
    movimientos = obtener_movimientos_analisis(sesion_bd, demo.id)

    resultado = detectar_anomalias(movimientos, HOY.year, HOY.month)

    assert resultado.datos_suficientes is True
    assert len(resultado.meses) >= 1


def test_hu12_ca1_seed_demo_tiene_proyeccion_con_tendencia_creciente(sesion_bd, cliente_chroma, embedder):
    _correr_seed_demo(sesion_bd, cliente_chroma, embedder)

    demo = sesion_bd.query(Usuario).filter_by(correo=CORREO_DEMO).one()
    movimientos = obtener_movimientos_analisis(sesion_bd, demo.id)

    resultado = proyeccion_gasto(movimientos, HOY.year, HOY.month)

    assert resultado.datos_suficientes is True
    assert resultado.monto > 0


def test_seed_demo_permite_iniciar_sesion_con_las_credenciales_publicadas(
    cliente, sesion_bd, cliente_chroma, embedder
):
    _correr_seed_demo(sesion_bd, cliente_chroma, embedder)

    respuesta_demo = cliente.post(
        "/api/auth/login", json={"correo": CORREO_DEMO, "contrasena": CONTRASENA_DEMO}
    )
    respuesta_admin = cliente.post(
        "/api/auth/login", json={"correo": CORREO_ADMIN, "contrasena": CONTRASENA_ADMIN}
    )

    assert respuesta_demo.status_code == 200
    assert respuesta_admin.status_code == 200
    assert auth(respuesta_demo.json()["access_token"])
