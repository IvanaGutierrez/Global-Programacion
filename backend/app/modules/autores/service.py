from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.autores.models import Autor
from app.modules.autores.schemas import AutorCreate, AutorLibroRead, AutorUpdate
from app.modules.libros.models import LibroAutor


async def create_autor(session: AsyncSession, data: AutorCreate) -> Autor:
    """Crea un nuevo autor en el sistema."""
    autor = Autor(nombre=data.nombre, nacionalidad=data.nacionalidad)
    session.add(autor)
    await session.commit()
    await session.refresh(autor)
    return autor


async def get_autor_by_id(session: AsyncSession, autor_id: int) -> Autor:
    """Busca un autor por ID; si no existe lanza HTTP 404."""
    query = select(Autor).where(Autor.id == autor_id)
    result = await session.execute(query)
    autor = result.scalar_one_or_none()
    if not autor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Autor no encontrado.",
        )
    return autor


async def update_autor(
    session: AsyncSession, autor_id: int, data: AutorUpdate
) -> Autor:
    """
    Actualización parcial (PATCH) aplicando solo campos enviados (exclude_unset=True).
    """
    autor = await get_autor_by_id(session, autor_id)
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        return autor

    for key, value in update_data.items():
        setattr(autor, key, value)

    session.add(autor)
    await session.commit()
    await session.refresh(autor)
    return autor


async def get_libros_by_autor(session: AsyncSession, autor_id: int) -> list[AutorLibroRead]:
    """
    Devuelve los libros de un autor junto con su rol y orden en la publicación.
    Usa joinedload(LibroAutor.libro) para precargar los libros en una única consulta (anti-N+1).
    """
    await get_autor_by_id(session, autor_id)
    query = (
        select(LibroAutor)
        .where(LibroAutor.autor_id == autor_id)
        .options(joinedload(LibroAutor.libro))
        .order_by(LibroAutor.orden)
    )
    result = await session.execute(query)
    autorias = result.scalars().all()

    return [
        AutorLibroRead(
            libro_id=autoria.libro.id,
            titulo=autoria.libro.titulo,
            isbn=autoria.libro.isbn,
            precio=autoria.libro.precio,
            stock=autoria.libro.stock,
            rol=autoria.rol,
            orden=autoria.orden,
        )
        for autoria in autorias
        if autoria.libro is not None
    ]
