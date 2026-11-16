# Guía de Despliegue en VPS con Easypanel (DEPLOY.md)

Este documento detalla el procedimiento completo, parámetros y configuraciones para desplegar la solución integrada **Librería de Barrio** en un Servidor Privado Virtual (VPS) administrado mediante **Easypanel**.

---

## 1. Ficha Técnica del Despliegue

* **Proyecto en Easypanel:** `global-libreria` (o nombre asignado al grupo)
* **Servicio Backend:**
  * **Nombre del servicio:** `backend`
  * **Build Path:** `/backend`
  * **Builder:** `Dockerfile` (ruta relativa `Dockerfile`)
  * **Puerto interno:** `8000` (privado, sin dominio público)
* **Servicio Frontend:**
  * **Nombre del servicio:** `frontend`
  * **Build Path:** `/frontend`
  * **Builder:** `Dockerfile` (ruta relativa `Dockerfile`)
  * **Puerto interno:** `80`
  * **Protocolo:** `HTTP` (Easypanel gestiona el certificado SSL y la terminación HTTPS hacia internet)
* **Proxy y Upstream:**
  * Variable en Frontend: `API_UPSTREAM=backend:8000`
  * Nginx reenvía `/api/` hacia `http://${API_UPSTREAM}/`
* **Base de Datos:**
  * Servicio PostgreSQL administrado por Easypanel (en la misma red interna).
  * Variable en Backend: `DATABASE_URL=postgresql+asyncpg://...`

---

## 2. Paso a Paso: Configuración del Servicio Backend

### 2.1 Creación del servicio App
1. Dentro del proyecto en Easypanel, hacer clic en **New Service** $\rightarrow$ **App**.
2. Nombrar el servicio como `backend`.

### 2.2 Configuración de Source y Build
* **Source:** Seleccionar el repositorio Git del proyecto y la rama a desplegar (ej. `main`).
* **Build Path:** Escribir `/backend`.
* **Build Type:** Seleccionar `Dockerfile`.
* **Dockerfile Path:** `Dockerfile`.

### 2.3 Variables de Entorno (Environment)
Cargar las siguientes variables en la pestaña **Environment**:

```ini
DATABASE_URL=postgresql+asyncpg://<usuario>:<password>@<host_postgres_interno>:5432/<nombre_db>
CORS_ORIGINS=*
SQL_ECHO=false
```
> **Nota sobre Base de Datos y Migraciones:** La API utiliza el ciclo de vida asincrónico `lifespan` de FastAPI, ejecutando `SQLModel.metadata.create_all` al arrancar. Por lo tanto, no se requiere ejecutar scripts manuales ni Alembic; todas las tablas, restricciones e índices se generan automáticamente de forma idempotente en el primer inicio.

### 2.4 Despliegue y Carga de Datos Iniciales (Seed)
1. Hacer clic en **Deploy** y observar los logs de construcción y arranque de Uvicorn en `0.0.0.0:8000`.
2. Una vez que el contenedor esté corriendo, abrir la pestaña **Shell** (Terminal interna del contenedor) y ejecutar:
   ```bash
   python -m scripts.seed
   ```
3. Verificar la salud de la API desde la misma consola:
   ```bash
   python -c "from urllib.request import urlopen; print(urlopen('http://127.0.0.1:8000/health/ready').status)"
   ```
   El comando debe imprimir `200`.

---

## 3. Paso a Paso: Configuración del Servicio Frontend

### 3.1 Creación del servicio App
1. En el mismo proyecto de Easypanel, hacer clic en **New Service** $\rightarrow$ **App**.
2. Nombrar el servicio como `frontend`.

### 3.2 Configuración de Source y Build
* **Source:** El mismo repositorio Git y rama.
* **Build Path:** Escribir `/frontend`.
* **Build Type:** Seleccionar `Dockerfile`.
* **Dockerfile Path:** `Dockerfile`.

### 3.3 Variables de Entorno (Environment)
Configurar la variable de enlace con el backend:

```ini
API_UPSTREAM=backend:8000
```
> Si Easypanel nombra los servicios con prefijo de proyecto (por ejemplo `grupo1_backend`), ajustar a `API_UPSTREAM=grupo1_backend:8000`.

### 3.4 Configuración de Dominio (Domains)
1. En la pestaña **Domains**, asignar el dominio público HTTPS asignado por la cátedra o por Easypanel (ej. `libreria.miapp.com`).
2. Configurar:
   * **Port:** `80`
   * **Protocol:** `HTTP`
3. Guardar los cambios y pulsar **Deploy**.

---

## 4. Verificación y Pruebas en Producción

Una vez completado el despliegue del frontend:
1. **Comprobar Endpoint de Salud:**
   Abrir en el navegador:
   `https://<dominio-frontend>/api/health/ready`
   Debe responder con código HTTP 200 y el JSON:
   ```json
   {"status": "ready", "database": "connected"}
   ```
2. **Probar Interfaz Web:**
   Abrir `https://<dominio-frontend>`:
   * El catálogo debe listar los libros cargados con el script de siembra.
   * El detalle de autorías debe abrirse consultando `/api/libros/{id}`.
   * Probar el registro de una venta con 2 renglones desde `ventas.html` y verificar su aparición en `historial.html`.

---

## 5. Procedimiento de Actualización sin Pérdida de Datos

Dado que la base de datos PostgreSQL reside en un volumen persistente independiente de los contenedores de aplicación:

1. **Actualización de Código:**
   Hacer `git push` con los nuevos cambios a la rama principal.
2. **Redespliegue en Easypanel:**
   * En el servicio modificado (`backend` o `frontend`), presionar **Deploy**.
   * Easypanel reconstruye la imagen y reemplaza el contenedor sin tiempo de inactividad perceptivo.
   * Al iniciar el backend, `create_all` detecta las tablas existentes sin reiniciarlas ni borrar registros.

---

## 6. Guía de Diagnóstico y Resolución de Problemas

| Síntoma | Causa Probable | Solución |
| :--- | :--- | :--- |
| **Falla en el build: COPY failed** | Rutas incorrectas o archivos fuera de contexto. | Verificar que en el servicio de Easypanel el **Build Path** sea exactamente `/frontend` (o `/backend`), y que la carpeta `public/` esté dentro de `frontend/`. |
| **Error 502 Bad Gateway al llamar `/api/...`** | Nginx no puede comunicarse con el backend. | 1. Revisar los logs del backend para asegurar que esté escuchando en `0.0.0.0:8000`.<br>2. Verificar el valor de `API_UPSTREAM` en el frontend (debe coincidir con el nombre interno del servicio backend en Easypanel, ej. `backend:8000`). |
| **`/api/health/ready` devuelve error 500** | Falla de conexión a PostgreSQL. | Verificar la variable `DATABASE_URL` en el backend, revisando usuario, contraseña y host interno de PostgreSQL. |
| **Petición devuelve 404 Not Found** | Desajuste en el prefijo o barra final. | Revisar en la pestaña Red de las herramientas de desarrollador que la URL solicitada conserve la barra final requerida (ej. `/api/libros/`). En Nginx, `proxy_pass http://${API_UPSTREAM}/;` con barra final reemplaza `/api/` por `/`. |
