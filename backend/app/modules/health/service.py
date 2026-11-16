from fastapi import HTTPException, status
from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession


async def check_liveness() -> dict[str, str]:
    """
    Comprueba que el proceso de la aplicación esté en ejecución.
    Requisito estricto: no toca la base de datos.
    """
    return {"estado": "vivo"}


async def check_readiness(session: AsyncSession) -> dict[str, str]:
    """
    Comprueba que la base de datos esté accesible ejecutando SELECT 1 en PostgreSQL.
    Si la base de datos responde correctamente, retorna 200 OK con el estado.
    Si no responde o la consulta falla, lanza HTTP 503 Service Unavailable sin exponer
    detalles internos ni trazas de la base de datos (RN-12).
    """
    try:
        result = await session.execute(text("SELECT 1"))
        scalar = result.scalar()
        if scalar == 1:
            return {"estado": "listo", "database": "conectada"}
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La base de datos no respondió con el valor esperado",
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La base de datos no está disponible",
        ) from exc
