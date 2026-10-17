# Roadmap y Memoria de Proyecto - Hugo Fernández Arte Creativo

## Estado Actual del Proyecto
- **Fecha de Actualización:** Octubre 2026
- **Directiva Vigente:** Fase 10 - Creación del Panel de Administración (CMS Propio).

---

### Fase 10: Creación del Panel de Administración (CMS Propio)
**Estado:** COMPLETADA ✅
**Hito Registrado:** Creación del Dashboard de Gestión

#### Enfoque Arquitectural:
- Implementación de un panel administrativo privado/oculto en la ruta `/admin` que independiza al cliente de la edición manual de código, transformando la plataforma en un CMS autónomo.
- Pipeline completo de subida física de archivos binarios (`multipart/form-data`) con sanitización de nombres de archivo mediante `secure_filename` y almacenamiento en disco en carpetas de assets locales y estáticos.
- Integración bidireccional con SQLite: inserción de metadatos de trajes con rutas relativas para el catálogo y moderación reactiva (eliminación) de comentarios públicos.

#### Entregables Implementados:
1. **Configuración de Carga y Endpoint en Backend (`app.py`):**
   - Configuración de `app.config['UPLOAD_FOLDER'] = 'assets/img/'`.
   - Endpoint `POST /api/trajes` con soporte para `multipart/form-data`.
   - Sanitización con `werkzeug.utils.secure_filename`, prevención de colisiones de nombres y guardado físico en `assets/img/` y réplica en `static/assets/img/`.
   - Registro en la tabla `trajes` de SQLite con `comparsero`, `comparsa`, `genero`, `materiales` y `foto_url`.
2. **Dashboard de Administración (`templates/admin.html`, `pages/admin.html`, `admin.html`):**
   - **Sección A (Cargar Nuevo Traje):** Formulario `#form-nuevo-traje` con inputs para Comparsero, Comparsa (con autocompletado datalist), Género, Materiales (textarea) e Input de archivo `<input type="file" id="foto" name="foto" accept="image/*" required>`.
   - Previsualización instantánea de la imagen seleccionada en el cliente con dimensiones y tamaño.
   - Envío asíncrono con JavaScript mediante `new FormData()` a `POST /api/trajes`, feedback con `alert()`, toast visual y reseteo del formulario.
   - **Sección B (Moderación de Comentarios):** Tabla dinámica alimentada por `GET /api/comentarios/todos` que visualiza ID, Traje asociado, Usuario, Texto del comentario, Fecha y botón rojo "🗑️ Eliminar".
   - Eliminación en tiempo real con `DELETE /api/comentarios/<id>` y remoción animada del elemento en el DOM.
3. **Ruta Servida en Flask (`app.py`):**
   - `@app.route('/admin')` configurado para renderizar `admin.html`.

---

### Fase 9: Mobile First y Scroll Snap
**Estado:** COMPLETADA ✅
**Hito Registrado:** Mobile First y Scroll Snap

#### Enfoque Arquitectural:
- Resolución de incidencias de desbordamiento horizontal (`overflow-x`) en resoluciones móviles (`<= 768px`), garantizando un viewport 100% hermético.
- **Separación de Comportamiento Móvil:**
  - **Comparsas (`pages/arandu-beleza.html`):** Cuadrícula tradicional compacta de 2 columnas (`repeat(2, 1fr)` con `gap: 10px`) para visión simultánea y scroll vertical estándar continuo.
  - **Trajes (`pages/trajes.html`):** Feed vertical inmersivo tipo Reels/Tinder (`.feed-trajes-mobile`) con `height: 85vh`, `scroll-snap-type: y mandatory` y tarjetas `.tarjeta-feed` a pantalla completa.
- Estricta preservación del layout desktop (`> 768px`): ambos catálogos conservan sus layouts amplios de cuadrícula y tarjetas expandidas.

#### Entregables Implementados:
1. **Reversión de la Grilla de Comparsas en Móvil (`.grilla-miniaturas`, `.comparseros-grid`):**
   - Configurada en cuadrícula 2x (`grid-template-columns: repeat(2, 1fr); gap: 10px;`) sin scroll snap.
   - Tarjetas `.tarjeta-miniatura` adaptadas con altura proporcional, thumb de 170px, cuerpo compacto y botón de consulta optimizado para dos columnas.
