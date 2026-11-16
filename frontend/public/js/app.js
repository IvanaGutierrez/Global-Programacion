// frontend/public/js/app.js — Orquestación completa de la UI con JavaScript nativo y API REST
// Evaluación Global de Programación III (UTN) — Integración de Catálogo, Libros, Clientes, Ventas e Historial
"use strict";

// =============================================================================
// 1. UTILIDADES Y FORMATEO
// =============================================================================

function redondear2(numero) {
    return Math.round(Number(numero) * 100) / 100;
}

function formatearImporte(numero) {
    const val = Number(numero);
    return isNaN(val) ? "0.00" : val.toFixed(2);
}

function formatearFecha(fechaStr) {
    if (!fechaStr) return "";
    try {
        const d = new Date(fechaStr);
        if (isNaN(d.getTime())) return fechaStr;
        const dia = String(d.getDate()).padStart(2, "0");
        const mes = String(d.getMonth() + 1).padStart(2, "0");
        const anio = d.getFullYear();
        const horas = String(d.getHours()).padStart(2, "0");
        const minutos = String(d.getMinutes()).padStart(2, "0");
        return `${dia}/${mes}/${anio} ${horas}:${minutos}`;
    } catch (e) {
        return fechaStr;
    }
}

function mostrarMensajeOk(texto, idOk = "msg-ok", idError = "msg-error") {
    const mensajeOk = document.getElementById(idOk);
    const mensajeError = document.getElementById(idError);
    if (mensajeError) {
        mensajeError.textContent = "";
        mensajeError.hidden = true;
    }
    if (mensajeOk) {
        mensajeOk.textContent = texto;
        mensajeOk.hidden = false;
        mensajeOk.style.color = "var(--exito, #1E7A34)";
    }
}

function mostrarMensajeError(texto, idOk = "msg-ok", idError = "msg-error") {
    const mensajeOk = document.getElementById(idOk);
    const mensajeError = document.getElementById(idError);
    if (mensajeOk) {
        mensajeOk.textContent = "";
        mensajeOk.hidden = true;
    }
    if (mensajeError) {
        mensajeError.textContent = texto;
        mensajeError.hidden = false;
        mensajeError.style.color = "var(--error, #B3261E)";
    }
}

function limpiarMensajes(idOk = "msg-ok", idError = "msg-error") {
    const mensajeOk = document.getElementById(idOk);
    const mensajeError = document.getElementById(idError);
    if (mensajeOk) {
        mensajeOk.textContent = "";
        mensajeOk.hidden = true;
    }
    if (mensajeError) {
        mensajeError.textContent = "";
        mensajeError.hidden = true;
    }
}

// =============================================================================
// 2. MÓDULO CATÁLOGO (index.html)
// =============================================================================

let catalogoOffset = 0;
const catalogoLimit = 20;
let catalogoFiltroTitulo = "";

async function cargarCatalogo() {
    const tabla = document.getElementById("catalogo-listado");
    if (!tabla) return;

    const tbody = tabla.querySelector("tbody");
    const msgEstado = document.getElementById("catalogo-mensaje");
    const msgVacio = document.getElementById("catalogo-vacio");
    const btnPrev = document.getElementById("btn-catalogo-prev");
    const btnNext = document.getElementById("btn-catalogo-next");
    const pagInfo = document.getElementById("catalogo-pagina-info");

    if (tbody) tbody.replaceChildren();

    // 1. Estado "Cargando"
    if (msgEstado) {
        msgEstado.textContent = "Cargando catálogo...";
        msgEstado.hidden = false;
    }
    if (msgVacio) msgVacio.hidden = true;

    try {
        const libros = await window.api.getLibros({
            limit: catalogoLimit,
            offset: catalogoOffset,
            titulo: catalogoFiltroTitulo,
        });

        // Ocultar mensaje de carga
        if (msgEstado) {
            msgEstado.hidden = true;
            msgEstado.textContent = "";
        }

        // 2. Estado "Lista vacía" vs "Búsqueda sin coincidencias"
        if (!libros || libros.length === 0) {
            if (catalogoFiltroTitulo && catalogoFiltroTitulo.trim() !== "") {
                // Búsqueda sin coincidencias
                if (msgEstado) {
                    msgEstado.textContent = `Sin resultados para la búsqueda «${catalogoFiltroTitulo}».`;
                    msgEstado.hidden = false;
                }
            } else if (catalogoOffset === 0) {
                // Lista vacía general
                if (msgVacio) {
                    msgVacio.textContent = "No hay registros en el catálogo.";
                    msgVacio.hidden = false;
                }
            }
            if (btnNext) btnNext.disabled = true;
            if (btnPrev) btnPrev.disabled = catalogoOffset === 0;
            if (pagInfo) {
                pagInfo.textContent = `Página ${Math.floor(catalogoOffset / catalogoLimit) + 1}`;
            }
            return;
        }

        if (msgVacio) msgVacio.hidden = true;

        // Renderizado de filas
        libros.forEach(function (libro) {
            const fila = document.createElement("tr");

            // Título con enlace interactivo para consultar autores vía GET /api/libros/{id}
            const celdaTitulo = document.createElement("td");
            const linkTitulo = document.createElement("a");
            linkTitulo.href = "#catalogo-detalle-contenedor";
            linkTitulo.textContent = libro.titulo;
            linkTitulo.style.cursor = "pointer";
            linkTitulo.title = "Haga clic para consultar autores y detalle completo";
            linkTitulo.addEventListener("click", function (e) {
                e.preventDefault();
                verDetalleLibroCatalogo(libro.id);
            });
            celdaTitulo.appendChild(linkTitulo);
            fila.appendChild(celdaTitulo);

            const celdaIsbn = document.createElement("td");
            celdaIsbn.textContent = libro.isbn;
            fila.appendChild(celdaIsbn);

            const celdaEditorial = document.createElement("td");
            celdaEditorial.textContent = libro.editorial ? libro.editorial.nombre : "Sin editorial";
            fila.appendChild(celdaEditorial);

            const celdaGenero = document.createElement("td");
            celdaGenero.textContent = libro.genero ? libro.genero.nombre : "Sin clasificar";
            fila.appendChild(celdaGenero);

            // Celda Autores: botón de carga rápida de detalle
            const celdaAutores = document.createElement("td");
            const btnVerAutores = document.createElement("button");
            btnVerAutores.type = "button";
            btnVerAutores.textContent = "Ver autores";
            btnVerAutores.style.fontSize = "0.85rem";
            btnVerAutores.addEventListener("click", function () {
                verDetalleLibroCatalogo(libro.id);
            });
            celdaAutores.appendChild(btnVerAutores);
            fila.appendChild(celdaAutores);

            const celdaPrecio = document.createElement("td");
            celdaPrecio.textContent = formatearImporte(libro.precio);
            fila.appendChild(celdaPrecio);

            tbody.appendChild(fila);
        });

        // Paginación
        if (btnPrev) btnPrev.disabled = catalogoOffset === 0;
        if (btnNext) btnNext.disabled = libros.length < catalogoLimit;
        if (pagInfo) {
            pagInfo.textContent = `Página ${Math.floor(catalogoOffset / catalogoLimit) + 1}`;
        }

    } catch (error) {
        // 4. Estado "Error de conexión"
        if (msgEstado) {
            msgEstado.textContent = error.isNetworkError
                ? "Error de conexión: No se pudo comunicar con el servidor."
                : `Error al cargar catálogo: ${error.message}`;
            msgEstado.hidden = false;
        }
        if (btnNext) btnNext.disabled = true;
        if (btnPrev) btnPrev.disabled = true;
    }
}

