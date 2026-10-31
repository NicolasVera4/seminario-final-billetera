from datetime import UTC, datetime
from typing import Protocol


class Reloj(Protocol):
    def ahora(self) -> datetime: ...


class RelojReal:
    def ahora(self) -> datetime:
        return datetime.now(UTC)


def obtener_reloj() -> Reloj:
    return RelojReal()
