import os
from dotenv import load_dotenv

# Carga variables de entorno desde el archivo .env local si existe
load_dotenv(override=True)

# Validación estricta: DATABASE_URL es obligatoria y no tiene valor por defecto
DATABASE_URL: str | None = os.getenv("DATABASE_URL")
if not DATABASE_URL or not DATABASE_URL.strip():
    raise RuntimeError(
        "Error crítico de configuración: La variable de entorno 'DATABASE_URL' no está definida. "
        "Por motivos de seguridad y consigna estricta, la aplicación no provee credenciales ni URL por defecto."
    )

# Diagnóstico de consultas SQL (SQL_ECHO)
SQL_ECHO: bool = os.getenv("SQL_ECHO", "false").strip().lower() in ("true", "1", "yes")
