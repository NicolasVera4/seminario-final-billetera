class ErrorServicio(Exception):
    """Error de negocio que un servicio levanta y la ruta traduce a una respuesta HTTP."""

    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
