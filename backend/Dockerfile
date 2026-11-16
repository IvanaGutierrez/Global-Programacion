# ==============================================================================
# Dockerfile - Parcial de Programación III (UTN) - "Librería de Barrio"
# Imagen base: python:3.12-alpine (< 100 MB, libre de compiladores innecesarios)
# ==============================================================================
FROM python:3.12-alpine

# Variables de entorno para optimización de Python en contenedores
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/code

WORKDIR /code

# 1. Crear usuario y grupo sin privilegios por motivos de seguridad
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# 2. Copiar e instalar dependencias antes del código para aprovechar la caché de capas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copiar únicamente el código fuente de la aplicación y scripts
COPY app/ ./app/
COPY scripts/ ./scripts/

# 4. Asignar propiedad de los archivos y activar usuario no privilegiado
RUN chown -R appuser:appgroup /code
USER appuser

# 5. Puerto de exposición del servicio
EXPOSE 8000

# 6. Comprobación de salud interna (HEALTHCHECK)
# Se utiliza estrictamente 127.0.0.1 en lugar de localhost debido a que Alpine
# resuelve localhost a IPv6 (::1) primero, mientras que uvicorn escucha en IPv4.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8000/health/ready || exit 1

# 7. Comando de arranque de la aplicación escuchando en todas las interfaces de red (0.0.0.0)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
