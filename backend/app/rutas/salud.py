from fastapi import APIRouter

router = APIRouter()


@router.get("/salud")
def salud() -> dict[str, str]:
    return {"estado": "ok"}