async function verDetalleLibroCatalogo(id) {
    const contenedor = document.getElementById("catalogo-detalle-contenedor");
    const divDetalle = document.getElementById("catalogo-libro-detalle");
    if (!contenedor || !divDetalle) return;

    divDetalle.replaceChildren();
    const avisoCarga = document.createElement("p");
    avisoCarga.textContent = `Consultando detalle del libro #${id}...`;
    divDetalle.appendChild(avisoCarga);
    contenedor.hidden = false;

    try {
        const libro = await window.api.getLibroById(id);
        divDetalle.replaceChildren();

        const titulo = document.createElement("h4");
        titulo.textContent = `${libro.titulo} (ID: ${libro.id})`;
        titulo.style.margin = "0 0 0.5rem 0";
        divDetalle.appendChild(titulo);

        const info = document.createElement("p");
        info.innerHTML = `<strong>ISBN:</strong> ${libro.isbn} | <strong>Editorial:</strong> ${libro.editorial.nombre} | <strong>Género:</strong> ${libro.genero ? libro.genero.nombre : "Sin clasificar"} | <strong>Stock:</strong> ${libro.stock} | <strong>Precio:</strong> $${formatearImporte(libro.precio)}`;
        divDetalle.appendChild(info);

        const subAutores = document.createElement("h5");
        subAutores.textContent = "Autorías registradas (GET /api/libros/{id}):";
        subAutores.style.margin = "0.75rem 0 0.25rem 0";
        divDetalle.appendChild(subAutores);

        if (!libro.autores || libro.autores.length === 0) {
            const sinAutores = document.createElement("p");
            sinAutores.textContent = "No registra autorías.";
            divDetalle.appendChild(sinAutores);
        } else {
            const ul = document.createElement("ul");
            ul.style.paddingLeft = "1.25rem";
            libro.autores.forEach(function (a) {
                const li = document.createElement("li");
                li.textContent = `${a.nombre} (${a.nacionalidad}) — Rol: ${a.rol}, Orden: ${a.orden} (ID Autor: ${a.autor_id})`;
                ul.appendChild(li);
            });
            divDetalle.appendChild(ul);
        }

        const btnCerrar = document.createElement("button");
        btnCerrar.type = "button";
        btnCerrar.textContent = "Cerrar detalle";
        btnCerrar.style.marginTop = "0.5rem";
        btnCerrar.addEventListener("click", function () {
            contenedor.hidden = true;
        });
        divDetalle.appendChild(btnCerrar);

    } catch (err) {
        divDetalle.replaceChildren();
        const errorP = document.createElement("p");
        errorP.style.color = "var(--error, #B3261E)";
        errorP.textContent = `Error al obtener detalle del libro: ${err.message}`;
        divDetalle.appendChild(errorP);
    }
}

function inicializarCatalogo() {
    const formBuscador = document.getElementById("form-buscador");
    const inputBuscador = document.getElementById("buscador-titulo");
    const btnPrev = document.getElementById("btn-catalogo-prev");
    const btnNext = document.getElementById("btn-catalogo-next");

    if (formBuscador) {
        formBuscador.addEventListener("submit", function (e) {
            e.preventDefault();
            catalogoFiltroTitulo = inputBuscador ? inputBuscador.value.trim() : "";
            catalogoOffset = 0; // Reinicio obligatorio de desplazamiento al filtrar
            cargarCatalogo();
        });
    }

    if (btnPrev) {
        btnPrev.addEventListener("click", function () {
            if (catalogoOffset >= catalogoLimit) {
                catalogoOffset -= catalogoLimit;
                cargarCatalogo();
            }
        });
    }

    if (btnNext) {
        btnNext.addEventListener("click", function () {
            catalogoOffset += catalogoLimit;
            cargarCatalogo();
        });
    }

    cargarCatalogo();
}

