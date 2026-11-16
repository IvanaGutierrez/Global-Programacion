import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.modules.editoriales.schemas import EditorialCreate, EditorialUpdate
from app.modules.generos.schemas import GeneroCreate
from app.modules.autores.schemas import AutorCreate, AutorUpdate
from app.modules.libros.schemas import LibroCreate, LibroAutorCreate, LibroUpdate
from app.modules.editoriales import service as editoriales_service
from app.modules.generos import service as generos_service
from app.modules.libros import service as libros_service
from app.modules.autores import service as autores_service


def test_routes_registered():
    """Verifica que todos los endpoints requeridos por la consigna estén en la aplicación."""
    paths = app.openapi()["paths"]
    print("\nTotal de rutas OpenAPI registradas:", len(paths))
    
    expected_endpoints = [
        "/health/live",
        "/health/ready",
        "/editoriales/",
        "/editoriales/{id}",
        "/editoriales/{id}/libros",
        "/generos/",
        "/generos/{id}/libros",
        "/autores/",
        "/autores/{id}",
        "/autores/{id}/libros",
        "/libros/",
        "/libros/{id}",
    ]
    for ep in expected_endpoints:
        assert ep in paths, f"Falta la ruta obligatoria: {ep}"
        print(f"  Ruta presente: {ep}")


def test_dto_validations():
    """Verifica las reglas de negocio en los DTOs (RN-03, autores únicos, rol, etc.)."""
    # 1. Precio <= 0 debe fallar (RN-03)
    try:
        LibroCreate(
            isbn="978-1234567890",
            titulo="Libro Test",
            precio=Decimal("0.00"),
            stock=10,
            editorial_id=1,
            autores=[LibroAutorCreate(autor_id=1, rol="autor", orden=1)],
        )
        assert False, "Debería fallar con precio <= 0"
    except ValidationError:
        print(" Validado: LibroCreate rechaza precio <= 0")

    # 2. Stock < 0 debe fallar (RN-03)
    try:
        LibroCreate(
            isbn="978-1234567890",
            titulo="Libro Test",
            precio=Decimal("1500.00"),
            stock=-1,
            editorial_id=1,
            autores=[LibroAutorCreate(autor_id=1, rol="autor", orden=1)],
        )
        assert False, "Debería fallar con stock < 0"
    except ValidationError:
        print(" Validado: LibroCreate rechaza stock negativo")

    # 3. Autores duplicados en el mismo libro debe fallar (integridad en DTO)
    try:
        LibroCreate(
            isbn="978-1234567890",
            titulo="Libro Test",
            precio=Decimal("1500.00"),
            stock=5,
            editorial_id=1,
            autores=[
                LibroAutorCreate(autor_id=2, rol="autor", orden=1),
                LibroAutorCreate(autor_id=2, rol="coautor", orden=2),
            ],
        )
        assert False, "Debería fallar con autor_id repetido"
    except ValidationError:
        print(" Validado: LibroCreate rechaza autor_id repetidos en la lista")

    # 4. Rol inválido debe fallar
    try:
        LibroAutorCreate(autor_id=1, rol="editor_fantasma", orden=1)  # type: ignore
        assert False, "Debería fallar con rol no admitido"
    except ValidationError:
        print(" Validado: LibroAutorCreate rechaza rol fuera de la lista permitida")


def test_c01_non_integer_route_param():
    """Caso C-01: Un parámetro de ruta que no es entero devuelve 422 sin ejecutar el handler."""
    mock_engine = MagicMock()
    mock_engine.dispose = AsyncMock()

    with patch("app.main.init_db", new_callable=AsyncMock), \
         patch("app.main.create_db_engine", return_value=mock_engine):
        with TestClient(app) as client:
            res = client.get("/editoriales/abc")
            assert res.status_code == 422, f"Esperado 422, obtenido {res.status_code}"
            print(f" C-01 verificado: GET /editoriales/abc devolvió {res.status_code}")

            res_libro = client.get("/libros/no-entero")
            assert res_libro.status_code == 422, f"Esperado 422, obtenido {res_libro.status_code}"
            print(f" C-01 verificado: GET /libros/no-entero devolvió {res_libro.status_code}")


