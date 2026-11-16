from typing import TYPE_CHECKING
from fastapi import APIRouter, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.modules.editoriales import service
from app.modules.editoriales.schemas import EditorialCreate, EditorialRead, EditorialUpdate

# Importamos LibroRead para la respuesta de /editoriales/{id}/libros
from app.modules.libros.schemas import LibroRead

router = APIRouter(prefix="/editoriales", tags=["Editoriales"])


@router.post("/", response_model=EditorialRead, status_code=status.HTTP_201_CREATED)
async def create_editorial(
    data: EditorialCreate,
    session: AsyncSession = Depends(get_session),
) -> EditorialRead:
    return await service.create_editorial(session, data)


@router.get("/", response_model=list[EditorialRead], status_code=status.HTTP_200_OK)
async def get_editoriales(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[EditorialRead]:
    return await service.get_editoriales(session, limit=limit, offset=offset)


@router.get("/{id}", response_model=EditorialRead, status_code=status.HTTP_200_OK)
async def get_editorial_by_id(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> EditorialRead:
    return await service.get_editorial_by_id(session, editorial_id=id)


@router.patch("/{id}", response_model=EditorialRead, status_code=status.HTTP_200_OK)
async def update_editorial(
    id: int,
    data: EditorialUpdate,
    session: AsyncSession = Depends(get_session),
) -> EditorialRead:
    return await service.update_editorial(session, editorial_id=id, data=data)


@router.get("/{id}/libros", response_model=list[LibroRead], status_code=status.HTTP_200_OK)
async def get_libros_by_editorial(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> list[LibroRead]:
    return await service.get_libros_by_editorial(session, editorial_id=id)