// =============================================================================
// 3. MÓDULO ALTA DE LIBROS (libros.html)
// =============================================================================

let autoresAltaLibro = []; // Array en memoria: [{ autor_id, nombre, rol, orden }]
let ultimoAutorVerificado = null;

async function cargarSelectoresLibro() {
    const selEditorial = document.getElementById("libro-editorial");
    const selGenero = document.getElementById("libro-genero");

    if (selEditorial) {
        try {
            const editoriales = await window.api.getEditoriales({ limit: 100 });
            selEditorial.replaceChildren();
            const opcVacia = document.createElement("option");
            opcVacia.value = "";
            opcVacia.textContent = "-- Seleccione editorial --";
            selEditorial.appendChild(opcVacia);

            editoriales.forEach(function (ed) {
                const opc = document.createElement("option");
                opc.value = ed.id;
                opc.textContent = ed.nombre;
                selEditorial.appendChild(opc);
            });
        } catch (e) {
            console.error("Error al cargar editoriales", e);
        }
    }

    if (selGenero) {
        try {
            const generos = await window.api.getGeneros();
            selGenero.replaceChildren();
            const opcSin = document.createElement("option");
            opcSin.value = "";
            opcSin.textContent = "Sin clasificar (opcional)";
            selGenero.appendChild(opcSin);

            generos.forEach(function (g) {
                const opc = document.createElement("option");
                opc.value = g.id;
                opc.textContent = g.nombre;
                selGenero.appendChild(opc);
            });
        } catch (e) {
            console.error("Error al cargar géneros", e);
        }
    }
}

async function renderizarCatalogoEnLibros() {
    const tabla = document.getElementById("libros-listado");
    if (!tabla) return;
    const tbody = tabla.querySelector("tbody");
    const vacio = document.getElementById("libros-vacio");
    if (tbody) tbody.replaceChildren();

    try {
        const libros = await window.api.getLibros({ limit: 100 });
        if (!libros || libros.length === 0) {
            if (vacio) {
                vacio.textContent = "No hay registros de libros.";
                vacio.hidden = false;
            }
            return;
        }

        if (vacio) vacio.hidden = true;

        libros.forEach(function (libro) {
            const fila = document.createElement("tr");

            const celdaTitulo = document.createElement("td");
            celdaTitulo.textContent = libro.titulo;
            fila.appendChild(celdaTitulo);

            const celdaIsbn = document.createElement("td");
            celdaIsbn.textContent = libro.isbn;
            fila.appendChild(celdaIsbn);

            const celdaEditorial = document.createElement("td");
            celdaEditorial.textContent = libro.editorial ? libro.editorial.nombre : "";
            fila.appendChild(celdaEditorial);

            const celdaGenero = document.createElement("td");
            celdaGenero.textContent = libro.genero ? libro.genero.nombre : "Sin clasificar";
            fila.appendChild(celdaGenero);

            const celdaAutores = document.createElement("td");
            celdaAutores.textContent = "Consultar detalle";
            fila.appendChild(celdaAutores);

            const celdaPrecio = document.createElement("td");
            celdaPrecio.textContent = formatearImporte(libro.precio);
            fila.appendChild(celdaPrecio);

            tbody.appendChild(fila);
        });
    } catch (err) {
        if (vacio) {
            vacio.textContent = `Error al cargar listado: ${err.message}`;
            vacio.hidden = false;
        }
    }
}

function actualizarListaAutoresAgregados() {
    const listaUl = document.getElementById("lista-autores-agregados");
    if (!listaUl) return;
    listaUl.replaceChildren();

    if (autoresAltaLibro.length === 0) {
        const li = document.createElement("li");
        li.id = "sin-autores-aviso";
        li.style.color = "var(--texto-secundario, #4A4A4A)";
        li.textContent = "No se han agregado autores aún (mínimo 1 requerido).";
        listaUl.appendChild(li);
        return;
    }

    autoresAltaLibro.forEach(function (item, index) {
        const li = document.createElement("li");
        li.style.margin = "0.25rem 0";
        li.textContent = `${item.nombre} (ID: ${item.autor_id}) — Rol: ${item.rol}, Orden: ${item.orden} `;

        const btnQuitar = document.createElement("button");
        btnQuitar.type = "button";
        btnQuitar.textContent = "Quitar";
        btnQuitar.style.fontSize = "0.8rem";
        btnQuitar.style.marginLeft = "0.5rem";
        btnQuitar.addEventListener("click", function () {
            autoresAltaLibro.splice(index, 1);
            actualizarListaAutoresAgregados();
        });

        li.appendChild(btnQuitar);
        listaUl.appendChild(li);
    });
}

async function buscarAutorParaAlta() {
    const inputId = document.getElementById("autor-id-buscar");
    const infoP = document.getElementById("autor-busqueda-info");
    if (!inputId || !infoP) return;

    const id = parseInt(inputId.value, 10);
    if (!id || id <= 0) {
        infoP.textContent = "Ingrese un ID de autor válido mayor a 0.";
        infoP.style.color = "var(--error, #B3261E)";
        return;
    }

    infoP.textContent = `Buscando autor #${id}...`;
    infoP.style.color = "var(--texto, #1A1A1A)";

    try {
        const autor = await window.api.getAutorById(id);
        ultimoAutorVerificado = autor;
        infoP.textContent = `Autor encontrado: «${autor.nombre}» (${autor.nacionalidad}). Listo para agregar.`;
        infoP.style.color = "var(--exito, #1E7A34)";
    } catch (err) {
        ultimoAutorVerificado = null;
        infoP.textContent = err.status === 404
            ? `No se encontró ningún autor con ID #${id}.`
            : `Error: ${err.message}`;
        infoP.style.color = "var(--error, #B3261E)";
    }
}