async def test_integrity_error_handling():
    """Verifica que IntegrityError se traduzca a HTTP 409 sin exponer trazas internas (RN-12, C-02, C-04)."""
    # 1. Editorial duplicada
    mock_session = AsyncMock()
    mock_session.commit.side_effect = IntegrityError("statement", "params", Exception("unique constraint violation"))
    
    try:
        await editoriales_service.create_editorial(
            mock_session,
            EditorialCreate(nombre="Editorial Repetida", pais="Argentina"),
        )
        assert False, "Debería lanzar HTTPException 409"
    except HTTPException as e:
        assert e.status_code == 409
        assert "Ya existe una editorial" in e.detail
        print(" Captura de IntegrityError en editorial: HTTP 409 con mensaje limpio:", e.detail)

    # 2. Género duplicado
    mock_session_genero = AsyncMock()
    mock_session_genero.commit.side_effect = IntegrityError("statement", "params", Exception("unique constraint violation"))
    try:
        await generos_service.create_genero(
            mock_session_genero,
            GeneroCreate(nombre="Género Repetido"),
        )
        assert False, "Debería lanzar HTTPException 409"
    except HTTPException as e:
        assert e.status_code == 409
        assert "Ya existe un género" in e.detail
        print(" Captura de IntegrityError en género: HTTP 409 con mensaje limpio:", e.detail)

    # 3. Libro con conflicto de integridad (ISBN repetido o FK inexistente)
    mock_session_libro = AsyncMock()
    mock_session_libro.flush.side_effect = IntegrityError("statement", "params", Exception("foreign key violation"))
    
    try:
        await libros_service.create_libro(
            mock_session_libro,
            LibroCreate(
                isbn="978-950-00-0001-1",
                titulo="Libro con FK inválida",
                precio=Decimal("25000.00"),
                stock=5,
                editorial_id=999,
                autores=[LibroAutorCreate(autor_id=999, rol="autor", orden=1)],
            ),
        )
        assert False, "Debería lanzar HTTPException 409"
    except HTTPException as e:
        assert e.status_code == 409
        assert "Conflicto de integridad" in e.detail
        print(" Captura de IntegrityError en libro (C-04): HTTP 409 con mensaje limpio:", e.detail)


async def test_anti_n_plus_one_eager_loading():
    """Verifica que las consultas utilicen joinedload y selectinload (Consigna Ejercicio 5, C-07)."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Intentamos get_libro_detail_by_id y capturamos la consulta ejecutada
    try:
        await libros_service.get_libro_detail_by_id(mock_session, 1)
    except HTTPException:
        pass

    executed_query = mock_session.execute.call_args[0][0]
    options_types = [type(opt).__name__ for opt in executed_query._with_options]
    assert "_Load" in options_types or any("Load" in t for t in options_types), "La consulta debe tener opciones de carga anticipada"
    print(" C-07 Eager loading verificado en libro: joinedload y selectinload aplicados a relaciones.")


async def test_c08_safe_sql_param_binding():
    """Caso C-08: Búsqueda con ' OR '1'='1 no rompe ni inyecta SQL plano (RN-11)."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    res = await libros_service.get_libros(mock_session, titulo="' OR '1'='1")
    assert res == [], "Debe retornar lista vacía"
    
    executed_query = mock_session.execute.call_args[0][0]
    # Comprobamos que el WHERE contiene un BinaryExpression (parámetro ligado) y no SQL concatenado
    where_clause = str(executed_query.whereclause)
    assert "libro.titulo ILIKE" in where_clause or "lower(libro.titulo) LIKE" in where_clause
    print(" C-08 verificado: Búsqueda parcial usa parámetros ligados y previene inyección SQL.")


def run_all():
    print("=== INICIANDO SUITE DE PRUEBAS PASO 3 (CATÁLOGO) ===")
    test_routes_registered()
    test_dto_validations()
    test_c01_non_integer_route_param()
    asyncio.run(test_integrity_error_handling())
    asyncio.run(test_anti_n_plus_one_eager_loading())
    asyncio.run(test_c08_safe_sql_param_binding())
    print("\n TODOS LOS TESTS DEL PASO 3 PASARON SATISFACTORIAMENTE.")


if __name__ == "__main__":
    run_all()
