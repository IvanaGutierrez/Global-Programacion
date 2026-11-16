from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.generos.models import Genero
from app.modules.generos.schemas import GeneroCreate
from app.modules.libros.models import Libro


async def create_genero(session: AsyncSession, data: GeneroCreate) -> Genero:
    """
    Crea un nuevo género sin consultas previas de unicidad.
    Delega en PostgreSQL y captura IntegrityError -> 409 (RN-12).
    """
    genero = Genero(nombre=data.nombre)
    session.add(genero)
    try:
        await session.commit()
        await session.refresh(genero)
        return genero
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un género registrado con ese nombre.",
        ) from exc


async def get_generos(session: AsyncSession) -> list[Genero]:
    """Obtiene el listado completo de géneros literarios."""
    query = select(Genero).order_by(Genero.id)
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_genero_by_id(session: AsyncSession, genero_id: int) -> Genero:
    """Obtiene un género por ID o lanza HTTP 404."""
    query = select(Genero).where(Genero.id == genero_id)
    result = await session.execute(query)
    genero = result.scalar_one_or_none()
    if not genero:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Género no encontrado.",
        )
    return genero


async def get_libros_by_genero(session: AsyncSession, genero_id: int) -> list[Libro]:
    """
    Obtiene los libros correspondientes al género con carga anticipada (anti-N+1).
    Si el género no existe lanza HTTP 404.
    """
    await get_genero_by_id(session, genero_id)
    query = (
        select(Libro)
        .where(Libro.genero_id == genero_id)
        .options(
            joinedload(Libro.editorial),
            joinedload(Libro.genero),
        )
        .order_by(Libro.id)
    )
    result = await session.execute(query)
    return list(result.scalars().all())
