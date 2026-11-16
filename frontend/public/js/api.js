// frontend/public/js/api.js — Cliente HTTP centralizado para la API REST de la Librería
// Cumple con el contrato de FastAPI y las especificaciones de la Evaluación Global de Programación III (UTN)
"use strict";

const API_BASE_URL = "/api";

/**
 * Función genérica para realizar peticiones HTTP con fetch nativo.
 * Maneja timeouts lógicos, parseo de JSON, extracción limpia de errores 409 y 422,
 * y diferenciación de errores de conexión de red.
 */
async function apiFetch(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const defaultHeaders = {
        "Accept": "application/json",
    };

    if (options.body && typeof options.body === "string") {
        defaultHeaders["Content-Type"] = "application/json";
    }

    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...(options.headers || {}),
        },
    };

    let response;
    try {
        response = await fetch(url, config);
    } catch (networkError) {
        const error = new Error("Error de conexión: No se pudo comunicar con el servidor. Verifique que el servicio backend esté activo.");
        error.isNetworkError = true;
        error.status = 0;
        throw error;
    }

    let responseData = null;
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
        try {
            responseData = await response.json();
        } catch (e) {
            responseData = null;
        }
    } else {
        try {
            responseData = await response.text();
        } catch (e) {
            responseData = null;
        }
    }

    if (!response.ok) {
        let mensaje = `Error HTTP ${response.status}`;

        if (responseData && typeof responseData === "object") {
            // Manejo de HTTP 409 (Conflict) o HTTP 404 (Not Found) con { "detail": "string" }
            if (typeof responseData.detail === "string") {
                mensaje = responseData.detail;
            }
            // Manejo de HTTP 422 (Unprocessable Entity) de FastAPI / Pydantic
            else if (Array.isArray(responseData.detail)) {
                mensaje = responseData.detail
                    .map(function (item) {
                        let msg = item.msg || JSON.stringify(item);
                        // Limpieza del prefijo estándar de Pydantic
                        if (msg.startsWith("Value error, ")) {
                            msg = msg.substring("Value error, ".length);
                        }
                        const campo = item.loc && item.loc.length > 0 ? item.loc[item.loc.length - 1] : "";
                        return campo && campo !== "body" ? `${campo}: ${msg}` : msg;
                    })
                    .join("; ");
            }
        }

        const httpError = new Error(mensaje);
        httpError.status = response.status;
        httpError.data = responseData;
        throw httpError;
    }

    return responseData;
}

// Objeto API centralizado expuesto globalmente
window.api = {
    // -------------------------------------------------------------
    // Salud del servicio
    // -------------------------------------------------------------
    async checkHealthReady() {
        return apiFetch("/health/ready");
    },

    // -------------------------------------------------------------
    // Módulo Catálogo / Libros
    // Conserva barra final obligatoria en listados: /api/libros/
    // -------------------------------------------------------------
    async getLibros({ limit = 20, offset = 0, titulo = null, genero_id = null } = {}) {
        const params = new URLSearchParams();
        params.append("limit", limit.toString());
        params.append("offset", offset.toString());

        if (titulo && titulo.trim() !== "") {
            params.append("titulo", titulo.trim());
        }
        if (genero_id !== null && genero_id !== undefined && genero_id !== "") {
            params.append("genero_id", genero_id.toString());
        }

        return apiFetch(`/libros/?${params.toString()}`);
    },

    async getLibroById(id) {
        return apiFetch(`/libros/${encodeURIComponent(id)}`);
    },

    async createLibro(data) {
        return apiFetch("/libros/", {
            method: "POST",
            body: JSON.stringify(data),
        });
    },

    // -------------------------------------------------------------
    // Módulo Editoriales y Géneros
    // -------------------------------------------------------------
    async getEditoriales({ limit = 100, offset = 0 } = {}) {
        return apiFetch(`/editoriales/?limit=${limit}&offset=${offset}`);
    },

    async getGeneros() {
        return apiFetch("/generos/");
    },

    // -------------------------------------------------------------
    // Módulo Autores (solo consulta individual por ID según contrato)
    // -------------------------------------------------------------
    async getAutorById(id) {
        return apiFetch(`/autores/${encodeURIComponent(id)}`);
    },

    // -------------------------------------------------------------
    // Módulo Clientes (alta y consulta individual por ID)
    // -------------------------------------------------------------
    async getClienteById(id) {
        return apiFetch(`/clientes/${encodeURIComponent(id)}`);
    },

    async createCliente(data) {
        return apiFetch("/clientes/", {
            method: "POST",
            body: JSON.stringify(data),
        });
    },

    // -------------------------------------------------------------
    // Módulo Ventas
    // Conserva barra final obligatoria: /api/ventas/
    // -------------------------------------------------------------
    async getVentas({ limit = 20, offset = 0 } = {}) {
        return apiFetch(`/ventas/?limit=${limit}&offset=${offset}`);
    },

    async getVentaById(id) {
        return apiFetch(`/ventas/${encodeURIComponent(id)}`);
    },

    async createVenta(data) {
        return apiFetch("/ventas/", {
            method: "POST",
            body: JSON.stringify(data),
        });
    },
};
