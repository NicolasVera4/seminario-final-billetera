from datetime import date
from pathlib import Path

import pytest
import yaml

from app.esquemas.movimientos import Catalogo
from app.proveedores.llm import ProveedorGroq
from app.seed import CATEGORIAS, MEDIOS_PAGO

RUTA_CONJUNTO = Path(__file__).parent / "conjunto_oro.yaml"
CAMPOS = ["intencion", "monto", "tipo", "medio_pago", "categoria", "faltantes"]

pytestmark = pytest.mark.integracion


def _cargar_todas():
    with RUTA_CONJUNTO.open(encoding="utf-8") as archivo:
        return yaml.safe_load(archivo)


def test_conjunto_oro_completo_contra_groq_real():
    proveedor = ProveedorGroq()
    catalogo = Catalogo(categorias=CATEGORIAS, medios_pago=MEDIOS_PAGO)

    aciertos = dict.fromkeys(CAMPOS, 0)
    total = dict.fromkeys(CAMPOS, 0)

    for caso in _cargar_todas():
        hoy = date.fromisoformat(caso["fecha_hoy"])
        resultado = proveedor.clasificar_e_interpretar(caso["texto"], hoy, catalogo)
        esperado = caso["esperado"]
        movimiento = resultado.movimiento

        total["intencion"] += 1
        aciertos["intencion"] += resultado.intencion == esperado["intencion"]

        if "monto" in esperado:
            total["monto"] += 1
            aciertos["monto"] += bool(movimiento) and movimiento.monto == esperado["monto"]

        if "tipo" in esperado:
            total["tipo"] += 1
            aciertos["tipo"] += bool(movimiento and movimiento.tipo and movimiento.tipo.value == esperado["tipo"])

        if "medio_pago" in esperado:
            total["medio_pago"] += 1
            aciertos["medio_pago"] += bool(movimiento) and movimiento.medio_pago == esperado["medio_pago"]

        if "categoria" in esperado:
            total["categoria"] += 1
            aciertos["categoria"] += bool(movimiento) and movimiento.categoria == esperado["categoria"]

        if "faltantes" in esperado:
            total["faltantes"] += 1
            # Subconjunto, no igualdad: al sistema le importa que lo obligatorio
            # (ej. "monto") este marcado, no que el modelo no agregue mas campos.
            aciertos["faltantes"] += set(esperado["faltantes"]) <= set(resultado.faltantes)

    print("\nResultados conjunto de oro (primeras 10 entradas):")
    for campo in CAMPOS:
        if total[campo]:
            porcentaje = 100 * aciertos[campo] / total[campo]
            print(f"  {campo}: {aciertos[campo]}/{total[campo]} ({porcentaje:.0f}%)")

    assert aciertos["intencion"] / total["intencion"] >= 0.7
