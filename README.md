# Evaluación Global de Integración y Despliegue — Programación III (UTN)

## Proyecto: Librería de Barrio Web Integrada

Sistema web completo integrado y contenerizado para la gestión del catálogo, clientes, ventas e historial de la Librería de Barrio. Conecta el frontend desarrollado con **HTML5, CSS3 y JavaScript nativo** servido a través de un proxy reverso **Nginx**, con un backend asincrónico en **FastAPI**, **SQLModel** y **PostgreSQL**, desplegable en VPS mediante **Easypanel**.

---

## 👥 Datos del Grupo

* **Grupo:** Mañana-Arranco
* **Integrantes:**
  * Ivana Gutierrez
  * Julieta Chavez
  * Rayssa Alejo
  * Brisa Muñoz
* **Materia:** Programación III — Tecnicatura Universitaria en Programación (UTN)
* **Docente:** Mauro Dip

---

## 🏗️ Arquitectura del Sistema

```text
[ Navegador Web ]
       │
       ▼ (HTTP / HTTPS puerto 8080 o dominio público)
┌────────────────────────────────────────────────────────┐
│  FRONTEND (Contenedor Nginx 1.30-alpine)              │
│  ├── public/ (index.html, libros.html, etc., CSS, JS)  │
│  └── Nginx Proxy Reverso:                              │
│      ├── /     -> Archivos estáticos HTML/CSS/JS       │
│      └── /api/ -> http://${API_UPSTREAM}/              │
└──────────────────────────┬─────────────────────────────┘
                           │ (Red interna Docker / Easypanel)
                           ▼
┌────────────────────────────────────────────────────────┐
│  BACKEND (Contenedor Python 3.12-alpine)               │
│  ├── FastAPI asincrónico (puerto 8000)                 │
│  ├── app/main.py (CORS_ORIGINS dinámico, lifespan)     │
│  ├── Inicialización idempotente: SQLModel create_all   │
│  └── BackgroundTasks (aviso no bloqueante comprobante) │
└──────────────────────────┬─────────────────────────────┘
                           │ (postgresql+asyncpg)
                           ▼
┌────────────────────────────────────────────────────────┐
│  BASE DE DATOS (PostgreSQL 16)                        │
│  └── 9 modelos relacionales (Catálogo, Clientes,       │
│      Ventas, Renglones con precios históricos)         │
└────────────────────────────────────────────────────────┘
```

---

## 📂 Estructura del Repositorio

```text
Global-Programacion/
├── backend/
│   ├── app/
│   │   ├── core/               # config.py, database.py
│   │   ├── modules/            # libros, autores, editoriales, generos, clientes, ventas, health
│   │   └── main.py             # Instancia FastAPI, CORS dinámico, lifespan
│   ├── scripts/                # seed.py (siembra idempotente)
│   ├── test/                   # casos_parcial.http, tests de integración
│   ├── .dockerignore           # Exclusión de entornos, cache y secretos
│   ├── Dockerfile              # Imagen python:3.12-alpine con usuario sin privilegios
│   ├── env.example             # Ejemplo de variables de entorno
│   └── requirements.txt        # Dependencias Python
├── frontend/
│   ├── public/                 # Archivos estáticos web
│   │   ├── css/                # estilos.css
│   │   ├── js/                 # api.js (cliente HTTP centralizado), app.js
│   │   ├── img/                # Recursos gráficos locales
│   │   ├── index.html          # Catálogo con paginación, filtros y detalle
│   │   ├── libros.html         # Registro de libros y tabla de libros
│   │   ├── clientes.html       # Registro y buscador individual de clientes por ID
│   │   ├── ventas.html         # Composición y confirmación de ventas
│   │   └── historial.html      # Historial de ventas y detalle histórico
│   ├── .dockerignore           # Exclusión de archivos locales para build
│   ├── default.conf.template   # Plantilla Nginx con proxy_pass /api/
│   └── Dockerfile              # Imagen nginx:1.30-alpine con sustitución de variables
├── evidencia/                  # Capturas y registros de ejecución
├── DEPLOY.md                   # Documentación detallada del despliegue en VPS
├── README.md                   # Esta guía
└── Consignas Global.pdf
```

---

## ⚙️ Variables de Entorno

### Backend
| Variable | Descripción | Ejemplo / Valor por defecto |
| :--- | :--- | :--- |
| `DATABASE_URL` | Cadena de conexión asincrónica con driver `asyncpg`. **Obligatoria**. | `postgresql+asyncpg://postgres:postgres@localhost:5432/libreria_db` |
| `CORS_ORIGINS` | Orígenes HTTP permitidos separados por coma para `CORSMiddleware`. | `http://localhost:8080,http://127.0.0.1:8080,http://localhost:5173,http://localhost:3000` |
| `SQL_ECHO` | Booleano para activar registro de consultas SQL de SQLAlchemy. | `false` |

### Frontend (Nginx)
| Variable | Descripción | Ejemplo / Valor por defecto |
| :--- | :--- | :--- |
| `API_UPSTREAM` | Host y puerto interno del backend (sin `http://` ni barra final). | En local: `host.docker.internal:8000`<br>En Easypanel: `backend:8000` |

---

## 🚀 Guía de Ejecución Local Paso a Paso

### 1. Requisitos Previos
* Python 3.12+
* Docker Desktop instalado y corriendo
* PostgreSQL corriendo localmente o en un contenedor

