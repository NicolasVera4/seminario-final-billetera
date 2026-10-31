from pydantic import BaseModel, EmailStr, Field

from app.modelos.enums import RolUsuario


class RegistroEntrada(BaseModel):
    nombre: str = Field(min_length=1, max_length=200)
    correo: EmailStr
    contrasena: str = Field(min_length=8, max_length=64)


class LoginEntrada(BaseModel):
    correo: EmailStr
    contrasena: str


class UsuarioSalida(BaseModel):
    id: int
    nombre: str
    correo: str
    rol: RolUsuario

    model_config = {"from_attributes": True}


class TokenSalida(BaseModel):
    access_token: str
    token_type: str = "bearer"
