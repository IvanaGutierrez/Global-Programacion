from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import CheckConstraint, Column, DateTime, Numeric, func
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.clientes.models import Cliente
    from app.modules.libros.models import Libro


class RenglonVenta(SQLModel, table=True):
    """
    Modelo de tabla para el renglón de una venta (composición).
    Restricciones: cantidad > 0, precio_unitario > 0.
    """
    __tablename__ = "renglon_venta"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="check_renglon_cantidad_positiva"),
        CheckConstraint("precio_unitario > 0", name="check_renglon_precio_unitario_positivo"),
    )

    id: int | None = Field(default=None, primary_key=True)
    venta_id: int = Field(foreign_key="venta.id", index=True, nullable=False)
    libro_id: int = Field(foreign_key="libro.id", index=True, nullable=False)
    cantidad: int = Field(nullable=False)
    precio_unitario: Decimal = Field(
        sa_column=Column(Numeric(10, 2), nullable=False)
    )

    # Relaciones de navegación
    venta: Optional["Venta"] = Relationship(back_populates="renglones")
    libro: Optional["Libro"] = Relationship(back_populates="renglones")


class Venta(SQLModel, table=True):
    """
    Modelo de tabla para ventas.
    Restricciones: total >= 0, fecha generada con timezone UTC.
    """
    __tablename__ = "venta"
    __table_args__ = (
        CheckConstraint("total >= 0", name="check_venta_total_no_negativo"),
    )

    id: int | None = Field(default=None, primary_key=True)
    cliente_id: int = Field(foreign_key="cliente.id", index=True, nullable=False)
    fecha: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    total: Decimal = Field(
        sa_column=Column(Numeric(12, 2), nullable=False)
    )

    # Relaciones de navegación
    cliente: Optional["Cliente"] = Relationship(back_populates="ventas")
    renglones: list[RenglonVenta] = Relationship(
        back_populates="venta",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
