# Roadmap y Memoria de Proyecto - Hugo Fernández Arte Creativo

## Estado Actual del Proyecto
- **Fecha de Actualización:** Octubre 2026
- **Directiva Vigente:** Fase 14 - Módulo Social (Comunidad & Moderación), Seed de Datos del Carnaval Correntino y Mejoras Autónomas de UX.

---

### Fase 14: Módulo Social, Seed de Datos y Mejoras Autónomas de Carnaval
**Estado:** COMPLETADA ✅
**Hito Registrado:** Comunidad de Comparseros (`/comunidad/subir`), Bandeja de Moderación (`estado='pendiente'/'publicado'`), Script `seed.py` con 6 Comparsas Correntinas, Vista Genérica `/comparsa/<nombre_comparsa>` y 3 Mejoras Autónomas de UX.

#### Enfoque Arquitectural:
1. **Módulo 1: Comunidad de Comparseros y Moderación (`database.py`, `app.py`, `templates/comunidad_subir.html`, `templates/admin.html`):**
   - **Esquema SQLite (`database.py`):** Adición de la columna `estado VARCHAR DEFAULT 'pendiente'` en la tabla `trajes` con migración automática en `init_db()` (preservando los registros previos en `'publicado'`).
   - **Subida Pública de Comunidad (`GET/POST /comunidad/subir`):** Nueva plantilla `templates/comunidad_subir.html` donde cualquier comparsero puede postular su traje, historia, créditos de diseño/herrería, materiales y múltiples fotografías (`fotos_traje`). Todo envío comunitario se guarda estrictamente con `estado = 'pendiente'`.
   - **Bandeja de Moderación en Panel Admin (`templates/admin.html`):** Nueva sección destacada con el bucle `{% for traje in trajes_pendientes %}` y botones de decisión:
     - **"Aprobar"** (`POST/PUT /api/trajes/aprobar/<id>` y `/admin/aprobar/<id>`): Ejecuta `UPDATE trajes SET estado = 'publicado' WHERE id = ?` y transfiere el traje inmediatamente al catálogo público.
     - **"Rechazar"** (`DELETE/POST /api/trajes/rechazar/<id>` y `/admin/rechazar/<id>`): Elimina el registro pendiente y sus fotografías asociadas.
   - **Filtro Público Estricto:** El feed público (`/trajes`, `/api/trajes`), la colección de Obras Maestras (`/obras-maestras`, `/api/trajes/obras-maestras`) y las páginas de comparsas (`/comparsa/<nombre_comparsa>`) consultan exclusivamente `SELECT * FROM trajes WHERE estado = 'publicado'`.
2. **Módulo 2: Páginas de Comparsas y Seed de Datos Automático (`seed.py`, `app.py`, `templates/comparsa.html`):**
   - **Script Independiente `seed.py`:** Script ejecutable en la raíz del proyecto que conecta a `carnaval.db` e inyecta 6 trajes realistas del Carnaval de Corrientes con `estado = 'publicado'`, créditos de herrería, diseño original, materiales de alta costura, descripciones ricas y galería en `fotos_traje`, cubriendo las 6 agrupaciones emblemáticas: **Arandú Beleza**, **Sapucay**, **Ará Berá**, **Samba Total**, **Copacabana** e **Imperio Bahiano**.
   - **Vista Genérica `GET /comparsa/<nombre_comparsa>`:** Renderiza `templates/comparsa.html` mostrando el título dinámico, apodo histórico ("La Verde y Blanca", "El Gallo", "El Rayo", "La Aplanadora del Ritmo", "La Decana", "La Fuerza Bahiana"), colores e historia de la agrupación, junto con la grilla filtrada de trajes publicados de esa comparsa y barra de navegación rápida entre agrupaciones.
3. **Módulo 3: Libre Albedrío UX - Mejoras No Destructivas del Carnaval Correntino (`css/estilos.css`, `js/main.js`, `templates/traje-detalle.html`, `templates/coordinacion.html`):**
   - **Mejora Autónoma #1 (Contador Regresivo del Carnaval Correntino):** Función `initCarnavalCountdown()` en `js/main.js` y barra `.carnaval-countdown-bar` en el header que muestra en tiempo real los días, horas, minutos y segundos hasta la noche inaugural en el Corsódromo "Nolo Alías", acompañada de un CTA directo a `/comunidad/subir`.
   - **Mejora Autónoma #2 (Brillo / Purpurina en Obras Maestras):** Animación CSS GPU-accelerated (`@keyframes destelloPurpurinaCarnaval` y `@keyframes pulsoInsigniaObraMaestra`) en `.coordinacion-card` y `.obra-maestra-glitter` que recrea el destello especular del strass boreal bajo los reflectores del corsódromo.
   - **Mejora Autónoma #3 (Open Graph Enriquecido + Botón WhatsApp):** Metadatos Open Graph completos (`og:type`, `og:site_name`, `og:locale`, `og:title`, `og:description`, `og:image`, `og:image:alt`, `og:url`) y botón nativo **"📲 Compartir en WhatsApp"** en `templates/traje-detalle.html`.

