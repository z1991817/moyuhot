from fastapi import APIRouter

from app.models.common import APIModel

router = APIRouter(tags=["health"])


class HealthResponse(APIModel):
    status: str


@router.get("/healthz", response_model=HealthResponse)
async def healthz() -> HealthResponse:
    return HealthResponse(status="ok")
