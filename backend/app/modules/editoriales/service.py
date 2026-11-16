from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.editoriales.models import Editorial
from app.modules.editoriales.schemas import EditorialCreate, EditorialUpdate
from app.modules.libros.models import Libro


async def create_editorial(session: AsyncSession, data: EditorialCreate) -> Editorial:
    """
    Inserta una nueva editorial sin consultar unicidad previa.
    Delega la integridad a PostgreSQL y traduce IntegrityError a HTTP 409 (RN-12).
    """
    editorial = Editorial(nombre=data.nombre, pais=data.pais)
    session.add(editorial)
    try:
        await session.commit()
        await session.refresh(editorial)
        return editorial
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una editorial registrada con ese nombre.",
        ) from exc


async def get_editoriales(session: AsyncSession, limit: int = 20, offset: int = 0) -> list[Editorial]:
    """Obtiene el listado paginado de editoriales (RN-10)."""
    query = select(Editorial).order_by(Editorial.id).offset(offset).limit(limit)
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_editorial_by_id(session: AsyncSession, editorial_id: int) -> Editorial:
    """Busca una editorial por su ID; si no existe lanza HTTP 404."""
    query = select(Editorial).where(Editorial.id == editorial_id)
    result = await session.execute(query)
    editorial = result.scalar_one_or_none()
    if not editorial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Editorial no encontrada.",
        )
    return editorial


async def update_editorial(
    session: AsyncSession, editorial_id: int, data: EditorialUpdate
) -> Editorial:
    """
    Actualización parcial (PATCH) aplicando solo campos enviados (exclude_unset=True).
    Captura posibles conflictos de unicidad (IntegrityError -> 409).
    """
    editorial = await get_editorial_by_id(session, editorial_id)
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        return editorial

    for key, value in update_data.items():
        setattr(editorial, key, value)

    session.add(editorial)
    try:
        await session.commit()
        await session.refresh(editorial)
        return editorial
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflicto de integridad: ya existe otra editorial con ese nombre.",
        ) from exc


async def get_libros_by_editorial(session: AsyncSession, editorial_id: int) -> list[Libro]:
    """
    Devuelve los libros de una editorial con carga anticipada (anti-N+1).
    Si la editorial no existe, responde HTTP 404.
    """
    await get_editorial_by_id(session, editorial_id)
    query = (
        select(Libro)
        .where(Libro.editorial_id == editorial_id)
        .options(
            joinedload(Libro.editorial),
            joinedload(Libro.genero),
        )
        .order_by(Libro.id)
    )
    result = await session.execute(query)
    return list(result.scalars().all())
