from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.modules.generos import service
from app.modules.generos.schemas import GeneroCreate, GeneroRead

# Importamos LibroRead para la respuesta de /generos/{id}/libros
from app.modules.libros.schemas import LibroRead

router = APIRouter(prefix="/generos", tags=["Géneros"])


@router.post("/", response_model=GeneroRead, status_code=status.HTTP_201_CREATED)
async def create_genero(
    data: GeneroCreate,
    session: AsyncSession = Depends(get_session),
) -> GeneroRead:
    return await service.create_genero(session, data)


@router.get("/", response_model=list[GeneroRead], status_code=status.HTTP_200_OK)
async def get_generos(
    session: AsyncSession = Depends(get_session),
) -> list[GeneroRead]:
    return await service.get_generos(session)


@router.get("/{id}/libros", response_model=list[LibroRead], status_code=status.HTTP_200_OK)
async def get_libros_by_genero(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> list[LibroRead]:
    return await service.get_libros_by_genero(session, genero_id=id)
