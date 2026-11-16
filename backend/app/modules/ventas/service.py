import asyncio
from datetime import datetime, timezone
from decimal import Decimal
import logging
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.libros.models import Libro
from app.modules.ventas.models import RenglonVenta, Venta
from app.modules.ventas.schemas import (
    RenglonRead,
    VentaClienteRead,
    VentaCreate,
    VentaDetailRead,
)

logger = logging.getLogger("libreria.ventas")


def _map_to_venta_detail_read(venta: Venta) -> VentaDetailRead:
    return VentaDetailRead(
        id=venta.id,  # type: ignore[arg-type]
        fecha=venta.fecha,
        total=venta.total,
        cliente=VentaClienteRead(
            id=venta.cliente.id,  # type: ignore[arg-type]
            nombre=venta.cliente.nombre,
            email=venta.cliente.email,
        ),
        renglones=[
            RenglonRead(
                libro_id=r.libro_id,
                titulo=r.libro.titulo,
                cantidad=r.cantidad,
                precio_unitario=r.precio_unitario,
                subtotal=Decimal(r.cantidad) * r.precio_unitario,
            )
            for r in venta.renglones
        ],
    )


async def notificar_comprobante(venta_id: int, cliente_email: str, total: Decimal) -> None:
    """
    Tarea en segundo plano (BackgroundTasks) requerida por el Ejercicio 6 y caso D-07.
    Ejecuta await asyncio.sleep(0.5) de forma no bloqueante y emite el mensaje de log
    tras haber enviado la respuesta HTTP 201 al cliente.
    """
    await asyncio.sleep(0.5)
    logger.info(
        f"[AVISO COMPROBANTE] Comprobante de venta #{venta_id} enviado a {cliente_email} por un total de ${total:.2f}"
    )


async def create_venta(session: AsyncSession, data: VentaCreate) -> VentaDetailRead:
    """
    Crea una nueva venta con sus renglones en composición (RN-04, RN-05, RN-06, RN-07, C-05, C-06).
    1. Consulta los libros involucrados en una sola consulta SQL para obtener sus precios y stock.
    2. Si algún libro no existe -> lanza HTTP 409 (C-05).
    3. Copia el precio del libro al renglón (RN-06), descuenta stock y calcula total en el servidor (RN-07).
    4. Inserta venta y renglones. Si el cliente no existe -> PostgreSQL lanza IntegrityError -> HTTP 409 (C-05).
    5. Recarga con carga anticipada (anti-N+1) para retornar VentaDetailRead.
    """
    libro_ids = [r.libro_id for r in data.renglones]

    # Paso 1: Consultar los libros en una única consulta
    query_libros = select(Libro).where(Libro.id.in_(libro_ids))
    result_libros = await session.execute(query_libros)
    libros_encontrados = result_libros.scalars().all()
    libros_map = {l.id: l for l in libros_encontrados}

    # Paso 2: Si falta algún libro, lanzar 409 (C-05)
    if len(libros_map) != len(libro_ids):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Uno o más libros especificados no existen en el catálogo.",
        )

    # Paso 3: Validar stock, calcular subtotales y total general en Decimal
    total = Decimal("0.00")
    renglones_instances: list[RenglonVenta] = []

    for r in data.renglones:
        libro = libros_map[r.libro_id]
        if libro.stock < r.cantidad:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Stock insuficiente para el libro '{libro.titulo}'. Stock disponible: {libro.stock}.",
            )

        libro.stock -= r.cantidad
        session.add(libro)

        subtotal = Decimal(r.cantidad) * libro.precio
        total += subtotal

        renglon = RenglonVenta(
            libro_id=r.libro_id,
            cantidad=r.cantidad,
            precio_unitario=libro.precio,
        )
        renglones_instances.append(renglon)

    # Paso 4: Crear la venta y asociar renglones por composición
    venta = Venta(
        cliente_id=data.cliente_id,
        fecha=datetime.now(timezone.utc),
        total=total,
    )
    venta.renglones = renglones_instances
    session.add(venta)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflicto de integridad: el cliente indicado no existe o se violó una restricción de integridad.",
        ) from exc

    return await get_venta_by_id(session, venta.id)  # type: ignore[arg-type]


async def get_venta_by_id(session: AsyncSession, venta_id: int) -> VentaDetailRead:
    """
    Obtiene el detalle completo de una venta con carga anticipada (anti-N+1).
    Usa joinedload(Venta.cliente) y selectinload(Venta.renglones).joinedload(RenglonVenta.libro).
    """
    query = (
        select(Venta)
        .where(Venta.id == venta_id)
        .options(
            joinedload(Venta.cliente),
            selectinload(Venta.renglones).joinedload(RenglonVenta.libro),
        )
    )
    result = await session.execute(query)
    venta = result.scalar_one_or_none()
    if not venta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venta no encontrada.",
        )
    return _map_to_venta_detail_read(venta)


async def get_ventas(
    session: AsyncSession, limit: int = 20, offset: int = 0
) -> list[VentaDetailRead]:
    """
    Listado paginado de ventas con carga anticipada de relaciones (RN-10, C-07).
    """
    query = (
        select(Venta)
        .options(
            joinedload(Venta.cliente),
            selectinload(Venta.renglones).joinedload(RenglonVenta.libro),
        )
        .order_by(Venta.id)
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(query)
    ventas = result.scalars().all()
    return [_map_to_venta_detail_read(v) for v in ventas]
