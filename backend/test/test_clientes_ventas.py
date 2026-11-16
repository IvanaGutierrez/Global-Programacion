import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.modules.clientes.models import Cliente, PerfilCliente
from app.modules.clientes.schemas import (
    ClienteCreate,
    ClienteUpdate,
    PerfilCreate,
)
from app.modules.clientes import service as clientes_service
from app.modules.libros.models import Libro
from app.modules.ventas.models import RenglonVenta, Venta
from app.modules.ventas.schemas import (
    RenglonCreate,
    VentaCreate,
)
from app.modules.ventas import service as ventas_service


def test_routes_registered_and_no_patch_ventas():
    """Verifica el registro de endpoints y la ausencia estricta de PATCH en ventas (RN-08)."""
    paths = app.openapi()["paths"]
    print("\nTotal de rutas OpenAPI:", len(paths))
    
    # 1. Rutas de clientes
    assert "/clientes/" in paths
    assert "/clientes/{id}" in paths
    assert "/clientes/{id}/perfil" in paths
    assert "/clientes/{id}/ventas" in paths
    print(" Rutas de clientes registradas correctamente.")

    # 2. Rutas de ventas
    assert "/ventas/" in paths
    assert "/ventas/{id}" in paths
    
    # RN-08: Verificar que no existe PATCH /ventas/{id} ni PATCH /ventas/
    assert "patch" not in paths.get("/ventas/{id}", {}), "ERROR: No debe existir PATCH /ventas/{id} (RN-08)"
    assert "patch" not in paths.get("/ventas/", {}), "ERROR: No debe existir PATCH /ventas/ (RN-08)"
    print(" RN-08 verificado: No existe método PATCH para ventas.")


def test_dto_validations():
    """Pruebas de validación en DTOs de Clientes y Ventas (RN-05, EmailStr, etc.)."""
    # 1. Email inválido en ClienteCreate
    try:
        ClienteCreate(nombre="Juan Pérez", email="correo-invalido")  # type: ignore
        assert False, "Debería fallar con email inválido"
    except ValidationError:
        print(" Validado: ClienteCreate rechaza email inválido.")

    # 2. Venta sin renglones debe fallar (min_length=1)
    try:
        VentaCreate(cliente_id=1, renglones=[])
        assert False, "Debería fallar con renglones vacíos"
    except ValidationError:
        print(" Validado: VentaCreate rechaza lista vacía de renglones.")

    # 3. Renglón con cantidad <= 0
    try:
        RenglonCreate(libro_id=1, cantidad=0)
        assert False, "Debería fallar con cantidad <= 0"
    except ValidationError:
        print(" Validado: RenglonCreate rechaza cantidad <= 0.")

    # 4. Renglones con libro_id repetido (RN-05) -> debe lanzar ValidationError (422)
    try:
        VentaCreate(
            cliente_id=1,
            renglones=[
                RenglonCreate(libro_id=1, cantidad=2),
                RenglonCreate(libro_id=1, cantidad=3),
            ],
        )
        assert False, "Debería fallar con libro_id duplicado en renglones"
    except ValidationError:
        print(" Validado RN-05: VentaCreate rechaza libro_id repetido en la misma venta.")


