from typing import TYPE_CHECKING, Optional
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.ventas.models import Venta


class PerfilCliente(SQLModel, table=True):
    """
    Modelo de tabla para perfil del cliente (relación 1 a 1).
    Restricciones: cliente_id es UNIQUE (RN-09) e indexado.
    """
    __tablename__ = "perfil_cliente"

    id: int | None = Field(default=None, primary_key=True)
    cliente_id: int = Field(
        foreign_key="cliente.id",
        unique=True,
        index=True,
        nullable=False,
    )
    telefono: str = Field(nullable=False)
    direccion: str = Field(nullable=False)

    # Navegación hacia el cliente propietario del perfil
    cliente: Optional["Cliente"] = Relationship(back_populates="perfil")


class Cliente(SQLModel, table=True):
    """
    Modelo de tabla para clientes.
    Restricciones: email UNIQUE (RN-02) e indexado.
    """
    __tablename__ = "cliente"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(nullable=False)
    email: str = Field(unique=True, index=True, nullable=False)

    # Relación 1 a 1: uselist=False garantiza que devuelve una entidad única o None, nunca una lista
    perfil: Optional[PerfilCliente] = Relationship(
        back_populates="cliente",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"},
    )

    # Relación 1 a N con Venta
    ventas: list["Venta"] = Relationship(back_populates="cliente")
