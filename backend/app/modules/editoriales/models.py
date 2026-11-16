from typing import TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.libros.models import Libro


class Editorial(SQLModel, table=True):
    __tablename__ = "editorial"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True, index=True, nullable=False)
    pais: str = Field(nullable=False)

    # Relación 1 a N: Una editorial puede estar asociada a muchos libros
    libros: list["Libro"] = Relationship(back_populates="editorial")
