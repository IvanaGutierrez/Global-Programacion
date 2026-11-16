import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import DATABASE_URL, SQL_ECHO
from app.core.database import create_db_engine, create_session_factory, init_db

# Registro de routers de todos los módulos
from app.modules.health.router import router as health_router
from app.modules.editoriales.router import router as editoriales_router
from app.modules.generos.router import router as generos_router
from app.modules.autores.router import router as autores_router
from app.modules.libros.router import router as libros_router
from app.modules.clientes.router import router as clientes_router
from app.modules.ventas.router import router as ventas_router

# Configuración básica de logging para BackgroundTasks y diagnóstico
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # 1. Crear el motor asincrónico y la fábrica de sesiones
    engine = create_db_engine(DATABASE_URL, echo=SQL_ECHO)
    session_factory = create_session_factory(engine)

    # 2. Guardar en app.state para inyección de dependencias (sección 1.9 de la consigna)
    app.state.engine = engine
    app.state.session_factory = session_factory

    # 3. Crear las tablas que falten al arrancar la aplicación (create_all no altera tablas existentes)
    await init_db(engine)

    yield

    # 4. Cerrar el motor asincrónico al apagar la aplicación
    await engine.dispose()


app = FastAPI(
    title="Librería de Barrio API",
    description="API REST asincrónica para catálogo y ventas de la Librería de Barrio - UTN Programación III",
    version="1.0.0",
    lifespan=lifespan,
)

raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080,http://localhost:5173,http://localhost:3000")
allow_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusión de todos los routers modulares
app.include_router(health_router)
app.include_router(editoriales_router)
app.include_router(generos_router)
app.include_router(autores_router)
app.include_router(libros_router)
app.include_router(clientes_router)
app.include_router(ventas_router)