### 2. Iniciar y Preparar el Backend
1. Abrir una terminal y posicionarse en `backend/`:
   ```bash
   cd backend
   ```
2. Crear y activar el entorno virtual:
   * **Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   * **Linux / macOS:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
3. Instalar las dependencias requeridas:
   ```bash
   pip install -r requirements.txt
   ```
4. Configurar el archivo `.env`:
   ```bash
   cp env.example .env
   ```
   Ajustar `DATABASE_URL` según su base PostgreSQL local.
5. Iniciar la API con Uvicorn:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
   > **Nota:** Al iniciar, el `lifespan` ejecuta `init_db(engine)` creando automáticamente todas las tablas relacionales que no existan en PostgreSQL.
6. En otra terminal con el entorno virtual activo, cargar los datos de prueba iniciales:
   ```bash
   python -m scripts.seed
   ```
   El script es **idempotente**: inserta editoriales, géneros, autores, libros de prueba y clientes sin duplicaciones.

### 3. Iniciar el Frontend con Docker y Nginx
1. Abrir otra terminal y posicionarse en `frontend/`:
   ```bash
   cd frontend
   ```
2. Construir la imagen Docker:
   ```bash
   docker build -t libreria-frontend .
   ```
3. Ejecutar el contenedor conectándolo a la API local:
   * **Windows / macOS (Docker Desktop con PowerShell):**
     ```powershell
     docker run --rm --name libreria-frontend -p 127.0.0.1:8080:80 -e API_UPSTREAM=host.docker.internal:8000 libreria-frontend
     ```
   * **Linux:**
     ```bash
     docker run --rm --name libreria-frontend -p 127.0.0.1:8080:80 --add-host=host.docker.internal:host-gateway -e API_UPSTREAM=host.docker.internal:8000 libreria-frontend
     ```
4. Abrir en el navegador:
   * `http://127.0.0.1:8080` (Catálogo principal)
   * `http://127.0.0.1:8080/api/health/ready` (Verificar respuesta `{"status":"ready","database":"connected"}`)

---

## 🧪 Casos de Prueba de la Evaluación (G-01 a G-07)

Los siguientes casos deben verificarse tanto localmente como sobre la URL pública desplegada en Easypanel:

| Caso | Acción a realizar | Resultado esperado y Comprobación |
| :--- | :--- | :--- |
| **G-01 · Catálogo** | 1. Ingresar a `index.html`.<br>2. Filtrar por título (ej. "Rayuela") y verificar listado.<br>3. Probar búsqueda sin coincidencias (ej. "xyzxyz").<br>4. Avanzar y retroceder con los botones de paginación.<br>5. Hacer clic en "Ver autores" o en el título de un libro. | Se visualiza título, ISBN, editorial, género ("Sin clasificar" si es nulo) y precio. Mensaje claro ante búsqueda sin coincidencias. Al abrir detalle, se consulta `GET /api/libros/{id}` mostrando autorías con rol y orden. |
| **G-02 · Alta de libro** | 1. Ingresar a `libros.html`.<br>2. Seleccionar editorial y género.<br>3. Consultar un autor existente por ID (ej. 1) y agregarlo con rol "autor" y orden 1.<br>4. Enviar formulario con stock > 0.<br>5. Reintentar con el mismo ISBN. | En el alta válida, la API responde `201 Created` y el libro aparece en el catálogo. Al repetir el ISBN, la API rechaza con `409 Conflict` y el mensaje se muestra en `#msg-error`. |
| **G-03 · Alta de cliente** | 1. Ingresar a `clientes.html`.<br>2. Registrar cliente con nombre y email nuevo.<br>3. Reintentar con el mismo correo.<br>4. En "Consultar cliente por ID", ingresar el ID generado. | El alta exitosa devuelve `201 Created` con el ID asignado. El email repetido devuelve `409 Conflict`. La consulta individual por ID (`GET /api/clientes/{id}`) recupera los datos correctos del cliente. |
| **G-04 · Venta** | 1. Ingresar a `ventas.html`.<br>2. Ingresar ID de cliente (ej. 1) y pulsar "Buscar cliente".<br>3. Agregar dos libros distintos con cantidades positivas.<br>4. Confirmar la venta.<br>5. Recargar la página e ir a `historial.html`. | El botón se deshabilita mientras se procesa. La API responde `201 Created`, calculando el total y copiando precios unitarios. Tras recargar, la venta aparece en el historial con el mismo total y detalle. |
| **G-05 · Precio histórico** | 1. Modificar el precio de uno de los libros vendidos mediante `PATCH /libros/{id}`.<br>2. Ir a `historial.html` y abrir el detalle de la venta registrada en G-04. | La venta anterior conserva sus precios unitarios y subtotales históricos intactos en los renglones, demostrando inmutabilidad contable (RN-08). |
| **G-06 · Rechazo** | 1. En `ventas.html`, intentar enviar una venta con cliente inexistente (ID 9999).<br>2. Intentar venta con renglones de libros duplicados. | La API responde `409 Conflict` ante cliente inexistente y `422 Unprocessable Entity` ante renglones con libro duplicado. **El borrador de la venta se conserva en memoria** para permitir corrección. |
| **G-07 · Despliegue** | 1. Acceder a la URL pública asignada en Easypanel por HTTPS.<br>2. Verificar `/api/health/ready`.<br>3. Redesplegar el servicio backend. | La URL abre con candado SSL válido, la salud responde `200 OK`, y los datos persisten en la base de datos tras el redespliegue sin pérdidas. |
