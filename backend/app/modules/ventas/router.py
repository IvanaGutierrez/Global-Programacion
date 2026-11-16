from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.modules.ventas import service
from app.modules.ventas.schemas import VentaCreate, VentaDetailRead

router = APIRouter(prefix="/ventas", tags=["Ventas"])


@router.post("/", response_model=VentaDetailRead, status_code=status.HTTP_201_CREATED)
async def create_venta(
    data: VentaCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> VentaDetailRead:
    """
    Registra una nueva venta con sus renglones (composición).
    El total es calculado en el servidor a partir de los precios actuales de los libros.
    Programa una tarea asincrónica en segundo plano (BackgroundTasks) para avisar del comprobante (RN-04 a RN-07, Ejercicio 6).
    """
    venta_detail = await service.create_venta(session, data)
    background_tasks.add_task(
        service.notificar_comprobante,
        venta_detail.id,
        venta_detail.cliente.email,
        venta_detail.total,
    )
    return venta_detail


@router.get("/", response_model=list[VentaDetailRead], status_code=status.HTTP_200_OK)
async def get_ventas(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[VentaDetailRead]:
    """Listado paginado de ventas con carga anticipada (RN-10)."""
    return await service.get_ventas(session, limit=limit, offset=offset)


@router.get("/{id}", response_model=VentaDetailRead, status_code=status.HTTP_200_OK)
async def get_venta_by_id(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> VentaDetailRead:
    """Detalle de una venta específica con cliente y renglones precargados (anti-N+1)."""
    return await service.get_venta_by_id(session, venta_id=id)

# NOTA DE REGLA DE NEGOCIO RN-08:
# Las ventas no se modifican (registran un hecho contable histórico).
# Por ende, NO existe endpoint PATCH /ventas/{id}.