async function agregarAutoriaAlta() {
    const inputId = document.getElementById("autor-id-buscar");
    const rolSelect = document.getElementById("autor-rol-select");
    const ordenInput = document.getElementById("autor-orden-input");
    const infoP = document.getElementById("autor-busqueda-info");

    const id = parseInt(inputId.value, 10);
    const rol = rolSelect ? rolSelect.value : "autor";
    const orden = parseInt(ordenInput.value, 10) || (autoresAltaLibro.length + 1);

    if (!id || id <= 0) {
        if (infoP) {
            infoP.textContent = "Ingrese un ID de autor válido.";
            infoP.style.color = "var(--error, #B3261E)";
        }
        return;
    }

    // Verificar si ya está en la lista de autorías
    const duplicado = autoresAltaLibro.some(a => a.autor_id === id);
    if (duplicado) {
        if (infoP) {
            infoP.textContent = `El autor #${id} ya fue agregado a la lista de este libro.`;
            infoP.style.color = "var(--error, #B3261E)";
        }
        return;
    }

    // Si aún no está verificado en memoria, consultarlo
    let nombreAutor = ultimoAutorVerificado && ultimoAutorVerificado.id === id ? ultimoAutorVerificado.nombre : null;
    if (!nombreAutor) {
        try {
            const autor = await window.api.getAutorById(id);
            nombreAutor = autor.nombre;
        } catch (err) {
            if (infoP) {
                infoP.textContent = err.status === 404
                    ? `No se puede agregar: Autor ID #${id} no existe.`
                    : `Error al validar autor: ${err.message}`;
                infoP.style.color = "var(--error, #B3261E)";
            }
            return;
        }
    }

    autoresAltaLibro.push({
        autor_id: id,
        nombre: nombreAutor,
        rol: rol,
        orden: orden,
    });

    actualizarListaAutoresAgregados();
    if (infoP) {
        infoP.textContent = `Autoría agregada: ${nombreAutor} como ${rol}.`;
        infoP.style.color = "var(--exito, #1E7A34)";
    }

    // Preparar siguiente orden sugerido
    if (ordenInput) {
        ordenInput.value = autoresAltaLibro.length + 1;
    }
}

async function manejarEnvioLibro(e) {
    e.preventDefault();
    limpiarMensajes();

    const titulo = document.getElementById("libro-titulo").value.trim();
    const isbn = document.getElementById("libro-isbn").value.trim();
    const precio = parseFloat(document.getElementById("libro-precio").value);
    const stockInput = document.getElementById("libro-stock");
    const stock = stockInput ? parseInt(stockInput.value, 10) : 0;
    const editorialId = parseInt(document.getElementById("libro-editorial").value, 10);
    const generoVal = document.getElementById("libro-genero").value;
    const generoId = generoVal && generoVal !== "" ? parseInt(generoVal, 10) : null;

    // Validaciones locales
    const errores = [];
    if (!titulo) errores.push("El título no puede quedar vacío.");
    if (!isbn) errores.push("El ISBN no puede quedar vacío.");
    if (isNaN(precio) || precio <= 0) errores.push("El precio debe ser un número positivo mayor a 0.");
    if (isNaN(stock) || stock < 0) errores.push("El stock debe ser un entero mayor o igual a 0.");
    if (!editorialId || isNaN(editorialId)) errores.push("Debe seleccionar una editorial.");
    if (autoresAltaLibro.length === 0) errores.push("Debe agregar al menos un autor con su rol y orden.");

    if (errores.length > 0) {
        mostrarMensajeError(errores.join(" "));
        return;
    }

    const payload = {
        titulo: titulo,
        isbn: isbn,
        precio: precio,
        stock: stock,
        editorial_id: editorialId,
        genero_id: generoId,
        autores: autoresAltaLibro.map(function (a) {
            return {
                autor_id: a.autor_id,
                rol: a.rol,
                orden: a.orden,
            };
        }),
    };

    try {
        const libroCreado = await window.api.createLibro(payload);
        mostrarMensajeOk(`Libro registrado exitosamente (HTTP 201): «${libroCreado.titulo}» (ID: ${libroCreado.id}, ISBN: ${libroCreado.isbn}).`);
        
        // Reset formulario y lista de autores
        document.getElementById("form-libro").reset();
        autoresAltaLibro = [];
        ultimoAutorVerificado = null;
        actualizarListaAutoresAgregados();
        if (stockInput) stockInput.value = "10";

        // Actualizar catálogo de libros
        renderizarCatalogoEnLibros();
    } catch (err) {
        // Muestra error 409 (ej: ISBN repetido) o 422
        mostrarMensajeError(err.message);
    }
}

function inicializarLibros() {
    const formLibro = document.getElementById("form-libro");
    if (!formLibro) return;

    formLibro.noValidate = true;
    cargarSelectoresLibro();
    renderizarCatalogoEnLibros();
    limpiarMensajes();

    const btnBuscarAutor = document.getElementById("btn-buscar-autor");
    if (btnBuscarAutor) {
        btnBuscarAutor.addEventListener("click", buscarAutorParaAlta);
    }

    const btnAgregarAutoria = document.getElementById("btn-agregar-autoria");
    if (btnAgregarAutoria) {
        btnAgregarAutoria.addEventListener("click", agregarAutoriaAlta);
    }

    formLibro.addEventListener("submit", manejarEnvioLibro);
}

