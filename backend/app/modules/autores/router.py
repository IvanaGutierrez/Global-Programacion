from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.modules.autores import service
from app.modules.autores.schemas import AutorCreate, AutorLibroRead, AutorRead, AutorUpdate

router = APIRouter(prefix="/autores", tags=["Autores"])


@router.post("/", response_model=AutorRead, status_code=status.HTTP_201_CREATED)
async def create_autor(
    data: AutorCreate,
    session: AsyncSession = Depends(get_session),
) -> AutorRead:
    return await service.create_autor(session, data)


@router.get("/{id}", response_model=AutorRead, status_code=status.HTTP_200_OK)
async def get_autor_by_id(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> AutorRead:
    return await service.get_autor_by_id(session, autor_id=id)


@router.patch("/{id}", response_model=AutorRead, status_code=status.HTTP_200_OK)
async def update_autor(
    id: int,
    data: AutorUpdate,
    session: AsyncSession = Depends(get_session),
) -> AutorRead:
    return await service.update_autor(session, autor_id=id, data=data)


@router.get("/{id}/libros", response_model=list[AutorLibroRead], status_code=status.HTTP_200_OK)
async def get_libros_by_autor(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> list[AutorLibroRead]:
    return await service.get_libros_by_autor(session, autor_id=id)