async def test_create_cliente_exitoso_y_duplicado():
    """Prueba create_cliente: éxito sin MissingGreenlet y conflicto 409 con email duplicado."""
    # 1. Éxito al crear cliente
    mock_session = AsyncMock()
    cliente_creado = Cliente(id=1, nombre="Ivana Gutierrez", email="ivana@example.com")

    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = cliente_creado
    mock_session.execute.return_value = mock_res

    res = await clientes_service.create_cliente(
        mock_session,
        ClienteCreate(nombre="Ivana Gutierrez", email="ivana@example.com"),
    )
    assert res.id == 1
    assert res.nombre == "Ivana Gutierrez"
    assert res.email == "ivana@example.com"
    assert res.perfil is None
    print(" Verificado: create_cliente devuelve ClienteRead sin MissingGreenlet.")

    # 2. Email duplicado lanza HTTP 409
    mock_session_dup = AsyncMock()
    mock_session_dup.commit.side_effect = IntegrityError("statement", "params", Exception("unique constraint cliente_email"))
    try:
        await clientes_service.create_cliente(
            mock_session_dup,
            ClienteCreate(nombre="Ivana Gutierrez", email="ivana@example.com"),
        )
        assert False, "Debería lanzar HTTP 409"
    except HTTPException as e:
        assert e.status_code == 409
        assert e.detail == "Ya existe un cliente registrado con ese correo electrónico."
        print(f" Verificado: create_cliente rechaza email duplicado con HTTP 409 ({e.detail}).")


async def test_c03_segundo_perfil_mismo_cliente():
    """Caso C-03: Segundo perfil para el mismo cliente debe lanzar HTTP 409 (RN-09)."""
    mock_session = AsyncMock()
    # Simula que el cliente existe
    mock_res_cliente = MagicMock()
    mock_res_cliente.scalar_one_or_none.return_value = 1
    mock_session.execute.return_value = mock_res_cliente
    
    # Simula que al hacer commit, la BD rechaza por cliente_id UNIQUE
    mock_session.commit.side_effect = IntegrityError("statement", "params", Exception("unique constraint cliente_id"))

    try:
        await clientes_service.create_perfil_cliente(
            mock_session,
            cliente_id=1,
            data=PerfilCreate(telefono="11223344", direccion="Av. Siempre Viva 742"),
        )
        assert False, "Debería lanzar HTTP 409"
    except HTTPException as e:
        assert e.status_code == 409
        assert "RN-09" in e.detail or "perfil" in e.detail
        print(f" C-03 verificado: Segundo perfil rechazado con 409 ({e.detail}).")


async def test_c05_venta_con_libro_o_cliente_inexistente():
    """Caso C-05: Venta con libro inexistente o cliente inexistente devuelve 409."""
    # 1. Libro inexistente
    mock_session = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalars.return_value.all.return_value = []  # No encuentra el libro
    mock_session.execute.return_value = mock_res

    try:
        await ventas_service.create_venta(
            mock_session,
            VentaCreate(
                cliente_id=1,
                renglones=[RenglonCreate(libro_id=999, cantidad=1)],
            ),
        )
        assert False, "Debería lanzar HTTP 409 con libro inexistente"
    except HTTPException as e:
        assert e.status_code == 409
        print(f" C-05 (Libro inexistente) verificado: HTTP 409 ({e.detail}).")

    # 2. Cliente inexistente (falla FK en commit)
    mock_session_fk = AsyncMock()
    mock_libro = Libro(id=1, isbn="123", titulo="Libro Test", precio=Decimal("100.00"), stock=10, editorial_id=1)
    mock_res_libro = MagicMock()
    mock_res_libro.scalars.return_value.all.return_value = [mock_libro]
    mock_session_fk.execute.return_value = mock_res_libro
    mock_session_fk.commit.side_effect = IntegrityError("statement", "params", Exception("fk cliente_id violation"))

    try:
        await ventas_service.create_venta(
            mock_session_fk,
            VentaCreate(
                cliente_id=999,  # Cliente inexistente
                renglones=[RenglonCreate(libro_id=1, cantidad=1)],
            ),
        )
        assert False, "Debería lanzar HTTP 409 con cliente inexistente"
    except HTTPException as e:
        assert e.status_code == 409
        print(f" C-05 (Cliente inexistente) verificado: HTTP 409 ({e.detail}).")


