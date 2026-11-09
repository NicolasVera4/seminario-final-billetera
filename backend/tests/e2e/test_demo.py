"""Recorrido E2E manual de Qash contra la API real (servidor local + Groq + Ollama + Chroma).

No corre en `make test` ni en CI: requiere el servidor en marcha en localhost:8000,
con `make seed-demo` ya ejecutado, y GROQ_API_KEY configurada.

Uso: `QASH_E2E_DOCS=/ruta/a/tus/documentos make test-e2e` (o `pytest tests/e2e/ -m e2e -s`).
`QASH_E2E_DOCS` tiene que apuntar a una carpeta FUERA del repo con los documentos de prueba
(y una subcarpeta `anexo-docs/` con los anonimizados) — no hay un valor por defecto a propósito,
para no dejar una ruta personal fija en el código.

Los documentos de prueba se leen desde esa ruta y nunca se copian ni se suben a ningún lado:
solo se leen sus bytes para mandarlos por HTTP al servidor local. El informe final no reproduce
datos personales (nombres, montos exactos de documentos reales) más allá de lo necesario para
evaluar el comportamiento del sistema.
"""

import os
import time
from pathlib import Path

import httpx
import pytest

pytestmark = pytest.mark.e2e

BASE_URL = "http://localhost:8000/api"

_ruta_docs = os.environ.get("QASH_E2E_DOCS")
if not _ruta_docs:
    pytest.skip(
        "Definí QASH_E2E_DOCS con la ruta a tus documentos de prueba (fuera del repo) para correr este recorrido.",
        allow_module_level=True,
    )
AIRFLOW = Path(_ruta_docs)
ANEXO = AIRFLOW / "anexo-docs"

CORREO_DEMO = "nicolas.vera@gmail.com"
CONTRASENA_DEMO = "UsuarioDemo2026"
CORREO_ADMIN = "nicolas.vera+admin@gmail.com"
CONTRASENA_ADMIN = "AdminDemo2026"

RESULTADOS: list[dict] = []


def registrar(paso: str, esperado: str, obtenido: str, estado: str, inicio: float, observacion: str = "") -> None:
    RESULTADOS.append(
        {
            "paso": paso,
            "esperado": esperado,
            "obtenido": obtenido,
            "estado": estado,
            "tiempo_s": round(time.monotonic() - inicio, 1),
            "observacion": observacion,
        }
    )
    print(f"\n[{estado}] {paso} ({round(time.monotonic() - inicio, 1)}s)\n  esperado: {esperado}\n  obtenido: {obtenido}")
    if observacion:
        print(f"  obs: {observacion}")


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def login(cliente: httpx.Client, correo: str, contrasena: str) -> str:
    r = cliente.post("/auth/login", json={"correo": correo, "contrasena": contrasena})
    r.raise_for_status()
    return r.json()["access_token"]


def subir_archivo(cliente: httpx.Client, ruta: Path, content_type: str, endpoint: str, token: str) -> httpx.Response:
    with ruta.open("rb") as f:
        return cliente.post(
            endpoint,
            files={"archivo": (ruta.name, f, content_type)},
            headers=auth(token),
        )


def escribir_informe() -> None:
    destino = Path(__file__).resolve().parents[3] / "docs" / "resultado_e2e_demo.md"
    lineas = [
        "# Resultado de la prueba E2E — Qash",
        "",
        "Generado automáticamente por `backend/tests/e2e/test_demo.py`. No contiene datos",
        "personales de los documentos de prueba, solo el comportamiento observado del sistema.",
        "",
        "| Paso | Esperado | Obtenido | Estado | Tiempo | Observación |",
        "|---|---|---|---|---|---|",
    ]
    for r in RESULTADOS:
        lineas.append(
            f"| {r['paso']} | {r['esperado']} | {r['obtenido']} | {r['estado']} | {r['tiempo_s']}s | {r['observacion']} |"
        )
    destino.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"\nInforme escrito en {destino}")


