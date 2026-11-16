from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.modules.clientes import service
from app.modules.clientes.schemas import (
    ClienteCreate,
    ClienteRead,
    ClienteUpdate,
    PerfilCreate,
    PerfilRead,
)
from app.modules.ventas.schemas import VentaDetailRead

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.post("/", response_model=ClienteRead, status_code=status.HTTP_201_CREATED)
async def create_cliente(
    data: ClienteCreate,
    session: AsyncSession = Depends(get_session),
) -> ClienteRead:
    return await service.create_cliente(session, data)


@router.get("/{id}", response_model=ClienteRead, status_code=status.HTTP_200_OK)
async def get_cliente_by_id(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> ClienteRead:
    return await service.get_cliente_by_id(session, cliente_id=id)


@router.patch("/{id}", response_model=ClienteRead, status_code=status.HTTP_200_OK)
async def update_cliente(
    id: int,
    data: ClienteUpdate,
    session: AsyncSession = Depends(get_session),
) -> ClienteRead:
    return await service.update_cliente(session, cliente_id=id, data=data)


@router.post("/{id}/perfil", response_model=PerfilRead, status_code=status.HTTP_201_CREATED)
async def create_perfil_cliente(
    id: int,
    data: PerfilCreate,
    session: AsyncSession = Depends(get_session),
) -> PerfilRead:
    return await service.create_perfil_cliente(session, cliente_id=id, data=data)


@router.get("/{id}/ventas", response_model=list[VentaDetailRead], status_code=status.HTTP_200_OK)
async def get_ventas_by_cliente(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> list[VentaDetailRead]:
    return await service.get_ventas_by_cliente(session, cliente_id=id)
