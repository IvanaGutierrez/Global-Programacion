from pydantic import EmailStr
from sqlmodel import Field, SQLModel


class PerfilCreate(SQLModel):
    telefono: str = Field(min_length=1)
    direccion: str = Field(min_length=1)


class PerfilRead(SQLModel):
    id: int
    telefono: str
    direccion: str


class ClienteCreate(SQLModel):
    nombre: str = Field(min_length=1)
    email: EmailStr


class ClienteUpdate(SQLModel):
    nombre: str | None = Field(default=None, min_length=1)
    email: EmailStr | None = None


class ClienteRead(SQLModel):
    id: int
    nombre: str
    email: str
    perfil: PerfilRead | None = None
