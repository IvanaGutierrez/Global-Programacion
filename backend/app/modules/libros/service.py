from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.editoriales.schemas import EditorialRead
from app.modules.generos.schemas import GeneroRead
from app.modules.libros.models import Libro, LibroAutor
from app.modules.libros.schemas import (
    LibroAutorRead,
    LibroCreate,
    LibroDetailRead,
    LibroRead,
    LibroUpdate,
)


def _map_to_libro_read(libro: Libro) -> LibroRead:
    return LibroRead(
        id=libro.id,  # type: ignore[arg-type]
        isbn=libro.isbn,
        titulo=libro.titulo,
        precio=libro.precio,
        stock=libro.stock,
        editorial=EditorialRead.model_validate(libro.editorial),
        genero=GeneroRead.model_validate(libro.genero) if libro.genero else None,
    )


def _map_to_libro_detail_read(libro: Libro) -> LibroDetailRead:
    return LibroDetailRead(
        id=libro.id,  # type: ignore[arg-type]
        isbn=libro.isbn,
        titulo=libro.titulo,
        precio=libro.precio,
        stock=libro.stock,
        editorial=EditorialRead.model_validate(libro.editorial),
        genero=GeneroRead.model_validate(libro.genero) if libro.genero else None,
        autores=[
            LibroAutorRead(
                autor_id=autoria.autor_id,
                nombre=autoria.autor.nombre,
                nacionalidad=autoria.autor.nacionalidad,
                rol=autoria.rol,
                orden=autoria.orden,
            )
            for autoria in sorted(libro.autorias, key=lambda a: a.orden)
            if autoria.autor is not None
        ],
    )


async def create_libro(session: AsyncSession, data: LibroCreate) -> LibroDetailRead:
    """
    Crea un libro junto con sus autorías (LibroAutor) sin consultas SELECT previas.
    Delega la validación de unicidad de ISBN y existencia de editorial, género y autores
    directamente en PostgreSQL. Si alguna falla, captura IntegrityError y devuelve HTTP 409 (RN-01, C-04).
    """
    libro = Libro(
        isbn=data.isbn,
        titulo=data.titulo,
        precio=data.precio,
        stock=data.stock,
        editorial_id=data.editorial_id,
        genero_id=data.genero_id,
    )

    try:
        session.add(libro)
        await session.flush()

        for a in data.autores:
            autoria = LibroAutor(
                libro_id=libro.id,
                autor_id=a.autor_id,
                rol=a.rol,
                orden=a.orden,
            )
            session.add(autoria)

        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflicto de integridad: verifique que el ISBN sea único y que las referencias a editorial, género y autores existan.",
        ) from exc

    return await get_libro_detail_by_id(session, libro.id)  # type: ignore[arg-type]


async def get_libro_detail_by_id(session: AsyncSession, libro_id: int) -> LibroDetailRead:
    """
    Obtiene el detalle completo de un libro aplicando carga anticipada obligatoria (anti-N+1).
    Utiliza joinedload para relaciones a 1 (editorial, genero, autor) y selectinload para autorias (C-07).
    """
    query = (
        select(Libro)
        .where(Libro.id == libro_id)
        .options(
            joinedload(Libro.editorial),
            joinedload(Libro.genero),
            selectinload(Libro.autorias).joinedload(LibroAutor.autor),
        )
    )
    result = await session.execute(query)
    libro = result.scalar_one_or_none()
    if not libro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Libro no encontrado.",
        )
    return _map_to_libro_detail_read(libro)


async def get_libros(
    session: AsyncSession,
    limit: int = 20,
    offset: int = 0,
    titulo: str | None = None,
    genero_id: int | None = None,
) -> list[LibroRead]:
    """
    Listado paginado de libros con filtros opcionales por título (ILIKE con parámetro ligado seguro)
    y genero_id (RN-10, RN-11, C-08). Carga anticipada de editorial y género (anti-N+1).
    """
    query = (
        select(Libro)
        .options(
            joinedload(Libro.editorial),
            joinedload(Libro.genero),
        )
    )

    if titulo:
        # Búsqueda parcial segura con parámetro ligado: ILIKE '%titulo%'
        query = query.where(Libro.titulo.ilike(f"%{titulo}%"))
    if genero_id is not None:
        query = query.where(Libro.genero_id == genero_id)

    query = query.order_by(Libro.id).offset(offset).limit(limit)
    result = await session.execute(query)
    libros = result.scalars().all()
    return [_map_to_libro_read(libro) for libro in libros]


async def update_libro(
    session: AsyncSession, libro_id: int, data: LibroUpdate
) -> LibroDetailRead:
    """
    Actualización parcial (PATCH) aplicando solo campos provistos (exclude_unset=True).
    Captura posibles conflictos de integridad (IntegrityError -> 409).
    """
    # Buscamos el modelo base para actualizar
    query = select(Libro).where(Libro.id == libro_id)
    result = await session.execute(query)
    libro = result.scalar_one_or_none()
    if not libro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Libro no encontrado.",
        )

    update_data = data.model_dump(exclude_unset=True)
    if update_data:
        for key, value in update_data.items():
            setattr(libro, key, value)
        session.add(libro)
        try:
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Conflicto de integridad al actualizar el libro (verifique unicidad de ISBN o existencia de editorial/género).",
            ) from exc

    return await get_libro_detail_by_id(session, libro_id)