---

### Fase 13: Arquitectura Definitiva (Galería Dinámica, Edición, Obras Maestras y Fix de Feed)
**Estado:** COMPLETADA ✅
**Hito Registrado:** Ciclo CRUD Completo, Filtro de Obras Maestras (`es_obra_maestra = 1`), Galería Múltiple y Eliminación de Jinja Crudo

#### Enfoque Arquitectural:
- **Actualización Estructural de Base de Datos (`database.py` & `carnaval.db`):**
  - Consolidación de columnas extendidas en tabla `trajes`: `descripcion` (TEXT), `diseno_original` (TEXT), `herreria_estructura` (TEXT) y `es_obra_maestra` (`BOOLEAN DEFAULT 0`), con migración dinámica en caliente (`PRAGMA table_info`).
  - Tabla `fotos_traje` (`id` PK, `traje_id` FK con `ON DELETE CASCADE`, `ruta_imagen`, `titulo`, `es_principal` BOOLEAN) sincronizada automáticamente con la portada de cada traje.
- **Fix del Feed "Scroll Snap", Obras Maestras y Enlaces SSR (`app.py`, `templates/trajes.html`, `templates/coordinacion.html`):**
  - **Feed Vertical de Trajes (`/trajes`, `/pages/trajes.html`):** Consulta estricta `SELECT * FROM trajes ORDER BY id DESC` sin filtros hardcodeados por comparsa; todo traje insertado aparece inmediatamente en el scroll público.
  - **Sección Obras Maestras (`/obras-maestras`, `/coordinacion`, `/pages/coordinacion.html`):** Renderización SSR con filtro estricto `SELECT * FROM trajes WHERE es_obra_maestra = 1 ORDER BY id DESC`.
  - **Corrección de Enlaces y Prevención de Jinja Crudo:** Estandarización del endpoint `detalle_traje` (`/traje/<int:id>`) y uso de `url_for('detalle_traje', id=traje.id)` en todas las plantillas, redirigiendo cualquier petición heredada a `/pages/traje-detalle.html` hacia el motor SSR de Flask.
- **Backend CRUD Completo (`app.py`):**
  - `POST /api/trajes`: Procesamiento de `descripcion`, `diseno_original`, `herreria_estructura`, booleano `es_obra_maestra` (checkbox) y subida múltiple de imágenes en `fotos_traje`.
  - `GET /admin/editar/<int:id>`: Renderizado del formulario administrativo pre-poblado con todos los metadatos y fotografías actuales del traje.
  - `POST/PUT /api/trajes/editar/<int:id>`: Actualización (`UPDATE`) de textos, estado de Obra Maestra, edición de títulos de fotos, cambio de portada (`es_principal`), eliminación selectiva de fotos existentes y adición de nuevas imágenes.
  - `DELETE /api/trajes/<int:id>`: Eliminación integral de trajes, sus fotografías en `fotos_traje` y comentarios asociados.
- **Actualización del Dashboard Administrativo (`templates/admin.html`, `pages/admin.html`, `admin.html`):**
  - Incorporación de campos de Descripción, Diseño Original, Herrería/Estructura y `<input type="checkbox" name="es_obra_maestra">` ("Destacar en Obras Maestras").
  - Interfaz de selección múltiple de archivos (`<input type="file" name="fotos" multiple>`) con previsualización instantánea, edición de títulos individuales y selector de portada.
  - Tabla de **Lista de Trajes Cargados (Dashboard)** con botón **"Editar"** (`/admin/editar/<id>`) junto al botón **"Eliminar"**.

---

### Fase 12: Expansión de Base de Datos, Galería Dinámica y Fix de Filtros
**Estado:** COMPLETADA ✅
**Hito Registrado:** Galería Fotográfica Múltiple, Créditos Enriquecidos y Feed Absoluto