2. **Feed Inmersivo Vertical para Trajes (`.feed-trajes-mobile` y `.tarjeta-feed`):**
   - Implementado en `pages/trajes.html` para las secciones de vestuarios femeninos y masculinos.
   - Contenedor con `height: 85vh;`, `overflow-y: scroll;`, `scroll-snap-type: y mandatory;` y barras de desplazamiento ocultas.
   - Tarjetas `.tarjeta-feed` con dimensionamiento a pantalla completa (`height: 100%; min-height: 85vh; scroll-snap-align: start;`).
   - Foto en fondo completo con `object-fit: cover;`, gradient overlay oscuro inferior y contenido superpuesto con CTA táctil.
3. **Auditoría Global de Viewport & Anti-Overflow (`index.html`, `pages/*.html`, `templates/*.html`, `css/estilos.css`):**
   - `max-width: 100vw; overflow-x: hidden;` a nivel global en `html, body`.
   - Normalización de paddings, márgenes y tipografías fluidas (`clamp()`) en títulos (`h1`, `h2`, `h3`, `.hero-title`, `.hero-description`).
   - Neutralización de elementos que provocaban scroll lateral en móviles.
4. **Protección de la Vista Desktop:**
   - La regla `@media (max-width: 768px)` encapsula exclusivamente los comportamientos móviles, preservando el CSS Grid de 3 columnas en Comparsas y la galería expandida en Trajes.

---

### Fase 8: SEO y Social Sharing (Open Graph)
**Estado:** COMPLETADA ✅
**Hito Registrado:** SEO y Social Sharing (Open Graph)

#### Enfoque Arquitectural:
- Transición a Server-Side Rendering (SSR) con Jinja2 en Flask para que los web scrapers de WhatsApp, Telegram, Facebook y Twitter puedan generar tarjetas de vista previa enriquecidas (Rich Cards) sin depender de ejecución JavaScript en el cliente.
- Organización de la estructura canónica en Flask: `templates/` para vistas dinámicas y `static/` para hojas de estilo, scripts y assets multimedia.
- Inyección contextual de metaetiquetas Open Graph y Twitter Cards basada en los datos consultados en SQLite.
- Experiencia de usuario enriquecida mediante la Web Share API nativa (`navigator.share`) en dispositivos móviles y fallback automático al portapapeles con feedback visual en navegadores de escritorio.

#### Entregables Implementados:
1. **Server-Side Rendering en Flask (`app.py`):**
   - Configuración de `template_folder="templates"` y `static_folder="static"`.
   - Endpoint SSR `@app.route('/traje/<int:id>')` que realiza consulta directa a SQLite y renderiza `templates/traje-detalle.html` con las variables `traje` y `materiales_lista`.
   - Compatibilidad retroactiva en `@app.route('/pages/traje-detalle.html')` reconociendo parámetros `?id=` y derivando a la renderización SSR.
2. **Plantilla SSR y Metaetiquetas Open Graph (`templates/traje-detalle.html`):**
   - `<meta property="og:title" content="{{ traje.comparsero }} - {{ traje.comparsa }} | Hugo Fernández">`
   - `<meta property="og:description" content="Descubre los detalles y materiales de esta obra del carnaval.">`
   - Inyección inteligente de imagen (`og:image`): soporte para URLs externas (`http://`, `https://`) y URLs absolutas para recursos locales vía `url_for('static', filename=..., _external=True)`.
   - `<meta property="og:url" content="{{ request.url }}">`
   - `<meta name="twitter:card" content="summary_large_image">`
   - Desglose de materiales y créditos renderizados desde el servidor con bucles Jinja2.
3. **Botón "Compartir Traje" y Web Share API (`js/detalle.js`, `static/js/detalle.js`, `css/estilos.css`):**
   - Botón estético `.btn-compartir` en el encabezado de la ficha del traje.
   - Función `compartirTraje()` invocando `navigator.share({ title, text, url })`.
   - Fallback robusto al portapapeles (`navigator.clipboard.writeText`) con toast feedback (`#share-feedback`).
4. **Redirección desde la Grilla (`js/main.js`, `static/js/main.js`):**
   - Las tarjetas dinámicas enlazan a la nueva ruta amigable SSR `/traje/${traje.id}` tanto en el botón "Ver Ficha del Traje" como en el evento clic de la tarjeta.

---

### Fase 7: Sistema de Comentarios y Panel de Moderación
**Estado:** COMPLETADA ✅
**Hito Registrado:** Sistema de Comentarios y Panel de Moderación

#### Enfoque Arquitectural:
- Interacción bidireccional de la comunidad comparsera sobre las fichas técnicas individuales.
- Persistencia relacional de comentarios asociados a cada traje en `carnaval.db` con clave foránea (`FOREIGN KEY (traje_id) REFERENCES trajes(id)`).
- Endpoints RESTful para consulta por traje, publicación segura de comentarios, auditoría global y eliminación supervisada.
- Panel administrativo de moderación (`/admin`) con tabla dinámica y acciones inmediatas en tiempo real.

