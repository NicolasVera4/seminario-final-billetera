from datetime import UTC, datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from app.config import settings

_contexto = CryptContext(schemes=["bcrypt"], bcrypt__rounds=12)

ALGORITMO = "HS256"


def hash_contrasena(contrasena: str) -> str:
    return _contexto.hash(contrasena)


def verificar_contrasena(contrasena: str, contrasena_hash: str) -> bool:
    return _contexto.verify(contrasena, contrasena_hash)


def generar_token(usuario_id: int) -> str:
    # El vencimiento del JWT se valida contra el reloj real (estandar JWT);
    # el reloj inyectado de la app es solo para la logica de bloqueo por intentos.
    expiracion = datetime.now(UTC) + timedelta(minutes=settings.jwt_minutos)
    return jwt.encode({"sub": str(usuario_id), "exp": expiracion}, settings.jwt_secreto, algorithm=ALGORITMO)


def decodificar_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secreto, algorithms=[ALGORITMO])