// =============================================================================
// 4. MÓDULO CLIENTES (clientes.html)
// =============================================================================

async function manejarEnvioCliente(e) {
    e.preventDefault();
    limpiarMensajes();

    const nombre = document.getElementById("cliente-nombre").value.trim();
    const email = document.getElementById("cliente-email").value.trim();

    if (!nombre) {
        mostrarMensajeError("El nombre completo no puede quedar vacío.");
        return;
    }
    if (!email || !email.includes("@")) {
        mostrarMensajeError("Ingrese un correo electrónico válido.");
        return;
    }

    try {
        const cliente = await window.api.createCliente({ nombre, email });
        mostrarMensajeOk(`Cliente registrado exitosamente (HTTP 201): ID #${cliente.id} — «${cliente.nombre}» (${cliente.email}).`);
        document.getElementById("form-cliente").reset();

        // Agregar fila al listado de clientes registrados en la página
        agregarFilaClienteTabla(cliente);
    } catch (err) {
        // HTTP 409 (correo duplicado) o 422
        mostrarMensajeError(err.message);
    }
}

function agregarFilaClienteTabla(cliente) {
    const tabla = document.getElementById("clientes-listado");
    if (!tabla) return;
    const tbody = tabla.querySelector("tbody");
    const vacio = document.getElementById("clientes-vacio");
    if (vacio) vacio.hidden = true;

    const fila = document.createElement("tr");
    const celdaNombre = document.createElement("td");
    celdaNombre.textContent = `${cliente.nombre} (ID: ${cliente.id})`;
    fila.appendChild(celdaNombre);

    const celdaEmail = document.createElement("td");
    celdaEmail.textContent = cliente.email;
    fila.appendChild(celdaEmail);

    if (tbody) tbody.appendChild(fila);
}

async function manejarConsultaClienteId(e) {
    e.preventDefault();
    const inputId = document.getElementById("buscar-cliente-id");
    const resultadoDiv = document.getElementById("cliente-consultado-resultado");
    if (!inputId || !resultadoDiv) return;

    const id = parseInt(inputId.value, 10);
    if (!id || id <= 0) {
        resultadoDiv.innerHTML = `<p style="color: var(--error, #B3261E);">Ingrese un ID válido mayor a 0.</p>`;
        return;
    }

    resultadoDiv.innerHTML = `<p>Consultando cliente #${id}...</p>`;

    try {
        const cliente = await window.api.getClienteById(id);
        const perfilInfo = cliente.perfil
            ? `Tel: ${cliente.perfil.telefono}, Dirección: ${cliente.perfil.direccion}`
            : "Sin perfil detallado";

        resultadoDiv.innerHTML = `
            <div style="padding: 0.75rem; border: 1px solid var(--borde); background: var(--superficie); border-radius: 4px;">
                <p style="margin: 0 0 0.25rem 0; font-weight: bold; color: var(--primario);">Cliente encontrado (HTTP 200):</p>
                <p style="margin: 0;"><strong>ID:</strong> ${cliente.id} | <strong>Nombre:</strong> ${cliente.nombre}</p>
                <p style="margin: 0;"><strong>Email:</strong> ${cliente.email}</p>
                <p style="margin: 0; font-size: 0.9rem; color: var(--texto-secundario);"><strong>Perfil:</strong> ${perfilInfo}</p>
            </div>
        `;
        agregarFilaClienteTabla(cliente);
    } catch (err) {
        resultadoDiv.innerHTML = `<p style="color: var(--error, #B3261E);">${err.status === 404 ? `No existe cliente con ID #${id}.` : err.message}</p>`;
    }
}

function inicializarClientes() {
    const formCliente = document.getElementById("form-cliente");
    if (!formCliente) return;

    formCliente.noValidate = true;
    limpiarMensajes();
    formCliente.addEventListener("submit", manejarEnvioCliente);

    const formBuscarCliente = document.getElementById("form-buscar-cliente");
    if (formBuscarCliente) {
        formBuscarCliente.addEventListener("submit", manejarConsultaClienteId);
    }
}

// =============================================================================
// 5. MÓDULO VENTAS (ventas.html)
// =============================================================================

let clienteVentaConfirmado = null; // Objeto { id, nombre, email }
let renglonesVentaActual = [];    // Array de borrador en memoria: [{ libroId, titulo, cantidad, precioUnitario, subtotal }]
let catalogoLibrosVenta = [];     // Catálogo cacheado para el selector de libros

async function cargarDatosFormularioVentas() {
    const selLibro = document.getElementById("venta-libro");
    if (!selLibro) return;

    try {
        catalogoLibrosVenta = await window.api.getLibros({ limit: 100 });
        selLibro.replaceChildren();
        const opcDefecto = document.createElement("option");
        opcDefecto.value = "";
        opcDefecto.textContent = "-- Seleccione un libro --";
        selLibro.appendChild(opcDefecto);

        catalogoLibrosVenta.forEach(function (libro) {
            const opc = document.createElement("option");
            opc.value = libro.id;
            opc.textContent = `${libro.titulo} — $${formatearImporte(libro.precio)} (Stock: ${libro.stock})`;
            selLibro.appendChild(opc);
        });
    } catch (err) {
        console.error("Error al cargar libros para venta", err);
    }
}