def test_recorrido_completo():
    cliente = httpx.Client(base_url=BASE_URL, timeout=180)

    # --- 2. Login + dashboard ---
    t = time.monotonic()
    try:
        token_demo = login(cliente, CORREO_DEMO, CONTRASENA_DEMO)
        registrar("2. Login usuario demo", "200 + access_token", "200 + access_token", "OK", t)
    except Exception as exc:
        registrar("2. Login usuario demo", "200 + access_token", repr(exc), "FALLA", t)
        escribir_informe()
        raise

    t = time.monotonic()
    datos = cliente.get("/dashboard", headers=auth(token_demo)).json()
    alerta_restaurantes = any(a["categoria"] == "Restaurantes" for a in datos.get("alertas", []))
    meses_anomalos = datos.get("anomalias", {}).get("meses", [])
    mes_anomalo_sep = any(m["mes"] == 9 for m in meses_anomalos)
    proyeccion_ok = datos.get("proyeccion", {}).get("datos_suficientes") is True
    ok = alerta_restaurantes and mes_anomalo_sep and proyeccion_ok
    registrar(
        "2. Dashboard demo",
        "alerta Restaurantes + mes anómalo = septiembre + proyección con datos suficientes",
        f"alerta_restaurantes={alerta_restaurantes}, meses_anomalos={[m['mes'] for m in meses_anomalos]}, "
        f"proyeccion.datos_suficientes={proyeccion_ok}, proyeccion.monto={datos.get('proyeccion', {}).get('monto')}",
        "OK" if ok else "FALLA",
        t,
    )

    catalogos = cliente.get("/catalogos", headers=auth(token_demo)).json()
    cat_id = {c["nombre"]: c["id"] for c in catalogos["categorias"]}
    medio_id = {m["nombre"]: m["id"] for m in catalogos["medios_pago"]}

    # --- 3. Registro por texto ---
    t = time.monotonic()
    r = cliente.post("/chat/mensajes", json={"texto": "gasté 15000 en el súper con débito", "conversacion_id": None}, headers=auth(token_demo))
    cuerpo = r.json()
    borrador_a = cuerpo.get("borrador")
    conversacion_id = cuerpo["conversacion_id"]
    ok = borrador_a is not None and float(borrador_a["monto"]) == 15000 and borrador_a["tipo"] == "EGRESO"
    registrar(
        "3a. Registro por texto: gasto súper débito",
        "borrador con monto=15000, tipo=EGRESO",
        f"borrador={borrador_a}",
        "OK" if ok else "FALLA",
        t,
    )
    if borrador_a:
        guardado = cliente.post(
            "/movimientos",
            json=[{
                "monto": borrador_a["monto"], "fecha": borrador_a["fecha"], "tipo": borrador_a["tipo"],
                "descripcion": borrador_a["descripcion"],
                "categoria_id": borrador_a["categoria_id"] or cat_id.get("Supermercado"),
                "medio_pago_id": borrador_a["medio_pago_id"] or medio_id.get("Débito"),
                "origen": "Texto", "conversacion_id": conversacion_id,
            }],
            headers=auth(token_demo),
        )
        registrar("3a. Confirmar guardado", "201", str(guardado.status_code), "OK" if guardado.status_code == 201 else "FALLA", t)

    t = time.monotonic()
    r = cliente.post("/chat/mensajes", json={"texto": "cobré 850000 de sueldo por transferencia", "conversacion_id": conversacion_id}, headers=auth(token_demo))
    borrador_b = r.json().get("borrador")
    ok = borrador_b is not None and float(borrador_b["monto"]) == 850000 and borrador_b["tipo"] == "INGRESO"
    registrar("3b. Registro por texto: sueldo transferencia", "borrador con monto=850000, tipo=INGRESO", f"borrador={borrador_b}", "OK" if ok else "FALLA", t)
    if borrador_b:
        cliente.post(
            "/movimientos",
            json=[{
                "monto": borrador_b["monto"], "fecha": borrador_b["fecha"], "tipo": borrador_b["tipo"],
                "descripcion": borrador_b["descripcion"],
                "categoria_id": borrador_b["categoria_id"] or cat_id.get("Sueldo"),
                "medio_pago_id": borrador_b["medio_pago_id"] or medio_id.get("Transferencia"),
                "origen": "Texto", "conversacion_id": conversacion_id,
            }],
            headers=auth(token_demo),
        )

    t = time.monotonic()
    r = cliente.post("/chat/mensajes", json={"texto": "compré ropa", "conversacion_id": conversacion_id}, headers=auth(token_demo))
    cuerpo_c = r.json()
    ok = cuerpo_c.get("borrador") is None and "monto" in cuerpo_c["mensaje"]["contenido"].lower()
    registrar("3c. Registro sin monto: compré ropa", "sin borrador, pide el monto", f"borrador={cuerpo_c.get('borrador')}, mensaje={cuerpo_c['mensaje']['contenido']!r}", "OK" if ok else "FALLA", t)

    t = time.monotonic()
    r = cliente.post("/chat/mensajes", json={"texto": "gasté 15000 en el súper con débito", "conversacion_id": conversacion_id}, headers=auth(token_demo))
    borrador_dup = r.json().get("borrador")
    if borrador_dup:
        val = cliente.post(
            "/movimientos/validar",
            json={
                "monto": borrador_dup["monto"], "fecha": borrador_dup["fecha"], "tipo": borrador_dup["tipo"],
                "descripcion": borrador_dup["descripcion"],
                "categoria_id": borrador_dup["categoria_id"] or cat_id.get("Supermercado"),
                "medio_pago_id": borrador_dup["medio_pago_id"] or medio_id.get("Débito"),
            },
            headers=auth(token_demo),
        ).json()
        ok = "POSIBLE_DUPLICADO" in val.get("advertencias", [])
        registrar("3d. Aviso de posible duplicado", "advertencias incluye POSIBLE_DUPLICADO", f"advertencias={val.get('advertencias')}", "OK" if ok else "FALLA", t)
    else:
        registrar("3d. Aviso de posible duplicado", "advertencias incluye POSIBLE_DUPLICADO", "sin borrador para validar", "FALLA", t)

    # --- 4. Comprobantes por imagen y PDF ---
    def paso_comprobante(nombre_paso, ruta, content_type, esperado, monto_esperado=None, fecha_esperada=None):
        t0 = time.monotonic()
        if not ruta.exists():
            registrar(nombre_paso, esperado, "archivo no encontrado", "FALLA", t0, f"no existe: {ruta}")
            return
        r = subir_archivo(cliente, ruta, content_type, "/archivos/comprobante", token_demo)
        if r.status_code != 200:
            registrar(nombre_paso, esperado, f"HTTP {r.status_code}: {r.text[:200]}", "FALLA", t0)
            return
        b = r.json().get("borrador")
        if b is None:
            registrar(nombre_paso, esperado, "sin borrador (no pudo interpretar el comprobante)", "FALLA", t0)
            return
        estado = "OK"
        obs = ""
        if monto_esperado is not None and float(b["monto"]) != monto_esperado:
            estado, obs = "FALLA", f"monto esperado {monto_esperado}, obtenido {b['monto']}"
        if fecha_esperada is not None and b["fecha"] != fecha_esperada:
            estado, obs = "FALLA", (obs + f"; fecha esperada {fecha_esperada}, obtenida {b['fecha']}").lstrip("; ")
        registrar(nombre_paso, esperado, f"borrador={b}", estado, t0, obs)

    paso_comprobante("4a. Ticket de compra", AIRFLOW / "ticket_compra.png", "image/png", "monto=7000, fecha=2026-11-07, EGRESO", 7000, "2026-11-07")
    paso_comprobante("4b. Comprobante de transferencia", ANEXO / "comprobante_transferencia_anonimizado.png", "image/png", "monto=70000, fecha=2026-11-04, EGRESO", 70000, "2026-11-04")
    paso_comprobante("4c. Factura de servicio (PDF real)", AIRFLOW / "Octubre_factura-telefono.pdf", "application/pdf", "borrador con monto y fecha de la factura (PDF con texto, sin OCR)")
    paso_comprobante("4d. Recibo de sueldo", ANEXO / "recibo_sueldo_anonimizado.png", "image/png", "informar cómo lo interpreta (no existe tipo 'recibo' en el enum)")

    # --- 5. Resumen de tarjeta (multi-página, con cuotas) ---
    t = time.monotonic()
    ruta = AIRFLOW / "resumen-septiembre.pdf"
    r = subir_archivo(cliente, ruta, "application/pdf", "/archivos/resumen", token_demo)
    if r.status_code == 200:
        cuerpo = r.json()
        items = cuerpo["items"]
        con_cuota = [i for i in items if i["cuota_numero"]]
        registrar(
            "5. Resumen de tarjeta (cuotas)",
            "N borradores (uno por consumo), páginas leídas, algunos con cuota",
            f"paginas_leidas={cuerpo['paginas_leidas']}, items={len(items)}, con_cuota={len(con_cuota)}",
            "OK" if items else "FALLA",
            t,
            "Comparar la cantidad de items contra los consumos reales del resumen a simple vista.",
        )
    else:
        registrar("5. Resumen de tarjeta (cuotas)", "200 con items", f"HTTP {r.status_code}: {r.text[:200]}", "FALLA", t)

    # --- 6. Resumen de cuenta (no tiene flujo dedicado, exploratorio) ---
    t = time.monotonic()
    ruta = AIRFLOW / "resumen28-8al1-10.pdf"
    r = subir_archivo(cliente, ruta, "application/pdf", "/archivos/resumen", token_demo)
    registrar(
        "6. Resumen de cuenta (exploratorio, vía /archivos/resumen)",
        "informar qué hace el sistema (no hay HU para esto)",
        f"HTTP {r.status_code}: {r.text[:300]}",
        "OBSERVACION",
        t,
    )

    # --- 7. Extracto ---
    t = time.monotonic()
    ruta = AIRFLOW / "extracto_demo_octubre_2026.csv"
    if ruta.exists():
        r = subir_archivo(cliente, ruta, "text/csv", "/archivos/extracto", token_demo)
        if r.status_code == 200:
            cuerpo = r.json()
            items = cuerpo["items"]
            ingresos = [i for i in items if i["tipo"] == "INGRESO"]
            egresos = [i for i in items if i["tipo"] == "EGRESO"]
            sin_cat_ni_medio = all(i["categoria_id"] is None and i["medio_pago_id"] is None for i in items)
            ok = len(items) + cuerpo["filas_descartadas"] >= 1 and sin_cat_ni_medio
            registrar(
                "7. Extracto CSV",
                "18 filas (2 ingresos, 16 egresos por signo), sin categoría ni medio de pago",
                f"items={len(items)} (ingresos={len(ingresos)}, egresos={len(egresos)}), "
                f"filas_descartadas={cuerpo['filas_descartadas']}, sin_categoria_ni_medio={sin_cat_ni_medio}",
                "OK" if ok else "FALLA",
                t,
            )
            if len(items) >= 2:
                t2 = time.monotonic()
                dos_filas = [
                    {
                        "monto": it["monto"], "fecha": it["fecha"], "tipo": it["tipo"], "descripcion": it["descripcion"],
                        "categoria_id": cat_id.get("Otros"), "medio_pago_id": medio_id.get("Transferencia"),
                        "origen": "Extracto", "archivo_ref": cuerpo["archivo_ref"], "comprobante_tipo": "EXTRACTO",
                    }
                    for it in items[:2]
                ]
                guardado = cliente.post("/movimientos", json=dos_filas, headers=auth(token_demo))
                registrar("7. Completar categoría/medio de 2 filas y guardar", "201", str(guardado.status_code), "OK" if guardado.status_code == 201 else "FALLA", t2)
        else:
            registrar("7. Extracto CSV", "200 con 18 filas", f"HTTP {r.status_code}: {r.text[:200]}", "FALLA", t)
    else:
        registrar("7. Extracto CSV", "18 filas", "archivo no encontrado", "FALLA", t, f"no existe: {ruta} (ni .xlsx provisto)")

    # --- 8. Historial: filtros ---
    t = time.monotonic()
    r = cliente.get("/movimientos", params={"categoria_id": cat_id.get("Supermercado")}, headers=auth(token_demo))
    registrar("8a. Filtro por categoría (Supermercado)", "200, items filtrados", f"HTTP {r.status_code}, total={r.json().get('total')}", "OK" if r.status_code == 200 else "FALLA", t)

    t = time.monotonic()
    r = cliente.get("/movimientos", params={"desde": "2026-11-01", "hasta": "2026-11-30"}, headers=auth(token_demo))
    registrar("8b. Filtro por fecha (noviembre 2026)", "200, items filtrados", f"HTTP {r.status_code}, total={r.json().get('total')}", "OK" if r.status_code == 200 else "FALLA", t)

    t = time.monotonic()
    r = cliente.get("/movimientos", params={"q": "Disco"}, headers=auth(token_demo))
    registrar("8c. Buscar 'Disco'", "200", f"HTTP {r.status_code}, total={r.json().get('total')}", "OK" if r.status_code == 200 else "FALLA", t)

    # --- 9. Asesoramiento ---
    preguntas = [
        "¿cuánto debería ahorrar de lo que gano?",
        "¿en qué estoy gastando de más este mes?",
        "¿cómo sé si estoy demasiado endeudado?",
    ]
    for pregunta in preguntas:
        t = time.monotonic()
        r = cliente.post("/chat/mensajes", json={"texto": pregunta, "conversacion_id": None}, headers=auth(token_demo))
        cuerpo = r.json()
        mensaje = cuerpo["mensaje"]
        fuentes = mensaje.get("fuentes") or []
        cita_documento = any(f["tipo"] == "documento" for f in fuentes)
        cita_movimientos = any(f["tipo"] == "movimientos" for f in fuentes)
        tiene_disclaimer = "orientativo" in mensaje["contenido"].lower()
        ok = (cita_documento or cita_movimientos) and tiene_disclaimer
        registrar(
            f"9. Asesoramiento: {pregunta!r}",
            "cita documento y/o movimientos + aclaración orientativa",
            f"cita_documento={cita_documento}, cita_movimientos={cita_movimientos}, disclaimer={tiene_disclaimer}, "
            f"titulos_citados={[f['titulo'] for f in fuentes if f['tipo'] == 'documento']}",
            "OK" if ok else "FALLA",
            t,
        )

    # --- 10 y 11. Admin + seguridad ---
    t = time.monotonic()
    token_admin = login(cliente, CORREO_ADMIN, CONTRASENA_ADMIN)
    registrar("10. Login administrador", "200 + token", "200 + token", "OK", t)

    t = time.monotonic()
    r = cliente.get("/admin/documentos", headers=auth(token_admin))
    docs = r.json() if r.status_code == 200 else []
    registrar("10. Admin ve los documentos de referencia", "3 documentos", f"HTTP {r.status_code}, cantidad={len(docs)}, titulos={[d['titulo'] for d in docs]}", "OK" if len(docs) == 3 else "FALLA", t)

    t = time.monotonic()
    registrar(
        "10. Listar usuarios desde el admin",
        "endpoint para listar usuarios",
        "no existe GET /admin/usuarios en el backend ni pantalla de admin en el frontend",
        "OBSERVACION",
        t,
        "Solo existe PATCH /admin/usuarios/{id}. No es un bug: ninguna fase de PLAN.md ni mockup contempla una pantalla de admin.",
    )

    t = time.monotonic()
    r1 = cliente.get("/movimientos", headers=auth(token_admin))
    r2 = cliente.get("/chat/conversaciones", headers=auth(token_admin))
    ok = r1.status_code == 403 and r2.status_code == 403
    registrar("10. Admin NO puede ver movimientos ni conversaciones", "403 y 403", f"movimientos={r1.status_code}, conversaciones={r2.status_code}", "OK" if ok else "FALLA", t)

    # Usuario temporal para bloqueo + aislamiento, para no tocar la cuenta demo.
    t = time.monotonic()
    correo_temp = "e2e.temporal@mail.com"
    cliente.post("/auth/registro", json={"nombre": "Usuario Temporal E2E", "correo": correo_temp, "contrasena": "Temporal2026"})
    for _ in range(5):
        cliente.post("/auth/login", json={"correo": correo_temp, "contrasena": "contrasena-incorrecta"})
    r = cliente.post("/auth/login", json={"correo": correo_temp, "contrasena": "contrasena-incorrecta"})
    registrar(
        "11. Bloqueo tras 5 intentos fallidos",
        "423 con mensaje genérico",
        f"HTTP {r.status_code}: {r.json().get('detail')}",
        "OK" if r.status_code == 423 else "FALLA",
        t,
    )

    t = time.monotonic()
    from app.db import SesionLocal
    from app.modelos.usuario import Usuario

    sesion = SesionLocal()
    usuario_temp = sesion.query(Usuario).filter_by(correo=correo_temp).one()
    id_temp = usuario_temp.id
    sesion.close()
    r = cliente.patch(f"/admin/usuarios/{id_temp}", json={"desbloquear": True}, headers=auth(token_admin))
    r2 = cliente.post("/auth/login", json={"correo": correo_temp, "contrasena": "Temporal2026"})
    ok = r.status_code == 200 and r2.status_code == 200
    registrar("11. Admin desbloquea al usuario", "200, y el usuario ya puede loguearse", f"patch={r.status_code}, login_post_desbloqueo={r2.status_code}", "OK" if ok else "FALLA", t)

    t = time.monotonic()
    correo_temp_b = "e2e.temporal.b@mail.com"
    cliente.post("/auth/registro", json={"nombre": "Usuario Temporal B", "correo": correo_temp_b, "contrasena": "Temporal2026"})
    token_b = login(cliente, correo_temp_b, "Temporal2026")
    r = cliente.get("/movimientos", headers=auth(token_b))
    total_b = r.json().get("total", -1)
    registrar(
        "11. Aislamiento entre usuarios",
        "el segundo usuario no ve movimientos del usuario demo (total=0)",
        f"total={total_b}",
        "OK" if total_b == 0 else "FALLA",
        t,
    )

    # --- 12. Dejar el usuario demo limpio para la grabación ---
    t = time.monotonic()
    from app.seed_demo import cargar_demo

    cargar_demo()
    registrar("12. Re-ejecutar seed-demo", "usuario demo con 6 meses frescos, sin los movimientos de esta prueba", "ejecutado sin excepción", "OK", t)

    sesion = SesionLocal()
    for correo in (correo_temp, correo_temp_b):
        usuario = sesion.query(Usuario).filter_by(correo=correo).one_or_none()
        if usuario:
            sesion.delete(usuario)
    sesion.commit()
    sesion.close()

    escribir_informe()
