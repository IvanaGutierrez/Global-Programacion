from sqlmodel import Field, SQLModel


class EditorialCreate(SQLModel):
    nombre: str = Field(min_length=1)
    pais: str = Field(min_length=1)


class EditorialUpdate(SQLModel):
    nombre: str | None = Field(default=None, min_length=1)
    pais: str | None = Field(default=None, min_length=1)


class EditorialRead(SQLModel):
    id: int
    nombre: str
    pais: str