#### Enfoque Arquitectural:
- **Evolución del Esquema Relacional (SQLite):**
  - Incorporación de metadatos narrativos y créditos en `trajes`: `descripcion` (párrafo inspiracional), `diseno_original` (créditos de boceto), `herreria_estructura` (detalles y peso de arnés).
  - Creación de la tabla `fotos_traje`: modelado 1:N (`traje_id`, `ruta_imagen`, `titulo`, `es_principal`) con soporte de claves foráneas y cascada de eliminación. Migración automática retroactiva para sincronizar `foto_url` preexistentes.
- **Fix Integral del Feed Móvil (Scroll Snap):**
  - Eliminación de cualquier filtro hardcodeado que limitara la vista solo a comparsas conocidas.
  - Implementación de consulta `SELECT * FROM trajes ORDER BY id DESC` absoluto tanto en el endpoint REST `/api/trajes` como en la renderización Server-Side Rendering (`/trajes`, `/pages/trajes.html` con `templates/trajes.html`). Todo traje registrado desde el CMS aparece inmediatamente en el feed vertical de trajes.
- **CMS Dinámico de Múltiples Imágenes (`admin.html`):**
  - Refactor del formulario de carga para soportar agregado interactivo de fotografías múltiples con títulos personalizados y selector radial para definir la foto principal de portada (`es_principal = 1`).
  - Inputs dedicados para "Descripción de la obra", "Diseño Original" y "Herrería/Estructura".
- **Backend Multilateral (`app.py`):**
  - Endpoint `POST /api/trajes` optimizado para procesar `files = request.files.getlist("fotos")`, persistir físicamente los binarios en `assets/img/` y registrar cada imagen vinculada en `fotos_traje`.
  - Enriquecimiento de `ver_traje_ssr` (`/traje/<id>`) para inyectar dinámicamente las fotos secundarias en las miniaturas de la galería y mostrar los créditos de producción.

---

### Fase 11: Autenticación del Panel de Administración
**Estado:** COMPLETADA ✅
**Hito Registrado:** Seguridad y Control de Acceso con Sesiones Flask

#### Enfoque Arquitectural:
- Protección perimetral completa de la interfaz de administración (`/admin`) y de los endpoints de mutación en la API REST (`POST /api/trajes`, `DELETE /api/comentarios/<id>`).
- Implementación de control de sesiones basado en cookies firmadas criptográficamente (`Flask.session`) usando `app.secret_key = 'una_clave_secreta_muy_dificil_de_adivinar'`.
- Autenticación con contraseña maestra centralizada (`ADMIN_PASSWORD = 'noloalias2026'`) con validación server-side.
- Manejo de ciclo de vida de sesión completo: autenticación mediante formulario en `/login`, revocación y destrucción de sesión en `/logout`, y redirecciones contextuales según estado de sesión.

#### Entregables Implementados:
1. **Configuración de Seguridad en Backend (`app.py`):**
   - Configuración de clave de firma de cookies: `app.secret_key = 'una_clave_secreta_muy_dificil_de_adivinar'`.
   - Definición de credencial maestra: `ADMIN_PASSWORD = 'noloalias2026'`.
   - Middleware de comprobación de sesión en `@app.route('/admin')`: redirige a `/login` si `not session.get('admin_logged_in')`.
   - Protección de endpoints de escritura y borrado: `POST /api/trajes` y `DELETE /api/comentarios/<int:id>` devuelven `401 Unauthorized` si no existe sesión activa.
   - Endpoint `@app.route('/login', methods=['GET', 'POST'])`:
     - `POST`: valida la contraseña contra `ADMIN_PASSWORD`; ante éxito, establece `session['admin_logged_in'] = True` y redirige a `/admin`; ante fallo, retorna feedback visual con mensaje de error.
     - `GET`: si ya existe sesión activa, redirige automáticamente a `/admin`; de lo contrario renderiza `login.html`.
   - Endpoint `@app.route('/logout')`: elimina `admin_logged_in` de `session` y redirige al inicio (`/`).
2. **Interfaz de Acceso (`templates/login.html`, `pages/login.html`, `login.html`):**
   - Formulario elegante y minimalista acorde a la estética dark/gold de Hugo Fernández.
   - Campo individual de contraseña `<input type="password" id="password" name="password" required>` (sin usuario).
   - Manejo de alertas de error con animación visual de feedback.
   - Enlace de retorno directo a la página principal.
3. **Barra de Navegación del Panel (`templates/admin.html`, `pages/admin.html`, `admin.html`):**
   - Botón directo de "Cerrar Sesión" (`/logout`) en el header administrativo.

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