async function buscarClienteParaVenta() {
    const inputId = document.getElementById("venta-cliente-id");
    const infoP = document.getElementById("venta-cliente-info");
    const selCliente = document.getElementById("venta-cliente");
    if (!inputId || !infoP) return;

    const id = parseInt(inputId.value, 10);
    if (!id || id <= 0) {
        infoP.textContent = "Ingrese un ID de cliente válido.";
        infoP.style.color = "var(--error, #B3261E)";
        clienteVentaConfirmado = null;
        return;
    }

    infoP.textContent = `Consultando cliente #${id}...`;
    infoP.style.color = "var(--texto, #1A1A1A)";

    try {
        const cliente = await window.api.getClienteById(id);
        clienteVentaConfirmado = cliente;
        infoP.textContent = `Cliente confirmado: «${cliente.nombre}» (${cliente.email}) [ID #${cliente.id}]`;
        infoP.style.color = "var(--exito, #1E7A34)";

        if (selCliente) {
            selCliente.replaceChildren();
            const opc = document.createElement("option");
            opc.value = cliente.id;
            opc.textContent = `${cliente.nombre} (ID: ${cliente.id})`;
            opc.selected = true;
            selCliente.appendChild(opc);
        }
    } catch (err) {
        clienteVentaConfirmado = null;
        infoP.textContent = err.status === 404
            ? `No existe ningún cliente registrado con ID #${id}.`
            : `Error: ${err.message}`;
        infoP.style.color = "var(--error, #B3261E)";
    }
}

function recalcularResumenVenta() {
    const resumen = document.getElementById("venta-resumen");
    if (!resumen) return;

    let total = 0;
    for (let i = 0; i < renglonesVentaActual.length; i++) {
        total += redondear2(renglonesVentaActual[i].subtotal);
    }
    total = redondear2(total);
    resumen.textContent = `Total borrador: $${formatearImporte(total)}.`;
}

function renderizarRenglonesVenta() {
    const tabla = document.getElementById("venta-renglones");
    if (!tabla) return;
    const cuerpo = tabla.querySelector("tbody");
    const vacio = document.getElementById("venta-renglones-vacio");
    if (!cuerpo) return;

    cuerpo.replaceChildren();

    if (renglonesVentaActual.length === 0) {
        if (vacio) vacio.hidden = false;
        recalcularResumenVenta();
        return;
    }

    if (vacio) vacio.hidden = true;

    renglonesVentaActual.forEach(function (renglon, idx) {
        const fila = document.createElement("tr");

        const celdaTitulo = document.createElement("td");
        celdaTitulo.textContent = renglon.titulo;
        fila.appendChild(celdaTitulo);

        const celdaCantidad = document.createElement("td");
        const inputCant = document.createElement("input");
        inputCant.type = "number";
        inputCant.min = "1";
        inputCant.value = renglon.cantidad;
        inputCant.style.width = "70px";
        inputCant.addEventListener("change", function (e) {
            const nuevaCant = parseInt(e.target.value, 10);
            if (!isNaN(nuevaCant) && nuevaCant >= 1) {
                renglon.cantidad = nuevaCant;
                renglon.subtotal = redondear2(nuevaCant * renglon.precioUnitario);
                renderizarRenglonesVenta();
            } else {
                mostrarMensajeError("La cantidad debe ser un entero mayor o igual a 1.");
                e.target.value = renglon.cantidad;
            }
        });
        celdaCantidad.appendChild(inputCant);
        fila.appendChild(celdaCantidad);

        const celdaPrecio = document.createElement("td");
        celdaPrecio.textContent = formatearImporte(renglon.precioUnitario);
        fila.appendChild(celdaPrecio);

        const celdaSubtotal = document.createElement("td");
        celdaSubtotal.textContent = formatearImporte(renglon.subtotal);
        fila.appendChild(celdaSubtotal);

        const celdaAccion = document.createElement("td");
        const btnQuitar = document.createElement("button");
        btnQuitar.type = "button";
        btnQuitar.textContent = "Quitar";
        btnQuitar.addEventListener("click", function () {
            renglonesVentaActual.splice(idx, 1);
            renderizarRenglonesVenta();
        });
        celdaAccion.appendChild(btnQuitar);
        fila.appendChild(celdaAccion);

        cuerpo.appendChild(fila);
    });

    recalcularResumenVenta();
}

function agregarRenglonVenta(e) {
    if (e) e.preventDefault();
    limpiarMensajes();

    const selLibro = document.getElementById("venta-libro");
    const inputCantidad = document.getElementById("venta-cantidad");
    if (!selLibro || !inputCantidad) return;

    const libroId = parseInt(selLibro.value, 10);
    const cantidad = parseInt(inputCantidad.value, 10);

    if (!libroId || isNaN(libroId)) {
        mostrarMensajeError("Debe seleccionar un libro del catálogo.");
        return;
    }
    if (isNaN(cantidad) || cantidad <= 0) {
        mostrarMensajeError("La cantidad debe ser un número entero mayor que cero.");
        return;
    }

    const libro = catalogoLibrosVenta.find(l => l.id === libroId);
    if (!libro) {
        mostrarMensajeError("El libro seleccionado no se encuentra en el catálogo.");
        return;
    }

    // Regla de negocio: un solo renglón por libro (si ya existe, acumula cantidad)
    const renglonExistente = renglonesVentaActual.find(r => r.libroId === libroId);
    if (renglonExistente) {
        renglonExistente.cantidad += cantidad;
        renglonExistente.subtotal = redondear2(renglonExistente.cantidad * renglonExistente.precioUnitario);
        mostrarMensajeOk(`Libro ya presente en borrador: cantidad incrementada a ${renglonExistente.cantidad}.`);
    } else {
        const precioUnitario = Number(libro.precio);
        renglonesVentaActual.push({
            libroId: libro.id,
            titulo: libro.titulo,
            cantidad: cantidad,
            precioUnitario: precioUnitario,
            subtotal: redondear2(cantidad * precioUnitario),
        });
    }

    inputCantidad.value = "1";
    renderizarRenglonesVenta();
}

