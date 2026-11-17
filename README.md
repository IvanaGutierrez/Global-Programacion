# Evaluación Global de Integración y Despliegue — Programación III (UTN)

## Proyecto: Librería de Barrio Web Integrada

Sistema web completo integrado y contenerizado para la gestión del catálogo, clientes, ventas e historial de la Librería de Barrio. Conecta el frontend desarrollado con **HTML5, CSS3 y JavaScript nativo** servido a través de un proxy reverso **Nginx**, con un backend asincrónico en **FastAPI**, **SQLModel** y **PostgreSQL**, desplegado en producción en VPS mediante **Easypanel**.

---

## 🌐 Enlaces de Producción y Repositorio

* **URL Pública del Frontend (HTTPS):** [https://mananaarranco-libreria-ivy-frontend.fqtdaq.easypanel.host](https://mananaarranco-libreria-ivy-frontend.fqtdaq.easypanel.host)
* **Endpoint de Salud / Health Check (/api):** [https://mananaarranco-libreria-ivy-frontend.fqtdaq.easypanel.host/api/health/ready](https://mananaarranco-libreria-ivy-frontend.fqtdaq.easypanel.host/api/health/ready)
* **Repositorio Oficial en GitHub:** [https://github.com/IvanaGutierrez/Global-Programacion](https://github.com/IvanaGutierrez/Global-Programacion)
* **Proyecto en Easypanel:** `mananaarranco`
  * `libreria-ivy-db`: Base de datos PostgreSQL 16 privada.
  * `libreria-ivy-backend`: API FastAPI en puerto 8000 con `CORS_ORIGINS=https://mananaarranco-libreria-ivy-frontend.fqtdaq.easypanel.host`.
  * `libreria-ivy-frontend`: Servidor Nginx en puerto 80 con `API_UPSTREAM=mananaarranco_libreria-ivy-backend:8000`.

> 🔒 **Aclaración de Seguridad:** Por políticas de seguridad y consigna de la cátedra, **no se exponen contraseñas ni la cadena `DATABASE_URL` real** en el repositorio ni en la documentación. Todas las credenciales permanecen en las variables de entorno privadas configuradas en Easypanel.

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

## 📑 Documentos de Entrega y Evidencias

* 📄 **Informe Integrador de Evaluación:** [`Informe_Global_Programacion_Manana-Arranco.pdf`](file:///c:/Users/Ivana%20Gutierrez/Documents/Global-Programacion/Informe_Global_Programacion_Manana-Arranco.pdf) ubicado en la raíz del proyecto.
* 📑 **Evidencias de Casos de Prueba (G-01 a G-07):** [`evidencia/Evidencias_Global_Programacion_G01_G07.docx`](file:///c:/Users/Ivana%20Gutierrez/Documents/Global-Programacion/evidencia/Evidencias_Global_Programacion_G01_G07.docx) con capturas de pantalla, pasos y respuestas observadas en la URL pública de producción.

---

## 🏗️ Arquitectura del Sistema

```text
[ Navegador Web ]
       │
       ▼ (HTTPS / Puerto 443 / 80 en producción o 8080 en local)
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
│   ├── env.example             # Ejemplo de variables de entorno (sin credenciales)
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
├── evidencia/
│   └── Evidencias_Global_Programacion_G01_G07.docx  # Evidencias en producción
├── .gitignore                  # Exclusión estricta de .env, .venv y temporales
├── DEPLOY.md                   # Documentación detallada del despliegue en VPS
├── Informe_Global_Programacion_Manana-Arranco.pdf   # Informe formal del proyecto
├── README.md                   # Esta guía
└── Consignas Global.pdf        # Consignas oficiales de la cátedra
```

---

## ⚙️ Variables de Entorno

### Backend
| Variable | Descripción | Ejemplo en Local | Configuración en Producción |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | Cadena asincrónica con driver `asyncpg`. **Obligatoria**. | `postgresql+asyncpg://postgres:postgres@localhost:5432/libreria_db` | `postgresql+asyncpg://<usr>:<pwd>@libreria-ivy-db:5432/<db>` |
| `CORS_ORIGINS` | Orígenes HTTP permitidos (separados por coma). | `http://localhost:8080,http://127.0.0.1:8080` | `https://mananaarranco-libreria-ivy-frontend.fqtdaq.easypanel.host` |
| `SQL_ECHO` | Booleano para registro de consultas SQL de SQLAlchemy. | `true` | `false` |

### Frontend (Nginx)
| Variable | Descripción | Ejemplo en Local | Configuración en Producción |
| :--- | :--- | :--- | :--- |
| `API_UPSTREAM` | Host y puerto interno del backend (sin `http://` ni `/`). | `host.docker.internal:8000` | `mananaarranco_libreria-ivy-backend:8000` |

---

## 🚀 Guía de Ejecución Local Paso a Paso

### 1. Requisitos Previos
* Python 3.12+
* Docker Desktop instalado y corriendo
* PostgreSQL corriendo localmente o en un contenedor

### 2. Iniciar y Preparar el Backend
1. Posicionarse en `backend/`:
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
1. Posicionarse en `frontend/`:
   ```bash
   cd ../frontend
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

Los siguientes casos fueron ejecutados y validados sobre la URL pública en producción ([https://mananaarranco-libreria-ivy-frontend.fqtdaq.easypanel.host](https://mananaarranco-libreria-ivy-frontend.fqtdaq.easypanel.host)):

| Caso | Acción Realizada en Producción | Resultado Observado |
| :--- | :--- | :--- |
| **G-01 · Catálogo** | Búsqueda por título, paginación con `limit` y `offset`, prueba de búsqueda sin coincidencias y apertura de detalle de libro. | Título, ISBN, editorial, género ("Sin clasificar" si es nulo) y precio visibles. Al abrir detalle, se consulta `GET /api/libros/{id}` mostrando autorías completas con rol y orden. |
| **G-02 · Alta de libro** | Alta con stock > 0, género opcional y autor validado por ID. Reintento con ISBN repetido. | El libro se crea con HTTP 201 y se actualiza el catálogo. El reintento con el mismo ISBN es rechazado con HTTP 409 Conflict. |
| **G-03 · Alta de cliente** | Creación de cliente nuevo, reintento con el mismo correo y consulta individual por ID. | Creación exitosa (HTTP 201). El email duplicado devuelve HTTP 409 con el detalle correspondiente. La consulta `GET /api/clientes/{id}` recupera los datos correctos. |
| **G-04 · Venta** | Selección de cliente validado por ID, composición de 2 renglones de libros y confirmación. | Botón deshabilitado durante el envío. La API responde HTTP 201 calculando el total y copiando precios unitarios. Tras recargar, la venta persiste en el historial. |
| **G-05 · Precio histórico** | Actualización de precio de libro con `PATCH /libros/{id}` y verificación en `historial.html`. | La venta previamente registrada conserva sus precios unitarios y subtotales históricos intactos (inmutabilidad contable, RN-08). |
| **G-06 · Rechazo** | Envío de venta con cliente inexistente (ID 9999) y prueba de renglones con libro duplicado. | La API devuelve HTTP 409 ante cliente inexistente y HTTP 422 ante libros duplicados. El borrador de la venta se mantiene intacto en memoria. |
| **G-07 · Despliegue** | Verificación de construcción de imágenes, navegación por HTTPS, respuesta 200 en `/api/health/ready` y persistencia tras redespliegue. | Despliegue operativo y verificado en Easypanel bajo dominio con certificado SSL válido y base de datos persistente. |
