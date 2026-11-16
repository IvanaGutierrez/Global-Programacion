from datetime import datetime
from decimal import Decimal
from pydantic import model_validator
from sqlmodel import Field, SQLModel


class RenglonCreate(SQLModel):
    libro_id: int
    cantidad: int = Field(gt=0)


class VentaCreate(SQLModel):
    cliente_id: int
    renglones: list[RenglonCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def validar_renglones_sin_duplicados(self) -> "VentaCreate":
        libro_ids = [r.libro_id for r in self.renglones]
        if len(libro_ids) != len(set(libro_ids)):
            raise ValueError(
                "RN-05: Una venta no puede contener el mismo libro en más de un renglón."
            )
        return self


class RenglonRead(SQLModel):
    libro_id: int
    titulo: str
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


class VentaClienteRead(SQLModel):
    id: int
    nombre: str
    email: str


class VentaDetailRead(SQLModel):
    id: int
    fecha: datetime
    total: Decimal
    cliente: VentaClienteRead
    renglones: list[RenglonRead]
