from typing import TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.libros.models import LibroAutor


class Autor(SQLModel, table=True):
    __tablename__ = "autor"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(nullable=False)
    nacionalidad: str = Field(nullable=False)

    # Relación 1 a N con el objeto de asociación LibroAutor
    autorias: list["LibroAutor"] = Relationship(back_populates="autor")
