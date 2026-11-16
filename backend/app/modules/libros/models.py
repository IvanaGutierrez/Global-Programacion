from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import CheckConstraint, Column, Numeric
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.autores.models import Autor
    from app.modules.editoriales.models import Editorial
    from app.modules.generos.models import Genero
    from app.modules.ventas.models import RenglonVenta


class LibroAutor(SQLModel, table=True):
    """
    Objeto de asociación para la relación muchos a muchos con datos entre Libro y Autor.
    Clave primaria compuesta por (libro_id, autor_id).
    Permite la navegación: libro.autorias[i].autor.
    """
    __tablename__ = "libro_autor"
    __table_args__ = (
        CheckConstraint(
            "rol IN ('autor', 'coautor', 'traductor', 'ilustrador')",
            name="check_libro_autor_rol_valido",
        ),
        CheckConstraint("orden >= 1", name="check_libro_autor_orden_minimo"),
    )

    libro_id: int = Field(foreign_key="libro.id", primary_key=True, index=True)
    autor_id: int = Field(foreign_key="autor.id", primary_key=True, index=True)
    rol: str = Field(nullable=False)
    orden: int = Field(nullable=False)

    # Navegación bidireccional
    libro: Optional["Libro"] = Relationship(back_populates="autorias")
    autor: Optional["Autor"] = Relationship(back_populates="autorias")


class Libro(SQLModel, table=True):
    """
    Modelo de tabla para libros.
    Restricciones: isbn UNIQUE, precio > 0, stock >= 0.
    """
    __tablename__ = "libro"
    __table_args__ = (
        CheckConstraint("precio > 0", name="check_libro_precio_positivo"),
        CheckConstraint("stock >= 0", name="check_libro_stock_no_negativo"),
    )

    id: int | None = Field(default=None, primary_key=True)
    isbn: str = Field(unique=True, index=True, nullable=False)
    titulo: str = Field(nullable=False)
    precio: Decimal = Field(
        sa_column=Column(Numeric(10, 2), nullable=False)
    )
    stock: int = Field(default=0, nullable=False)

    editorial_id: int = Field(foreign_key="editorial.id", index=True, nullable=False)
    genero_id: int | None = Field(default=None, foreign_key="genero.id", nullable=True, index=True)

    # Relaciones de navegación
    editorial: Optional["Editorial"] = Relationship(back_populates="libros")
    genero: Optional["Genero"] = Relationship(back_populates="libros")
    autorias: list[LibroAutor] = Relationship(
        back_populates="libro",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    renglones: list["RenglonVenta"] = Relationship(back_populates="libro")
