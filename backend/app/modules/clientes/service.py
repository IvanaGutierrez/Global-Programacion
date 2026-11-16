from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.clientes.models import Cliente, PerfilCliente
from app.modules.clientes.schemas import (
    ClienteCreate,
    ClienteRead,
    ClienteUpdate,
    PerfilCreate,
    PerfilRead,
)
from app.modules.ventas.models import RenglonVenta, Venta
from app.modules.ventas.schemas import RenglonRead, VentaClienteRead, VentaDetailRead


def _map_to_cliente_read(cliente: Cliente) -> ClienteRead:
    # Verificación segura en __dict__ para evitar MissingGreenlet al serializar
    # si la relación 'perfil' no fue cargada o es None
    perfil_obj = cliente.__dict__.get("perfil") if hasattr(cliente, "__dict__") else None
    return ClienteRead(
        id=cliente.id,  # type: ignore[arg-type]
        nombre=cliente.nombre,
        email=cliente.email,
        perfil=(
            PerfilRead(
                id=perfil_obj.id,  # type: ignore[arg-type]
                telefono=perfil_obj.telefono,
                direccion=perfil_obj.direccion,
            )
            if perfil_obj
            else None
        ),
    )


async def create_cliente(session: AsyncSession, data: ClienteCreate) -> ClienteRead:
    """
    Crea un nuevo cliente sin SELECT previo de unicidad (RN-02).
    Delega en PostgreSQL y captura IntegrityError -> HTTP 409 (RN-12).
    Recupera el cliente con selectinload mediante get_cliente_by_id para evitar MissingGreenlet.
    """
    cliente = Cliente(nombre=data.nombre, email=data.email)
    session.add(cliente)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un cliente registrado con ese correo electrónico.",
        ) from exc

    return await get_cliente_by_id(session, cliente.id)  # type: ignore[arg-type]


async def get_cliente_by_id(session: AsyncSession, cliente_id: int) -> ClienteRead:
    """
    Obtiene un cliente junto a su perfil utilizando selectinload (relación 1 a 1, sin N+1).
    Lanza HTTP 404 si el cliente no existe.
    """
    query = (
        select(Cliente)
        .where(Cliente.id == cliente_id)
        .options(selectinload(Cliente.perfil))
    )
    result = await session.execute(query)
    cliente = result.scalar_one_or_none()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado.",
        )
    return _map_to_cliente_read(cliente)


async def update_cliente(
    session: AsyncSession, cliente_id: int, data: ClienteUpdate
) -> ClienteRead:
    """
    Actualización parcial de cliente (PATCH).
    Captura posible conflicto de unicidad en email (IntegrityError -> 409).
    """
    query = (
        select(Cliente)
        .where(Cliente.id == cliente_id)
        .options(selectinload(Cliente.perfil))
    )
    result = await session.execute(query)
    cliente = result.scalar_one_or_none()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado.",
        )

    update_data = data.model_dump(exclude_unset=True)
    if update_data:
        for key, value in update_data.items():
            setattr(cliente, key, value)
        session.add(cliente)
        try:
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un cliente registrado con ese correo electrónico.",
            ) from exc

    return await get_cliente_by_id(session, cliente.id)  # type: ignore[arg-type]


async def create_perfil_cliente(
    session: AsyncSession, cliente_id: int, data: PerfilCreate
) -> PerfilRead:
    """
    Crea el perfil para un cliente existente.
    Verifica que el cliente exista (404 si no).
    Inserta el perfil sin comprobar previamente si ya tiene uno: si ya existe,
    PostgreSQL rechaza la restricción UNIQUE de cliente_id y se traduce a HTTP 409 (RN-09, Caso C-03).
    """
    # Verificamos existencia del cliente
    query_cliente = select(Cliente.id).where(Cliente.id == cliente_id)
    result_cliente = await session.execute(query_cliente)
    if not result_cliente.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado.",
        )

    perfil = PerfilCliente(
        cliente_id=cliente_id,
        telefono=data.telefono,
        direccion=data.direccion,
    )
    session.add(perfil)
    try:
        await session.commit()
        await session.refresh(perfil)
        return PerfilRead(
            id=perfil.id,  # type: ignore[arg-type]
            telefono=perfil.telefono,
            direccion=perfil.direccion,
        )
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El cliente ya posee un perfil asignado (RN-09).",
        ) from exc


async def get_ventas_by_cliente(
    session: AsyncSession, cliente_id: int
) -> list[VentaDetailRead]:
    """
    Obtiene las ventas realizadas por el cliente con carga anticipada (anti-N+1).
    Si el cliente no existe, responde HTTP 404.
    """
    query_cliente = select(Cliente.id).where(Cliente.id == cliente_id)
    result_cliente = await session.execute(query_cliente)
    if not result_cliente.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado.",
        )

    query = (
        select(Venta)
        .where(Venta.cliente_id == cliente_id)
        .options(
            joinedload(Venta.cliente),
            selectinload(Venta.renglones).joinedload(RenglonVenta.libro),
        )
        .order_by(Venta.id)
    )
    result = await session.execute(query)
    ventas = result.scalars().all()

    return [
        VentaDetailRead(
            id=v.id,  # type: ignore[arg-type]
            fecha=v.fecha,
            total=v.total,
            cliente=VentaClienteRead(
                id=v.cliente.id,  # type: ignore[arg-type]
                nombre=v.cliente.nombre,
                email=v.cliente.email,
            ),
            renglones=[
                RenglonRead(
                    libro_id=r.libro_id,
                    titulo=r.libro.titulo,
                    cantidad=r.cantidad,
                    precio_unitario=r.precio_unitario,
                    subtotal=Decimal(r.cantidad) * r.precio_unitario,
                )
                for r in v.renglones
            ],
        )
        for v in ventas
    ]
