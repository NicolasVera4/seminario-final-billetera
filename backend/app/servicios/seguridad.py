from app.servicios.reloj import Reloj


def hash_contrasena(contrasena: str) -> str:
    raise NotImplementedError


def verificar_contrasena(contrasena: str, contrasena_hash: str) -> bool:
    raise NotImplementedError


def generar_token(usuario_id: int, reloj: Reloj) -> str:
    raise NotImplementedError


def decodificar_token(token: str) -> dict:
    raise NotImplementedError