#### Entregables Implementados:
1. **Base de Datos (`database.py` y `carnaval.db`):**
   - Tabla `comentarios`: `id`, `traje_id`, `usuario`, `texto`, `fecha`.
   - Semilla inicial con comentarios de prueba.
2. **Backend Flask (`app.py`):**
   - `GET /api/comentarios/<int:traje_id>`: Comentarios de un traje específico.
   - `POST /api/comentarios`: Inserción de nuevos comentarios vía JSON.
   - `GET /api/comentarios/todos`: Lista de todos los comentarios con metadata para administración.
   - `DELETE /api/comentarios/<int:id>`: Eliminación de comentario por ID.
   - `GET /admin`: Servicio del panel de moderación `pages/admin.html`.
3. **Frontend de Ficha Técnica (`pages/traje-detalle.html`, `js/main.js`, `js/detalle.js`):**
   - Sección interactiva de comentarios al pie de la ficha.
   - Formulario público para Nombre/Usuario y Comentario.
   - Envío asíncrono con `POST` y recarga en caliente del listado sin refrescar la página.
4. **Panel de Moderación Admin (`pages/admin.html`):**
   - Interfaz con tabla de comentarios, datos del traje, usuario, contenido y fecha.
   - Botón rojo de eliminación con confirmación y remoción animada del DOM.

---

### Fase 6: Migración a Base de Datos Dinámica con SQLite y Flask
**Estado:** COMPLETADA ✅
**Hito Reciente:** Conexión de traje-detalle.html con la API REST

#### Enfoque Arquitectural:
- Transición hacia una arquitectura desacoplada y escalable basada en API REST y persistencia local liviana.
- La base de datos SQLite permite que el catálogo se alimente dinámicamente sin tocar código HTML.
- Consumo asíncrono con `fetch('/api/trajes')`, renderizado dinámico con Template Literals, persistencia en dataset/sessionStorage para la ficha técnica individual y filtrado en memoria en tiempo real.

#### Entregables Implementados:
1. **Configuración de la Base de Datos (`database.py` y `carnaval.db`):**
   - Base de datos relacional con `sqlite3` y tabla `trajes` (`id`, `comparsero`, `comparsa`, `genero`, `materiales`, `foto_url`).
   - Semilla inicial con 4 trajes representativos.
2. **Servidor Backend con Flask (`app.py`):**
   - Servidor web ligero en Python sirviendo estáticos y endpoints REST:
     - `GET /api/trajes` (lista completa).
     - `GET /api/trajes/<id>` (traje individual).
     - `GET /api/trajes/filtrar` (filtros backend).
3. **Hidratación Dinámica del Frontend (`js/main.js`):**
   - Función asíncrona `cargarTrajes()` que consulta `/api/trajes` y vacía `.grilla-miniaturas` (`.comparseros-grid`).
   - Renderizado con Template Literals de cada `.tarjeta-miniatura` inyectando imagen (`foto_url`), comparsero (título), comparsa y género (subtítulos) y `data-id`.
   - Inyección del objeto completo en `dataset.traje` y `sessionStorage` para transferir el desglose exacto de materiales a `traje-detalle.html`.
   - Buscador y botones de filtro en tiempo real que operan sobre el arreglo en memoria y re-renderizan la grilla sin ocultamientos CSS.
   - Limpieza del HTML en `pages/arandu-beleza.html`, dejando el contenedor vacío para su hidratación por JavaScript.
4. **Guía de Integración Técnica (`instrucciones.md`):**
   - Documentación técnica y código de referencia.

---

### Historial de Fases Previas:
- **Fase 4:** Vidriera interactiva con componente slider "Boceto vs Realidad" en `pages/traje-detalle.html`.
- **Fase 3:** Actualización de narrativa principal del Hero con la biografía real de Hugo y 6 comparsas confirmadas en la sección de trayectoria de `index.html`.
- **Fase 2:** Separación de lógicas (Trajes inspiración con fotos grandes vs. Comparsas catálogo con thumbnails y buscador en tiempo real en `js/main.js`).
- **Fase 1:** Reestructuración de galerías en miniaturas, pestañas de filtrado, ficha individual asimétrica (`traje-detalle.html`) y sección de Obras Maestras (`coordinacion.html`).
- **Fase 0:** Setup de arquitectura modular (`/css`, `/js`, `/assets`, `/pages`), sticky header dinámico y directivas de diseño formalizadas en `agentes.md`.
