from typing import Protocol

import httpx

from app.config import settings


class Embedder(Protocol):
    def embeber(self, textos: list[str]) -> list[list[float]]: ...


class EmbedderOllama:
    def embeber(self, textos: list[str]) -> list[list[float]]:
        vectores = []
        for texto in textos:
            respuesta = httpx.post(
                f"{settings.ollama_url}/api/embeddings",
                json={"model": settings.ollama_modelo_embeddings, "prompt": texto},
                timeout=30,
            )
            respuesta.raise_for_status()
            vectores.append(respuesta.json()["embedding"])
        return vectores


def obtener_embedder() -> Embedder:
    return EmbedderOllama()