function resetearFormularioVentaCompleto() {
    const form = document.getElementById("form-venta");
    if (form) form.reset();
    clienteVentaConfirmado = null;
    const infoCliente = document.getElementById("venta-cliente-info");
    if (infoCliente) infoCliente.textContent = "";
    const selCliente = document.getElementById("venta-cliente");
    if (selCliente) {
        selCliente.replaceChildren();
        const opc = document.createElement("option");
        opc.value = "";
        opc.textContent = "-- Ingrese ID y presione Buscar cliente --";
        selCliente.appendChild(opc);
    }
    renglonesVentaActual = [];
    renderizarRenglonesVenta();
}

async function confirmarVentaFinal() {
    limpiarMensajes();

    if (!clienteVentaConfirmado) {
        mostrarMensajeError("Debe consultar y confirmar un cliente por ID antes de confirmar la venta.");
        return;
    }

    if (renglonesVentaActual.length === 0) {
        mostrarMensajeError("Debe agregar al menos un renglón a la venta.");
        return;
    }

    // Comprobar cantidades positivas
    for (let i = 0; i < renglonesVentaActual.length; i++) {
        if (!renglonesVentaActual[i].cantidad || renglonesVentaActual[i].cantidad <= 0) {
            mostrarMensajeError("Todas las cantidades deben ser enteras positivas.");
            return;
        }
    }

    const btnConfirmar = document.getElementById("venta-confirmar");
    if (btnConfirmar) {
        btnConfirmar.disabled = true;
        btnConfirmar.textContent = "Procesando venta...";
    }

    const payload = {
        cliente_id: clienteVentaConfirmado.id,
        renglones: renglonesVentaActual.map(function (r) {
            return {
                libro_id: r.libroId,
                cantidad: r.cantidad,
            };
        }),
    };

    try {
        const ventaRegistrada = await window.api.createVenta(payload);

        // Construir detalle del comprobante devuelto por la API
        const resumenRenglones = ventaRegistrada.renglones.map(function (r) {
            return `• ${r.titulo} (cant: ${r.cantidad}, precio unit.: $${formatearImporte(r.precio_unitario)}, subtotal: $${formatearImporte(r.subtotal)})`;
        }).join("\n");

        mostrarMensajeOk(
            `Venta #${ventaRegistrada.id} confirmada con éxito (HTTP 201)!\n` +
            `Cliente: ${ventaRegistrada.cliente.nombre} (${ventaRegistrada.cliente.email})\n` +
            `Fecha: ${formatearFecha(ventaRegistrada.fecha)}\n` +
            `Total registrado en API: $${formatearImporte(ventaRegistrada.total)}\n` +
            `Detalle de renglones:\n${resumenRenglones}`
        );

        // Limpiar el borrador únicamente tras confirmación exitosa
        resetearFormularioVentaCompleto();

        // Refrescar catálogo en segundo plano para reflejar descuento de stock
        cargarDatosFormularioVentas();

    } catch (err) {
        // En caso de error (409 stock insuficiente / cliente inexistente, o 422 renglón repetido):
        // Se muestra el error y SE CONSERVA EL BORRADOR EN MEMORIA
        mostrarMensajeError(`No se pudo procesar la venta: ${err.message}`);
    } finally {
        if (btnConfirmar) {
            btnConfirmar.disabled = false;
            btnConfirmar.textContent = "Confirmar venta";
        }
    }
}

function inicializarVentas() {
    const formVenta = document.getElementById("form-venta");
    if (!formVenta) return;

    formVenta.noValidate = true;
    limpiarMensajes();
    cargarDatosFormularioVentas();

    const btnBuscarCliente = document.getElementById("btn-buscar-cliente-venta");
    if (btnBuscarCliente) {
        btnBuscarCliente.addEventListener("click", buscarClienteParaVenta);
    }

    formVenta.addEventListener("submit", agregarRenglonVenta);

    const btnConfirmar = document.getElementById("venta-confirmar");
    if (btnConfirmar) {
        btnConfirmar.addEventListener("click", confirmarVentaFinal);
    }

    renderizarRenglonesVenta();
}

// =============================================================================
// 6. MÓDULO HISTORIAL (historial.html)
// =============================================================================

let historialOffset = 0;
const historialLimit = 20;

async function cargarHistorialVentas() {
    const tabla = document.getElementById("historial-listado");
    if (!tabla) return;
    const tbody = tabla.querySelector("tbody");
    const vacio = document.getElementById("historial-vacio");
    const btnPrev = document.getElementById("btn-historial-prev");
    const btnNext = document.getElementById("btn-historial-next");
    const pagInfo = document.getElementById("historial-pagina-info");

    if (tbody) tbody.replaceChildren();
    if (vacio) vacio.hidden = true;

    try {
        const ventas = await window.api.getVentas({
            limit: historialLimit,
            offset: historialOffset,
        });

        if (!ventas || ventas.length === 0) {
            if (vacio) {
                vacio.textContent = "No hay ventas registradas.";
                vacio.hidden = false;
            }
            if (btnNext) btnNext.disabled = true;
            if (btnPrev) btnPrev.disabled = historialOffset === 0;
            if (pagInfo) {
                pagInfo.textContent = `Página ${Math.floor(historialOffset / historialLimit) + 1}`;
            }
            return;
        }

        ventas.forEach(function (venta) {
            const fila = document.createElement("tr");

            const celdaId = document.createElement("td");
            celdaId.textContent = `#${venta.id}`;
            fila.appendChild(celdaId);

            const celdaFecha = document.createElement("td");
            celdaFecha.textContent = formatearFecha(venta.fecha);
            fila.appendChild(celdaFecha);

            const celdaCliente = document.createElement("td");
            celdaCliente.textContent = venta.cliente ? venta.cliente.nombre : "Cliente N/D";
            fila.appendChild(celdaCliente);

            const celdaTotal = document.createElement("td");
            celdaTotal.textContent = `$${formatearImporte(venta.total)}`;
            fila.appendChild(celdaTotal);

            const celdaDetalle = document.createElement("td");
            const linkDetalle = document.createElement("a");
            linkDetalle.href = "#historial-detalle";
            linkDetalle.textContent = `Ver detalle (#${venta.id})`;
            linkDetalle.addEventListener("click", function (e) {
                e.preventDefault();
                verDetalleVentaHistorial(venta.id);
            });
            celdaDetalle.appendChild(linkDetalle);
            fila.appendChild(celdaDetalle);

            tbody.appendChild(fila);
        });

        if (btnPrev) btnPrev.disabled = historialOffset === 0;
        if (btnNext) btnNext.disabled = ventas.length < historialLimit;
        if (pagInfo) {
            pagInfo.textContent = `Página ${Math.floor(historialOffset / historialLimit) + 1}`;
        }

    } catch (err) {
        if (vacio) {
            vacio.textContent = `Error al cargar historial: ${err.message}`;
            vacio.hidden = false;
        }
    }
}

