# Guía y Registro de Despliegue en Producción (DEPLOY.md)

Este documento registra los parámetros, configuraciones y procedimientos del despliegue oficial de la **Librería de Barrio** en el Servidor Privado Virtual (VPS) administrado mediante **Easypanel** para la **Evaluación Global de Integración y Despliegue — Programación III (UTN)**.

---

## 1. Ficha Técnica y Enlaces de Producción

* **URL Pública del Frontend (HTTPS):** [https://mananaarranco-libreria-ivy-frontend.fqtdaq.easypanel.host](https://mananaarranco-libreria-ivy-frontend.fqtdaq.easypanel.host)
* **Endpoint de Salud / Health Check (/api):** [https://mananaarranco-libreria-ivy-frontend.fqtdaq.easypanel.host/api/health/ready](https://mananaarranco-libreria-ivy-frontend.fqtdaq.easypanel.host/api/health/ready)
* **Repositorio Oficial en GitHub:** [https://github.com/IvanaGutierrez/Global-Programacion](https://github.com/IvanaGutierrez/Global-Programacion)
* **Proyecto en Easypanel:** `mananaarranco`

### Servicios Configurados en Easypanel:
1. **`libreria-ivy-db` (Base de Datos):**
   * Tipo: Servicio **Postgres** gestionado internamente por Easypanel.
   * Red: Privada interna del proyecto `mananaarranco`. Puerto 5432 no expuesto a internet.
2. **`libreria-ivy-backend` (API REST FastAPI):**
   * Tipo: Servicio **App**
   * Build Path: `/backend`
   * Builder: `Dockerfile`
   * Puerto interno: `8000` (sin dominio público directo, permanece en la red privada de Easypanel).
   * Variables de entorno:
     * `DATABASE_URL=postgresql+asyncpg://...` (conexión interna al servicio Postgres).
     * `CORS_ORIGINS=https://mananaarranco-libreria-ivy-frontend.fqtdaq.easypanel.host`
     * `SQL_ECHO=false`
3. **`libreria-ivy-frontend` (Servidor Web Nginx):**
   * Tipo: Servicio **App**
   * Build Path: `/frontend`
   * Builder: `Dockerfile`
   * Puerto interno: `80`
   * Protocolo: `HTTP` interno (Easypanel provee terminación TLS/HTTPS con certificado SSL automático).
   * Dominio público asignado: `mananaarranco-libreria-ivy-frontend.fqtdaq.easypanel.host`
   * Variable de enlace upstream:
     * `API_UPSTREAM=mananaarranco_libreria-ivy-backend:8000`

> 🔒 **Nota de Seguridad y Buenas Prácticas:**
> Siguiendo los principios de seguridad de la cátedra, **no se exponen contraseñas ni la cadena `DATABASE_URL` real** en este repositorio ni en la documentación pública. Las credenciales de acceso a la base de datos se configuran de forma estrictamente privada dentro de la sección **Environment** del servicio en Easypanel.

---

## 2. Documentos de Entrega y Evidencias

El repositorio cuenta con la documentación requerida por la cátedra para la corrección y evaluación:
* 📄 **Informe Integrador de la Evaluación:** [`Informe_Global_Programacion_Manana-Arranco.pdf`](file:///c:/Users/Ivana%20Gutierrez/Documents/Global-Programacion/Informe_Global_Programacion_Manana-Arranco.pdf) ubicado en la raíz del proyecto.
* 📑 **Evidencias de Casos de Prueba (G-01 a G-07):** [`evidencia/Evidencias_Global_Programacion_G01_G07.docx`](file:///c:/Users/Ivana%20Gutierrez/Documents/Global-Programacion/evidencia/Evidencias_Global_Programacion_G01_G07.docx) con capturas de pantalla y registros de consola de cada caso ejecutado sobre la URL pública en producción.

---

## 3. Configuración y Despliegue del Backend (`libreria-ivy-backend`)

### 3.1 Creación del servicio App
1. Dentro del proyecto `mananaarranco` en Easypanel, hacer clic en **New Service** $\rightarrow$ **App**.
2. Asignar el nombre `libreria-ivy-backend`.

### 3.2 Source y Build
* **Source:** Repositorio GitHub `https://github.com/IvanaGutierrez/Global-Programacion`, rama `main`.
* **Build Path:** `/backend`
* **Build Type:** `Dockerfile`
* **Dockerfile Path:** `Dockerfile`

### 3.3 Variables de Entorno (Environment)
```ini
DATABASE_URL=postgresql+asyncpg://<usuario>:<password>@libreria-ivy-db:5432/<nombre_db>
CORS_ORIGINS=https://mananaarranco-libreria-ivy-frontend.fqtdaq.easypanel.host
SQL_ECHO=false
```

> **Ciclo de vida y migraciones:** La aplicación utiliza el ciclo de vida asincrónico `lifespan` de FastAPI ejecutando `SQLModel.metadata.create_all` al arrancar. Todas las tablas, relaciones e índices se inicializan automáticamente e idempotentemente al iniciar el contenedor.

### 3.4 Carga Inicial de Datos (Seed)
1. Con el backend desplegado y en ejecución, abrir la pestaña **Shell** del servicio `libreria-ivy-backend`.
2. Ejecutar la siembra de datos ficticios:
   ```bash
   python -m scripts.seed
   ```
3. Comprobar que el endpoint de salud responde `200`:
   ```bash
   python -c "from urllib.request import urlopen; print(urlopen('http://127.0.0.1:8000/health/ready').status)"
   ```

---

## 4. Configuración y Despliegue del Frontend (`libreria-ivy-frontend`)

### 4.1 Creación del servicio App
1. En el proyecto `mananaarranco`, seleccionar **New Service** $\rightarrow$ **App**.
2. Asignar el nombre `libreria-ivy-frontend`.

### 4.2 Source y Build
* **Source:** Repositorio GitHub `https://github.com/IvanaGutierrez/Global-Programacion`, rama `main`.
* **Build Path:** `/frontend`
* **Build Type:** `Dockerfile`
* **Dockerfile Path:** `Dockerfile`

### 4.3 Variables de Entorno (Environment)
```ini
API_UPSTREAM=mananaarranco_libreria-ivy-backend:8000
```
> En la red interna de Docker creada por Easypanel para el proyecto `mananaarranco`, el servicio backend se resuelve bajo el nombre de host `mananaarranco_libreria-ivy-backend:8000`.

### 4.4 Configuración de Dominio (Domains)
1. En la pestaña **Domains**, configurar:
   * **Domain:** `mananaarranco-libreria-ivy-frontend.fqtdaq.easypanel.host`
   * **Port:** `80`
   * **Protocol:** `HTTP`
2. Guardar y pulsar **Deploy**. Easypanel genera automáticamente el certificado SSL mediante Let's Encrypt.

---

## 5. Verificación en Producción

1. **Prueba de Salud:**
   Abrir [https://mananaarranco-libreria-ivy-frontend.fqtdaq.easypanel.host/api/health/ready](https://mananaarranco-libreria-ivy-frontend.fqtdaq.easypanel.host/api/health/ready).
   Respuesta esperada (HTTP 200):
   ```json
   {
     "status": "ready",
     "database": "connected"
   }
   ```
2. **Navegación e Integración de Pantallas:**
   * **Catálogo:** Acceso a la página principal con paginación funcional y detalle de autores (`GET /api/libros/{id}`).
   * **Alta de Libros y Clientes:** Creación de registros y validación de restricciones únicas (ISBN y email devolviendo 409).
   * **Ventas e Historial:** Registro de ventas con dos renglones y consulta de comprobantes con precios unitarios históricos inmutables.

---

## 6. Procedimiento de Actualización sin Pérdida de Datos

La base de datos reside en el volumen persistente de `libreria-ivy-db`. Para actualizar el código:
1. Enviar los cambios al repositorio:
   ```bash
   git push origin main
   ```
2. En Easypanel, presionar **Deploy** sobre el servicio correspondiente (`libreria-ivy-backend` o `libreria-ivy-frontend`).
3. El contenedor se reconstruye y se levanta sin alterar las tablas ni los registros almacenados en PostgreSQL.

---

## 7. Diagnóstico Rápido

| Problema | Causa | Solución |
| :--- | :--- | :--- |
| **502 Bad Gateway en `/api/...`** | Nombre de upstream incorrecto o backend caído. | Verificar que `API_UPSTREAM` coincida con el nombre interno (`mananaarranco_libreria-ivy-backend:8000`) y que el backend esté en estado `running`. |
| **`/api/health/ready` responde 500** | Problema de conectividad con PostgreSQL. | Revisar que la variable `DATABASE_URL` use el host interno `libreria-ivy-db` y que las credenciales coincidan. |
| **404 Not Found en peticiones API** | Barra final ausente en rutas. | Verificar que las peticiones conserven la barra final (`/api/libros/`, `/api/ventas/`). En Nginx, `proxy_pass http://${API_UPSTREAM}/;` reenvía con la barra intacta. |
