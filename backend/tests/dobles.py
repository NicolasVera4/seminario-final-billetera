from datetime import datetime


class RelojFijo:
    """Doble de Reloj: devuelve un instante fijo que el test controla y puede avanzar."""

    def __init__(self, instante: datetime):
        self.instante = instante

    def ahora(self) -> datetime:
        return self.instante

    def avanzar(self, delta) -> None:
        self.instante = self.instante + delta


class FakeLLM:
    """Doble de ProveedorLLM: devuelve/lanza lo que el test configure y registra lo que recibio."""

    def __init__(self):
        self.llamadas_clasificar = []
        self.respuesta_clasificar = None
        self.llamadas_extraer = []
        self.respuesta_extraer = []
        self.respuesta_responder = "Esta es una respuesta de prueba."
        self.llamadas_responder = []

    def clasificar_e_interpretar(self, texto, hoy, catalogo):
        self.llamadas_clasificar.append({"texto": texto, "hoy": hoy, "catalogo": catalogo})
        if isinstance(self.respuesta_clasificar, Exception):
            raise self.respuesta_clasificar
        return self.respuesta_clasificar

    def extraer_movimientos(self, texto_documento, tipo, catalogo):
        self.llamadas_extraer.append({"texto_documento": texto_documento, "tipo": tipo, "catalogo": catalogo})
        if isinstance(self.respuesta_extraer, Exception):
            raise self.respuesta_extraer
        return self.respuesta_extraer

    def responder(self, pregunta, contexto_usuario, fragmentos, historial):
        self.llamadas_responder.append(
            {
                "pregunta": pregunta,
                "contexto_usuario": contexto_usuario,
                "fragmentos": fragmentos,
                "historial": historial,
            }
        )
        return self.respuesta_responder


class FakeEmbedder:
    """Doble de Embedder: vectores deterministas. El test puede fijar vectores
    exactos para textos puntuales (para controlar que recupere Chroma) y el
    resto cae a un vector derivado del propio texto (mismo texto, mismo vector)."""

    def __init__(self):
        self.vectores: dict[str, list[float]] = {}
        self.llamadas: list[list[str]] = []

    def embeber(self, textos: list[str]) -> list[list[float]]:
        self.llamadas.append(textos)
        return [self.vectores.get(texto, self._vector_por_defecto(texto)) for texto in textos]

    @staticmethod
    def _vector_por_defecto(texto: str) -> list[float]:
        total = sum(ord(c) for c in texto)
        return [float(len(texto)), float(total % 997), float(total % 101)]