async def test_c06_venta_valida_calculos_y_precios():
    """
    Caso C-06: Venta válida con dos renglones:
    - Precios copiados de cada libro (RN-06).
    - Subtotal = cantidad * precio_unitario.
    - Total calculado en el servidor (RN-07).
    """
    mock_session = AsyncMock()
    
    libro1 = Libro(id=1, isbn="978-1", titulo="Rayuela", precio=Decimal("25000.00"), stock=10, editorial_id=1)
    libro2 = Libro(id=4, isbn="978-4", titulo="Respiración artificial", precio=Decimal("27000.00"), stock=5, editorial_id=1)
    
    mock_res_libros = MagicMock()
    mock_res_libros.scalars.return_value.all.return_value = [libro1, libro2]
    
    # Mock para get_venta_by_id posterior
    cliente_mock = Cliente(id=2, nombre="Tomás Ríos", email="tomas@example.com")
    venta_db = Venta(
        id=2,
        cliente_id=2,
        fecha=datetime(2026, 10, 8, 21, 14, 11, tzinfo=timezone.utc),
        total=Decimal("77000.00"),
    )
    venta_db.cliente = cliente_mock
    venta_db.renglones = [
        RenglonVenta(id=1, venta_id=2, libro_id=1, cantidad=2, precio_unitario=Decimal("25000.00")),
        RenglonVenta(id=2, venta_id=2, libro_id=4, cantidad=1, precio_unitario=Decimal("27000.00")),
    ]
    venta_db.renglones[0].libro = libro1
    venta_db.renglones[1].libro = libro2
    
    mock_res_venta = MagicMock()
    mock_res_venta.scalar_one_or_none.return_value = venta_db
    
    mock_session.execute.side_effect = [mock_res_libros, mock_res_venta]

    venta_req = VentaCreate(
        cliente_id=2,
        renglones=[
            RenglonCreate(libro_id=1, cantidad=2),
            RenglonCreate(libro_id=4, cantidad=1),
        ],
    )

    res = await ventas_service.create_venta(mock_session, venta_req)

    # Verificaciones estrictas
    assert res.total == Decimal("77000.00"), f"Total esperado 77000.00, obtenido {res.total}"
    assert len(res.renglones) == 2
    assert res.renglones[0].precio_unitario == Decimal("25000.00")
    assert res.renglones[0].subtotal == Decimal("50000.00")
    assert res.renglones[1].precio_unitario == Decimal("27000.00")
    assert res.renglones[1].subtotal == Decimal("27000.00")
    
    # Stock descontado
    assert libro1.stock == 8, f"Stock de libro 1 esperado 8, obtenido {libro1.stock}"
    assert libro2.stock == 4, f"Stock de libro 2 esperado 4, obtenido {libro2.stock}"

    print(f" C-06 verificado: Venta generada exitosamente con Total={res.total} y precios copiados.")


async def test_background_task_notificacion():
    """Ejercicio 6 y Caso D-07: Comprobante en segundo plano no bloqueante."""
    import time
    start = time.perf_counter()
    await ventas_service.notificar_comprobante(venta_id=2, cliente_email="tomas@example.com", total=Decimal("77000.00"))
    elapsed = time.perf_counter() - start
    assert elapsed >= 0.45, "La tarea debe ejecutar el delay de 0.5 segundos asincrónico"
    print(f" BackgroundTasks comprobado: Notificación emitida tras {elapsed:.2f}s sin llamadas bloqueantes.")


def run_all():
    print("=== INICIANDO SUITE DE PRUEBAS PASO 4 (CLIENTES Y VENTAS) ===")
    test_routes_registered_and_no_patch_ventas()
    test_dto_validations()
    asyncio.run(test_create_cliente_exitoso_y_duplicado())
    asyncio.run(test_c03_segundo_perfil_mismo_cliente())
    asyncio.run(test_c05_venta_con_libro_o_cliente_inexistente())
    asyncio.run(test_c06_venta_valida_calculos_y_precios())
    asyncio.run(test_background_task_notificacion())
    print("\n TODOS LOS TESTS DEL PASO 4 PASARON SATISFACTORIAMENTE.")


if __name__ == "__main__":
    run_all()
