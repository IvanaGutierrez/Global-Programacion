from decimal import Decimal
from typing import Literal
from pydantic import model_validator
from sqlmodel import Field, SQLModel

from app.modules.editoriales.schemas import EditorialRead
from app.modules.generos.schemas import GeneroRead


class LibroAutorCreate(SQLModel):
    autor_id: int
    rol: Literal["autor", "coautor", "traductor", "ilustrador"]
    orden: int = Field(ge=1)


class LibroCreate(SQLModel):
    isbn: str = Field(min_length=1)
    titulo: str = Field(min_length=1)
    precio: Decimal = Field(gt=Decimal("0.00"))
    stock: int = Field(default=0, ge=0)
    editorial_id: int
    genero_id: int | None = None
    autores: list[LibroAutorCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def validar_autores_unicos(self) -> "LibroCreate":
        ids = [a.autor_id for a in self.autores]
        if len(ids) != len(set(ids)):
            raise ValueError("No puede haber autor_id duplicados en la lista de autores de un libro.")
        return self


class LibroUpdate(SQLModel):
    isbn: str | None = Field(default=None, min_length=1)
    titulo: str | None = Field(default=None, min_length=1)
    precio: Decimal | None = Field(default=None, gt=Decimal("0.00"))
    stock: int | None = Field(default=None, ge=0)
    editorial_id: int | None = None
    genero_id: int | None = None


class LibroAutorRead(SQLModel):
    autor_id: int
    nombre: str
    nacionalidad: str
    rol: str
    orden: int


class LibroRead(SQLModel):
    id: int
    isbn: str
    titulo: str
    precio: Decimal
    stock: int
    editorial: EditorialRead
    genero: GeneroRead | None = None


class LibroDetailRead(LibroRead):
    autores: list[LibroAutorRead] = []
