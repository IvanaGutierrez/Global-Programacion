import asyncio
from decimal import Decimal
import logging
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import DATABASE_URL, SQL_ECHO
from app.core.database import (
    Autor,
    Cliente,
    Editorial,
    Genero,
    Libro,
    LibroAutor,
    PerfilCliente,
    create_db_engine,
    create_session_factory,
    init_db,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed")


async def seed_data(session: AsyncSession) -> None:
    logger.info("Verificando y poblando datos iniciales...")

    # 1. Editoriales (idempotente)
    editoriales_data = [
        {"nombre": "Sudamericana", "pais": "Argentina"},
        {"nombre": "Emecé", "pais": "Argentina"},
    ]
    editoriales_map: dict[str, Editorial] = {}
    for ed_data in editoriales_data:
        query = select(Editorial).where(Editorial.nombre == ed_data["nombre"])
        result = await session.execute(query)
        editorial = result.scalar_one_or_none()
        if not editorial:
            editorial = Editorial(nombre=ed_data["nombre"], pais=ed_data["pais"])
            session.add(editorial)
            await session.flush()
            logger.info(f"Editorial creada: {editorial.nombre} (ID: {editorial.id})")
        editoriales_map[editorial.nombre] = editorial

    # 2. Géneros (idempotente)
    generos_data = ["Novela", "Ficción"]
    generos_map: dict[str, Genero] = {}
    for gen_nombre in generos_data:
        query = select(Genero).where(Genero.nombre == gen_nombre)
        result = await session.execute(query)
        genero = result.scalar_one_or_none()
        if not genero:
            genero = Genero(nombre=gen_nombre)
            session.add(genero)
            await session.flush()
            logger.info(f"Género creado: {genero.nombre} (ID: {genero.id})")
        generos_map[genero.nombre] = genero

    # 3. Autores (idempotente)
    autores_data = [
        {"nombre": "Julio Cortázar", "nacionalidad": "Argentina"},
        {"nombre": "Jorge Luis Borges", "nacionalidad": "Argentina"},
        {"nombre": "Silvina Ocampo", "nacionalidad": "Argentina"},
        {"nombre": "Adolfo Bioy Casares", "nacionalidad": "Argentina"},
    ]
    autores_map: dict[str, Autor] = {}
    for aut_data in autores_data:
        query = select(Autor).where(Autor.nombre == aut_data["nombre"])
        result = await session.execute(query)
        autor = result.scalar_one_or_none()
        if not autor:
            autor = Autor(nombre=aut_data["nombre"], nacionalidad=aut_data["nacionalidad"])
            session.add(autor)
            await session.flush()
            logger.info(f"Autor creado: {autor.nombre} (ID: {autor.id})")
        autores_map[autor.nombre] = autor

    # 4. Libros y sus Autorías (idempotente)
    # Datos coherentes con los ejemplos del enunciado (Caso C-06 y D-03):
    # Libro 1: Rayuela ($25000.00)
    # Libro 4: Respiración artificial ($27000.00)
    libros_data = [
        {
            "isbn": "978-950-07-0001-0",
            "titulo": "Rayuela",
            "precio": Decimal("25000.00"),
            "stock": 50,
            "editorial_nombre": "Sudamericana",
            "genero_nombre": "Novela",
            "autores": [
                {"autor_nombre": "Julio Cortázar", "rol": "autor", "orden": 1}
            ],
        },
        {
            "isbn": "978-950-04-0002-0",
            "titulo": "Ficciones",
            "precio": Decimal("22000.00"),
            "stock": 35,
            "editorial_nombre": "Emecé",
            "genero_nombre": "Ficción",
            "autores": [
                {"autor_nombre": "Jorge Luis Borges", "rol": "autor", "orden": 1}
            ],
        },
        {
            "isbn": "978-950-04-0003-0",
            "titulo": "El Aleph",
            "precio": Decimal("23000.00"),
            "stock": 25,
            "editorial_nombre": "Emecé",
            "genero_nombre": "Ficción",
            "autores": [
                {"autor_nombre": "Jorge Luis Borges", "rol": "autor", "orden": 1}
            ],
        },
        {
            "isbn": "978-950-07-0004-0",
            "titulo": "Respiración artificial",
            "precio": Decimal("27000.00"),
            "stock": 40,
            "editorial_nombre": "Sudamericana",
            "genero_nombre": "Novela",
            "autores": [
                {"autor_nombre": "Silvina Ocampo", "rol": "coautor", "orden": 1},
                {"autor_nombre": "Adolfo Bioy Casares", "rol": "coautor", "orden": 2},
            ],
        },
    ]

    for b_data in libros_data:
        query = select(Libro).where(Libro.isbn == b_data["isbn"])
        result = await session.execute(query)
        libro = result.scalar_one_or_none()
        if not libro:
            ed = editoriales_map[b_data["editorial_nombre"]]
            gen = generos_map[b_data["genero_nombre"]]
            libro = Libro(
                isbn=b_data["isbn"],
                titulo=b_data["titulo"],
                precio=b_data["precio"],
                stock=b_data["stock"],
                editorial_id=ed.id,  # type: ignore[arg-type]
                genero_id=gen.id,    # type: ignore[arg-type]
            )
            session.add(libro)
            await session.flush()
            logger.info(f"Libro creado: {libro.titulo} (ID: {libro.id})")

            for aut_info in b_data["autores"]:
                autor_obj = autores_map[aut_info["autor_nombre"]]
                autoria = LibroAutor(
                    libro_id=libro.id,      # type: ignore[arg-type]
                    autor_id=autor_obj.id,  # type: ignore[arg-type]
                    rol=aut_info["rol"],
                    orden=aut_info["orden"],
                )
                session.add(autoria)
            await session.flush()

    # 5. Clientes (idempotente)
    # Cliente 1: Sin perfil inicial para permitir probar caso C-03 (POST /clientes/1/perfil)
    # Cliente 2: "Tomás Ríos" (usado en caso C-06 y D-03)
    clientes_data = [
        {"nombre": "Martín Fierro", "email": "martin@example.com"},
        {"nombre": "Tomás Ríos", "email": "tomas@example.com"},
    ]
    for c_data in clientes_data:
        query = select(Cliente).where(Cliente.email == c_data["email"])
        result = await session.execute(query)
        cliente = result.scalar_one_or_none()
        if not cliente:
            cliente = Cliente(nombre=c_data["nombre"], email=c_data["email"])
            session.add(cliente)
            await session.flush()
            logger.info(f"Cliente creado: {cliente.nombre} (ID: {cliente.id})")

    await session.commit()
    logger.info("Carga de datos iniciales finalizada exitosamente.")


async def main() -> None:
    logger.info("Iniciando conexión a base de datos para seed...")
    engine = create_db_engine(DATABASE_URL, echo=SQL_ECHO)
    session_factory = create_session_factory(engine)

    # Aseguramos que las tablas existan antes de poblar
    await init_db(engine)

    async with session_factory() as session:
        await seed_data(session)

    await engine.dispose()
    logger.info("Proceso de seed finalizado.")


if __name__ == "__main__":
    asyncio.run(main())
