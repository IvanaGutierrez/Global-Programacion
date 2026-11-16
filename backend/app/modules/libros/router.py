from fastapi import APIRouter, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.modules.libros import service
from app.modules.libros.schemas import (
    LibroCreate,
    LibroDetailRead,
    LibroRead,
    LibroUpdate,
)

router = APIRouter(prefix="/libros", tags=["Libros"])


@router.post("/", response_model=LibroDetailRead, status_code=status.HTTP_201_CREATED)
async def create_libro(
    data: LibroCreate,
    session: AsyncSession = Depends(get_session),
) -> LibroDetailRead:
    return await service.create_libro(session, data)


@router.get("/", response_model=list[LibroRead], status_code=status.HTTP_200_OK)
async def get_libros(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    titulo: str | None = Query(default=None),
    genero_id: int | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> list[LibroRead]:
    return await service.get_libros(
        session,
        limit=limit,
        offset=offset,
        titulo=titulo,
        genero_id=genero_id,
    )


@router.get("/{id}", response_model=LibroDetailRead, status_code=status.HTTP_200_OK)
async def get_libro_by_id(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> LibroDetailRead:
    return await service.get_libro_detail_by_id(session, libro_id=id)


@router.patch("/{id}", response_model=LibroDetailRead, status_code=status.HTTP_200_OK)
async def update_libro(
    id: int,
    data: LibroUpdate,
    session: AsyncSession = Depends(get_session),
) -> LibroDetailRead:
    return await service.update_libro(session, libro_id=id, data=data)
