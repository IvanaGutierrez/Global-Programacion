from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.modules.health import service

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live", status_code=status.HTTP_200_OK)
async def health_live() -> dict[str, str]:
    """
    GET /health/live
    Verifica que la aplicación esté viva.
    No realiza consultas a la base de datos.
    """
    return await service.check_liveness()


@router.get("/ready", status_code=status.HTTP_200_OK)
async def health_ready(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    """
    GET /health/ready
    Verifica que la base de datos esté lista ejecutando SELECT 1.
    """
    return await service.check_readiness(session)
