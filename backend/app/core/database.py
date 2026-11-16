from collections.abc import AsyncGenerator
from fastapi import Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel

# Importación de todos los modelos de dominio para que queden registrados en SQLModel.metadata
# antes de la llamada a init_db() / SQLModel.metadata.create_all
from app.modules.editoriales.models import Editorial
from app.modules.generos.models import Genero
from app.modules.autores.models import Autor
from app.modules.libros.models import Libro, LibroAutor
from app.modules.clientes.models import Cliente, PerfilCliente
from app.modules.ventas.models import Venta, RenglonVenta

__all__ = [
    "create_db_engine",
    "create_session_factory",
    "init_db",
    "get_session",
    "Editorial",
    "Genero",
    "Autor",
    "Libro",
    "LibroAutor",
    "Cliente",
    "PerfilCliente",
    "Venta",
    "RenglonVenta",
]


def create_db_engine(database_url: str, echo: bool = False) -> AsyncEngine:
    """
    Crea la instancia de AsyncEngine para SQLAlchemy / SQLModel con asyncpg.
    """
    return create_async_engine(
        database_url,
        echo=echo,
        future=True,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """
    Crea la fábrica de sesiones asincrónicas.
    Cumple con el requisito estricto: expire_on_commit=False (sección 4.5 de la consigna).
    """
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )


async def init_db(engine: AsyncEngine) -> None:
    """
    Crea las tablas en la base de datos si no existen utilizando metadata de SQLModel.
    create_all solo crea las tablas que no existen y no altera las existentes.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependencia de FastAPI (Depends(get_session)) para inyectar una sesión por petición.
    Obtiene la fábrica de sesiones guardada en app.state.session_factory durante el lifespan.
    Garantiza que la sesión se cierre correctamente tras finalizar la petición HTTP.
    """
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with session_factory() as session:
        yield session
