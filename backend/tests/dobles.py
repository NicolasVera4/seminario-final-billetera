from datetime import datetime


class RelojFijo:
    """Doble de Reloj: devuelve un instante fijo que el test controla y puede avanzar."""

    def __init__(self, instante: datetime):
        self.instante = instante

    def ahora(self) -> datetime:
        return self.instante

    def avanzar(self, delta) -> None:
        self.instante = self.instante + delta
