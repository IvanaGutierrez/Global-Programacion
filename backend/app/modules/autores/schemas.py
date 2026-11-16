from decimal import Decimal
from sqlmodel import Field, SQLModel


class AutorCreate(SQLModel):
    nombre: str = Field(min_length=1)
    nacionalidad: str = Field(min_length=1)


class AutorUpdate(SQLModel):
    nombre: str | None = Field(default=None, min_length=1)
    nacionalidad: str | None = Field(default=None, min_length=1)


class AutorRead(SQLModel):
    id: int
    nombre: str
    nacionalidad: str


class AutorLibroRead(SQLModel):
    """Representa la información de un libro asociado al autor, incluyendo su rol y orden."""
    libro_id: int
    titulo: str
    isbn: str
    precio: Decimal
    stock: int
    rol: str
    orden: int
