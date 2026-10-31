import enum


class RolUsuario(str, enum.Enum):
    USUARIO = "USUARIO"
    ADMINISTRADOR = "ADMINISTRADOR"


class TipoMovimiento(str, enum.Enum):
    INGRESO = "INGRESO"
    EGRESO = "EGRESO"


class TipoComprobante(str, enum.Enum):
    TICKET = "TICKET"
    FACTURA = "FACTURA"
    RESUMEN_TARJETA = "RESUMEN_TARJETA"
    EXTRACTO = "EXTRACTO"


class RolMensaje(str, enum.Enum):
    USUARIO = "USUARIO"
    ASISTENTE = "ASISTENTE"