async function verDetalleVentaHistorial(id) {
    const contenedor = document.getElementById("historial-detalle");
    if (!contenedor) return;

    contenedor.replaceChildren();
    const aviso = document.createElement("p");
    aviso.textContent = `Consultando detalle de la venta #${id}...`;
    contenedor.appendChild(aviso);

    try {
        const venta = await window.api.getVentaById(id);
        contenedor.replaceChildren();

        const cabecera = document.createElement("div");
        cabecera.style.padding = "0.75rem";
        cabecera.style.background = "var(--superficie, #FFFFFF)";
        cabecera.style.border = "1px solid var(--borde, #D8CFC0)";
        cabecera.style.borderRadius = "4px";
        cabecera.style.marginBottom = "1rem";

        cabecera.innerHTML = `
            <h4 style="margin: 0 0 0.5rem 0; color: var(--primario);">Comprobante de Venta #${venta.id}</h4>
            <p style="margin: 0 0 0.25rem 0;"><strong>Fecha:</strong> ${formatearFecha(venta.fecha)}</p>
            <p style="margin: 0 0 0.25rem 0;"><strong>Cliente:</strong> ${venta.cliente.nombre} (${venta.cliente.email})</p>
            <p style="margin: 0; font-size: 1.1rem; font-weight: bold; color: var(--acento, #B4552D);">Total facturado: $${formatearImporte(venta.total)}</p>
        `;
        contenedor.appendChild(cabecera);

        const subRenglones = document.createElement("h5");
        subRenglones.textContent = "Renglones e importes históricos (anti-N+1):";
        subRenglones.style.margin = "0 0 0.5rem 0";
        contenedor.appendChild(subRenglones);

        if (!venta.renglones || venta.renglones.length === 0) {
            const pSin = document.createElement("p");
            pSin.textContent = "La venta no registra renglones.";
            contenedor.appendChild(pSin);
        } else {
            const tablaRenglones = document.createElement("table");
            tablaRenglones.style.width = "100%";
            tablaRenglones.innerHTML = `
                <thead>
                    <tr>
                        <th style="text-align: left;">Libro</th>
                        <th style="text-align: right;">Cantidad</th>
                        <th style="text-align: right;">Precio Unitario Histórico</th>
                        <th style="text-align: right;">Subtotal</th>
                    </tr>
                </thead>
                <tbody>
                    ${venta.renglones.map(r => `
                        <tr>
                            <td>${r.titulo}</td>
                            <td style="text-align: right;">${r.cantidad}</td>
                            <td style="text-align: right;">$${formatearImporte(r.precio_unitario)}</td>
                            <td style="text-align: right;">$${formatearImporte(r.subtotal)}</td>
                        </tr>
                    `).join("")}
                </tbody>
            `;
            contenedor.appendChild(tablaRenglones);
        }

    } catch (err) {
        contenedor.replaceChildren();
        const pErr = document.createElement("p");
        pErr.style.color = "var(--error, #B3261E)";
        pErr.textContent = `Error al consultar detalle de la venta: ${err.message}`;
        contenedor.appendChild(pErr);
    }
}

function inicializarHistorial() {
    const tabla = document.getElementById("historial-listado");
    if (!tabla) return;

    limpiarMensajes();

    const btnPrev = document.getElementById("btn-historial-prev");
    const btnNext = document.getElementById("btn-historial-next");

    if (btnPrev) {
        btnPrev.addEventListener("click", function () {
            if (historialOffset >= historialLimit) {
                historialOffset -= historialLimit;
                cargarHistorialVentas();
            }
        });
    }

    if (btnNext) {
        btnNext.addEventListener("click", function () {
            historialOffset += historialLimit;
            cargarHistorialVentas();
        });
    }

    cargarHistorialVentas();
}

// =============================================================================
// 7. ARRANQUE DE LA APLICACIÓN
// =============================================================================

document.addEventListener("DOMContentLoaded", function () {
    if (document.getElementById("catalogo-listado")) {
        inicializarCatalogo();
    }
    if (document.getElementById("form-libro")) {
        inicializarLibros();
    }
    if (document.getElementById("form-cliente")) {
        inicializarClientes();
    }
    if (document.getElementById("form-venta")) {
        inicializarVentas();
    }
    if (document.getElementById("historial-listado")) {
        inicializarHistorial();
    }
});
