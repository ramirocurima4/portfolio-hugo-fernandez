"""
Hugo Fernández Arte Creativo - Servidor Backend Flask
FASE 13: Arquitectura Definitiva (Galería Dinámica, Edición, Obras Maestras y Fix de Feed).
FASE 14: Módulo Social (Comunidad & Moderación), Seed de Datos y Páginas Dinámicas de Comparsas.
"""

import os
import shutil
import time
import unicodedata
from werkzeug.utils import secure_filename
from flask import Flask, jsonify, request, send_from_directory, render_template, url_for, session, redirect
from database import get_db_connection, init_db

# Configuración de directorios para SSR y archivos estáticos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Flask(
    __name__,
    template_folder=TEMPLATES_DIR,
    static_folder=STATIC_DIR,
    static_url_path="/static"
)

# FASE 10: Configuración de carpeta de subida de imágenes
app.config['UPLOAD_FOLDER'] = 'assets/img/'

# FASE 11: Configuración de sesiones y contraseña maestra para administración
app.secret_key = 'una_clave_secreta_muy_dificil_de_adivinar'
ADMIN_PASSWORD = 'noloalias2026'


# ==============================================================================
# METADATOS CULTURALES DEL CARNAVAL CORRENTINO (FASE 14 - MÓDULO 2)
# ==============================================================================

COMPARSAS_OFICIALES = [
    {
        "nombre": "Arandú Beleza",
        "slug": "arandu-beleza",
        "apodo": "La Verde y Blanca",
        "categoria": "Comparsa de Primera Categoría • Corrientes Capital",
        "colores": "Verde Esmeralda, Blanco y Dorado",
        "historia": (
            "Fundada en 2005 en la Capital Nacional del Carnaval, Arandú Beleza ('Sabiduría y Belleza' en guaraní-portugués) "
            "irrumpió en el Corsódromo Nolo Alías con una impronta filosófica, mística y teatral inconfundible, destacándose "
            "por la audacia de sus diseños y la potencia de su escuela de samba."
        ),
    },
    {
        "nombre": "Sapucay",
        "slug": "sapucay",
        "apodo": "El Gallo del Carnaval",
        "categoria": "Comparsa de Primera Categoría • Corrientes Capital",
        "colores": "Rojo Rubí, Amarillo Oro y Negro",
        "historia": (
            "Nacida en 1980, Sapucay ('Grito Triunfal' en guaraní) es sinónimo de majestuosidad escénica, opulencia "
            "en carros alegóricos y perfección artesanal en herrería y plumaje de faisán dentro de la calzada del Nolo Alías."
        ),
    },
    {
        "nombre": "Ará Berá",
        "slug": "ara-bera",
        "apodo": "El Rayo",
        "categoria": "Comparsa de Primera Categoría • Corrientes Capital",
        "colores": "Rojo Fuego, Blanco Nieve y Plata",
        "historia": (
            "Fundada en 1961, Ará Berá ('Luz del Cielo' o 'Relámpago' en guaraní) electriza cada edición de los Carnavales "
            "Correntinos con el fervor de su hinchada, su mística histórica y la luminosidad de sus trajes bordados en cristal."
        ),
    },
    {
        "nombre": "Samba Total",
        "slug": "samba-total",
        "apodo": "La Aplanadora del Ritmo",
        "categoria": "Agrupación Musical Multicampeona • Corrientes Capital",
        "colores": "Azul Francia, Blanco y Plata",
        "historia": (
            "Máximo referente histórico entre las Agrupaciones Musicales del carnaval correntino. Sus vestuarios exigen "
            "ingeniería ergonómica de peso ultraliviano y articulación total para acompañar su arrolladora cadencia de batería."
        ),
    },
    {
        "nombre": "Copacabana",
        "slug": "copacabana",
        "apodo": "La Decana de los Carnavales Correntinos",
        "categoria": "Comparsa Pionera • Corrientes Capital",
        "colores": "Oro Imperial, Turquesa y Blanco",
        "historia": (
            "Pionera absoluta desde 1960 y cuna del esplendor del Carnaval de Corrientes. Copacabana representa la escuela "
            "clásica de alta costura artesanal, el lujo en pedrería fina y los grandes espaldares imperiales."
        ),
    },
    {
        "nombre": "Imperio Bahiano",
        "slug": "imperio-bahiano",
        "apodo": "La Fuerza Bahiana",
        "categoria": "Agrupación Musical • Corrientes Capital",
        "colores": "Verde Tropical, Amarillo Sol y Dorado",
        "historia": (
            "Agrupación musical de energía vibrante e identidad afro-bahiana que enciende las tribunas del corsódromo "
            "con percusión de alto impacto y vestuarios de gran destello cromático."
        ),
    },
    {
        "nombre": "Panambí",
        "slug": "panambi",
        "apodo": "El Origen en San Roque",
        "categoria": "Comparsa Tradicional • San Roque, Corrientes",
        "colores": "Dorado, Turquesa y Coral",
        "historia": (
            "La comparsa barrial de San Roque donde Hugo Fernández dio sus primeros pasos como comparsero en la calzada, "
            "forjando la sensibilidad técnica y el amor por el carnaval que hoy define a su taller."
        ),
    },
]


def normalizar_texto_comparacion(texto):
    """Elimina tildes, guiones y normaliza a minúsculas para comparar nombres o slugs de comparsas."""
    if not texto:
        return ""
    texto_limpio = str(texto).strip().replace("-", " ").replace("_", " ")
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", texto_limpio)
        if unicodedata.category(c) != "Mn"
    )
    return " ".join(sin_tildes.lower().split())


def obtener_info_comparsa(nombre_raw):
    """Retorna el diccionario de metadatos culturales de una comparsa a partir de su nombre o slug."""
    clave = normalizar_texto_comparacion(nombre_raw)
    for comp in COMPARSAS_OFICIALES:
        if clave in (
            normalizar_texto_comparacion(comp["nombre"]),
            normalizar_texto_comparacion(comp["slug"]),
        ) or normalizar_texto_comparacion(comp["nombre"]) in clave:
            return comp

    nombre_formateado = str(nombre_raw).replace("-", " ").strip().title()
    return {
        "nombre": nombre_formateado,
        "slug": normalizar_texto_comparacion(nombre_raw).replace(" ", "-"),
        "apodo": "Agrupación del Carnaval Correntino",
        "categoria": "Carnaval Oficial • Corrientes",
        "colores": "Dorado Escénico & Alta Costura",
        "historia": (
            f"Colección de vestuarios, estructuras de herrería y tocados realizados y coordinados "
            f"para las figuras de {nombre_formateado}."
        ),
    }


def obtener_comparsas_unicas():
    """
    Consulta estricta a la tabla trajes para inyectar la lista dinámica de comparsas únicas:
    SELECT DISTINCT comparsa FROM trajes WHERE estado = 'publicado'
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT comparsa FROM trajes WHERE estado = 'publicado' AND comparsa IS NOT NULL AND TRIM(comparsa) != '' ORDER BY comparsa ASC"
        )
        comparsas_unicas = [row["comparsa"] for row in cursor.fetchall()]
        conn.close()
        return comparsas_unicas
    except Exception:
        return [c["nombre"] for c in COMPARSAS_OFICIALES]


@app.context_processor
def inyectar_comparsas_unicas():
    """
    Inyecta automáticamente comparsas_unicas en todas las plantillas Jinja (index.html,
    trajes.html, coordinacion.html, comparsa.html, entrevistas.html, etc.).
    """
    return {"comparsas_unicas": obtener_comparsas_unicas()}


# ==============================================================================
# FUNCIONES AUXILIARES DE DATOS Y ARCHIVOS (FASE 13 & FASE 14)
# ==============================================================================

def enriquecer_traje(cursor, row):
    """
    Convierte una fila de 'trajes' en diccionario, normaliza 'es_obra_maestra' y 'estado',
    e inyecta su lista ordenada de fotografías desde 'fotos_traje'.
    """
    t = dict(row)
    t["es_obra_maestra"] = 1 if t.get("es_obra_maestra") in (1, True, "1", "true", "on") else 0
    t["estado"] = (t.get("estado") or "publicado").strip().lower()
    cursor.execute("""
        SELECT id, traje_id, ruta_imagen, titulo, es_principal 
        FROM fotos_traje 
        WHERE traje_id = ? 
        ORDER BY es_principal DESC, id ASC
    """, (t["id"],))
    fotos = [dict(f) for f in cursor.fetchall()]
    t["fotos"] = fotos
    if fotos and fotos[0].get("ruta_imagen"):
        t["foto_url"] = fotos[0]["ruta_imagen"]
    return t


def guardar_archivos_fisicos(files, titulos, principal_idx=None):
    """
    Guarda físicamente una lista de archivos FileStorage en assets/img/ y static/assets/img/.
    Retorna la lista de diccionarios listos para insertar en fotos_traje.
    """
    target_dir = os.path.join(BASE_DIR, "assets", "img")
    static_img_dir = os.path.join(STATIC_DIR, "assets", "img")
    os.makedirs(target_dir, exist_ok=True)
    os.makedirs(static_img_dir, exist_ok=True)

    fotos_guardadas = []
    for idx, file in enumerate(files):
        if not file or not getattr(file, "filename", ""):
            continue

        raw_filename = secure_filename(file.filename)
        if not raw_filename:
            raw_filename = f"traje_{int(time.time())}_{idx}.jpg"

        base_name, ext = os.path.splitext(raw_filename)
        if not ext:
            ext = ".jpg"
            raw_filename = f"{base_name}{ext}"

        filename = raw_filename
        counter = 1
        while os.path.exists(os.path.join(target_dir, filename)):
            filename = f"{base_name}_{counter}{ext}"
            counter += 1

        dest_path = os.path.join(target_dir, filename)
        file.save(dest_path)

        static_dest_path = os.path.join(static_img_dir, filename)
        shutil.copyfile(dest_path, static_dest_path)

        titulo = (
            titulos[idx].strip()
            if idx < len(titulos) and titulos[idx] and titulos[idx].strip()
            else ("Vista Principal" if idx == 0 else f"Detalle #{idx + 1}")
        )
        es_principal = 1 if (principal_idx is not None and idx == principal_idx) else 0
        foto_rel = f"assets/img/{filename}"

        fotos_guardadas.append({
            "ruta_imagen": foto_rel,
            "titulo": titulo,
            "es_principal": es_principal
        })

    return fotos_guardadas


def parsear_checkbox_obra_maestra(form_or_json):
    """Normaliza el valor de un checkbox HTML o booleano JSON a 1 o 0."""
    val = form_or_json.get("es_obra_maestra")
    if isinstance(val, bool):
        return 1 if val else 0
    if isinstance(val, int):
        return 1 if val == 1 else 0
    raw = str(val or "").strip().lower()
    return 1 if raw in ("1", "true", "on", "yes", "si", "sí") else 0


# ==============================================================================
# FASE 8, 12, 13 & 14: SERVER-SIDE RENDERING (SSR), FEED, OBRAS MAESTRAS Y COMPARSAS
# ==============================================================================

@app.route("/traje/<int:id>")
def detalle_traje(id):
    """
    FASE 8, 12, 13 & 14: Ruta oficial de detalle de traje (url_for('detalle_traje', id=traje.id)).
    Renderiza templates/traje-detalle.html con SSR, etiquetas Open Graph enriquecidas para WhatsApp,
    galería fotográfica completa (fotos_traje) y créditos técnicos.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trajes WHERE id = ?", (id,))
    row = cursor.fetchone()

    if row is None:
        conn.close()
        return jsonify({"error": "Traje no encontrado"}), 404

    traje = enriquecer_traje(cursor, row)
    conn.close()

    fotos = traje.get("fotos", [])
    materiales_lista = [m.strip() for m in (traje.get("materiales") or "").rstrip(".").split(",") if m.strip()]

    return render_template("traje-detalle.html", traje=traje, materiales_lista=materiales_lista, fotos=fotos)


# Mantener alias de endpoint ver_traje_ssr por compatibilidad retroactiva
app.add_url_rule("/traje/<int:id>", endpoint="ver_traje_ssr", view_func=detalle_traje)


@app.route("/trajes")
@app.route("/trajes.html")
@app.route("/pages/trajes.html")
def ver_trajes_feed():
    """
    FASE 13 & FASE 14 (Módulo 1): Feed Vertical de Trajes ("Scroll Snap").
    Filtra estrictamente los trajes publicados:
    SELECT * FROM trajes WHERE estado = 'publicado' ORDER BY id DESC.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trajes WHERE estado = 'publicado' ORDER BY id DESC")
    rows = cursor.fetchall()
    trajes = [enriquecer_traje(cursor, r) for r in rows]
    conn.close()

    return render_template("trajes.html", trajes=trajes)


@app.route("/obras-maestras")
@app.route("/coordinacion")
@app.route("/coordinacion.html")
@app.route("/pages/coordinacion.html")
def obras_maestras():
    """
    FASE 13 & FASE 14 (Módulo 1): Sección "Obras Maestras".
    Filtra con SELECT * FROM trajes WHERE estado = 'publicado' AND es_obra_maestra = 1 ORDER BY id DESC.
    Renderiza con enlaces url_for('detalle_traje', id=traje.id).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trajes WHERE estado = 'publicado' AND es_obra_maestra = 1 ORDER BY id DESC")
    rows = cursor.fetchall()
    trajes = [enriquecer_traje(cursor, r) for r in rows]
    conn.close()

    return render_template("coordinacion.html", trajes=trajes)


@app.route("/comparsa/<path:nombre>", endpoint="vista_comparsa")
def vista_comparsa(nombre=None, nombre_comparsa=None):
    """
    FASE 14 (Módulo 2): Vista genérica GET /comparsa/<nombre> (url_for('vista_comparsa', nombre=comparsa)).
    Renderiza comparsa.html mostrando el título dinámico e identidad de la agrupación
    y filtrando únicamente los trajes con estado = 'publicado' correspondientes a esa comparsa.
    """
    nombre_objetivo = nombre if nombre is not None else nombre_comparsa
    info_comparsa = obtener_info_comparsa(nombre_objetivo)
    clave_buscada = normalizar_texto_comparacion(info_comparsa["nombre"])
    clave_raw = normalizar_texto_comparacion(nombre_objetivo)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trajes WHERE estado = 'publicado' ORDER BY id DESC")
    rows = cursor.fetchall()

    trajes_comparsa = []
    for r in rows:
        comp_row = normalizar_texto_comparacion(r["comparsa"])
        if comp_row == clave_buscada or comp_row == clave_raw or clave_buscada in comp_row or clave_raw in comp_row:
            trajes_comparsa.append(enriquecer_traje(cursor, r))

    conn.close()

    return render_template(
        "comparsa.html",
        nombre_comparsa=info_comparsa["nombre"],
        info_comparsa=info_comparsa,
        trajes=trajes_comparsa,
        comparsas_oficiales=COMPARSAS_OFICIALES,
    )


# Alias de compatibilidad retroactiva para url_for('ver_comparsa', nombre_comparsa=...)
app.add_url_rule("/comparsa/<path:nombre_comparsa>", endpoint="ver_comparsa", view_func=vista_comparsa)


@app.route("/comunidad/subir", methods=["GET", "POST"])
@app.route("/pages/comunidad-subir.html", methods=["GET", "POST"])
def comunidad_subir():
    """
    FASE 14 (Módulo 1): Comunidad de Comparseros y Moderación.
    GET: Muestra el formulario público donde los comparseros pueden subir su propio traje.
    POST: Guarda el traje en la base de datos con estado = 'pendiente' y procesa múltiples fotos.
    """
    if request.method == "GET":
        enviado = request.args.get("enviado") == "1"
        return render_template(
            "comunidad_subir.html",
            exito=enviado,
            traje_enviado=None,
            comparsas_oficiales=COMPARSAS_OFICIALES,
        )

    # Procesar POST de la comunidad
    data_source = request.form if request.form else (request.get_json(silent=True) or {})
    comparsero = (data_source.get("comparsero") or "").strip()
    comparsa = (data_source.get("comparsa") or "").strip()
    genero = (data_source.get("genero") or "Femenino").strip()
    materiales = (data_source.get("materiales") or "Cristales, plumas y estructura artesanal de carnaval").strip()
    descripcion = (data_source.get("descripcion") or "").strip()
    diseno_original = (data_source.get("diseno_original") or "").strip()
    herreria_estructura = (data_source.get("herreria_estructura") or "").strip()

    wants_json = (
        request.is_json
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or "application/json" in (request.headers.get("Accept") or "")
    )

    if not comparsero or not comparsa:
        if wants_json:
            return jsonify({"error": "Los campos 'comparsero' y 'comparsa' son obligatorios."}), 400
        return render_template(
            "comunidad_subir.html",
            error="Por favor completá el nombre de la figura/comparsero y la comparsa.",
            comparsas_oficiales=COMPARSAS_OFICIALES,
        ), 400

    files = [f for f in request.files.getlist("fotos") if f and f.filename != ""]
    if not files:
        files = [f for f in request.files.getlist("foto") if f and f.filename != ""]

    titulos = request.form.getlist("titulos_fotos") if request.form else []
    try:
        principal_idx = int(data_source.get("foto_principal_index", 0))
    except (ValueError, TypeError):
        principal_idx = 0

    fotos_guardadas = guardar_archivos_fisicos(files, titulos, principal_idx)

    # Si no se subieron archivos binarios pero se envió foto_url (o fallback para pruebas)
    if not fotos_guardadas:
        foto_fallback = (
            data_source.get("foto_url")
            or "https://images.unsplash.com/photo-1549488344-1f9b8d2bd1f3?q=80&w=800&auto=format&fit=crop"
        ).strip()
        fotos_guardadas = [{
            "ruta_imagen": foto_fallback,
            "titulo": "Vista Principal (Comunidad)",
            "es_principal": 1
        }]

    if not any(f["es_principal"] == 1 for f in fotos_guardadas):
        fotos_guardadas[0]["es_principal"] = 1

    foto_principal_url = next(f["ruta_imagen"] for f in fotos_guardadas if f["es_principal"] == 1)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO trajes (
            comparsero, comparsa, genero, materiales, foto_url,
            descripcion, diseno_original, herreria_estructura, es_obra_maestra, estado
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 'pendiente')
    """, (
        comparsero, comparsa, genero, materiales, foto_principal_url,
        descripcion, diseno_original, herreria_estructura
    ))
    nuevo_id = cursor.lastrowid

    for f in fotos_guardadas:
        cursor.execute("""
            INSERT INTO fotos_traje (traje_id, ruta_imagen, titulo, es_principal)
            VALUES (?, ?, ?, ?)
        """, (nuevo_id, f["ruta_imagen"], f["titulo"], f["es_principal"]))

    conn.commit()

    cursor.execute("SELECT * FROM trajes WHERE id = ?", (nuevo_id,))
    traje_creado = enriquecer_traje(cursor, cursor.fetchone())
    conn.close()

    if wants_json:
        return jsonify({
            "mensaje": "Traje recibido con éxito. Quedó en estado 'pendiente' en la Bandeja de Moderación.",
            "traje": traje_creado
        }), 201

    return render_template(
        "comunidad_subir.html",
        exito=True,
        traje_enviado=traje_creado,
        comparsas_oficiales=COMPARSAS_OFICIALES,
    ), 201


@app.route("/traje-detalle.html")
@app.route("/pages/traje-detalle.html")
def traje_detalle_legacy_proxy():
    """
    FASE 13 (Paso 2): Evita que se sirva pages/traje-detalle.html como archivo estático
    con Jinja crudo. Redirige o renderiza siempre mediante detalle_traje (SSR).
    """
    traje_id = request.args.get("id")
    if traje_id and traje_id.isdigit():
        return redirect(url_for("detalle_traje", id=int(traje_id)))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM trajes WHERE estado = 'publicado' ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    default_id = row["id"] if row else 1
    return redirect(url_for("detalle_traje", id=default_id))


# ==============================================================================
# RUTAS DE ADMINISTRACIÓN, MODERACIÓN Y EDICIÓN (CMS - FASE 10, 11, 13 & 14)
# ==============================================================================

@app.route("/admin")
@app.route("/admin.html")
@app.route("/pages/admin.html")
def admin_panel():
    """
    Sirve el Dashboard de Gestión, Bandeja de Moderación (FASE 14) y Panel CMS.
    Protegido por autenticación de sesión maestra.
    """
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trajes WHERE estado = 'pendiente' ORDER BY id DESC")
    trajes_pendientes = [enriquecer_traje(cursor, r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM trajes WHERE estado = 'publicado' ORDER BY id DESC")
    trajes = [enriquecer_traje(cursor, r) for r in cursor.fetchall()]
    conn.close()

    return render_template(
        "admin.html",
        trajes=trajes,
        trajes_pendientes=trajes_pendientes,
        traje_editar=None,
    )


@app.route("/admin/editar/<int:id>", methods=["GET"])
def admin_editar_traje(id):
    """
    FASE 13 (Paso 3): NUEVA RUTA - GET /admin/editar/<id>
    Renderiza el formulario de administración pre-poblado con los datos
    y fotografías del traje existente para su edición.
    """
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trajes WHERE id = ?", (id,))
    row = cursor.fetchone()

    if row is None:
        conn.close()
        return redirect(url_for("admin_panel"))

    traje_editar = enriquecer_traje(cursor, row)

    cursor.execute("SELECT * FROM trajes WHERE estado = 'pendiente' ORDER BY id DESC")
    trajes_pendientes = [enriquecer_traje(cursor, r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM trajes WHERE estado = 'publicado' ORDER BY id DESC")
    trajes = [enriquecer_traje(cursor, r) for r in cursor.fetchall()]
    conn.close()

    return render_template(
        "admin.html",
        trajes=trajes,
        trajes_pendientes=trajes_pendientes,
        traje_editar=traje_editar,
    )


@app.route("/admin/aprobar/<int:id>", methods=["POST", "PUT"])
@app.route("/api/trajes/aprobar/<int:id>", methods=["POST", "PUT"])
def aprobar_traje_moderacion(id):
    """
    FASE 14 (Módulo 1): Aprueba un traje enviado por la comunidad en la Bandeja de Moderación,
    ejecutando UPDATE trajes SET estado = 'publicado' WHERE id = ?.
    """
    if not session.get("admin_logged_in"):
        return jsonify({"error": "No autorizado. Sesión de administrador requerida."}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trajes WHERE id = ?", (id,))
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return jsonify({"error": "Traje no encontrado"}), 404

    cursor.execute("UPDATE trajes SET estado = 'publicado' WHERE id = ?", (id,))
    conn.commit()

    cursor.execute("SELECT * FROM trajes WHERE id = ?", (id,))
    traje_aprobado = enriquecer_traje(cursor, cursor.fetchone())
    conn.close()

    wants_json = (
        request.path.startswith("/api/")
        or request.is_json
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or "application/json" in (request.headers.get("Accept") or "")
    )
    if wants_json:
        return jsonify({
            "mensaje": "Traje aprobado y publicado en el catálogo oficial",
            "id": id,
            "estado": "publicado",
            "traje": traje_aprobado,
        }), 200

    return redirect(url_for("admin_panel") + "#bandeja-moderacion")


@app.route("/admin/rechazar/<int:id>", methods=["POST", "DELETE"])
@app.route("/api/trajes/rechazar/<int:id>", methods=["POST", "DELETE"])
def rechazar_traje_moderacion(id):
    """
    FASE 14 (Módulo 1): Rechaza un traje pendiente en la Bandeja de Moderación,
    eliminando el registro y sus fotografías asociadas de la base de datos.
    """
    if not session.get("admin_logged_in"):
        return jsonify({"error": "No autorizado. Sesión de administrador requerida."}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, comparsero FROM trajes WHERE id = ?", (id,))
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return jsonify({"error": "Traje no encontrado"}), 404

    cursor.execute("DELETE FROM fotos_traje WHERE traje_id = ?", (id,))
    cursor.execute("DELETE FROM comentarios WHERE traje_id = ?", (id,))
    cursor.execute("DELETE FROM trajes WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    wants_json = (
        request.path.startswith("/api/")
        or request.is_json
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or "application/json" in (request.headers.get("Accept") or "")
    )
    if wants_json:
        return jsonify({
            "mensaje": "Propuesta de traje rechazada y eliminada de la bandeja",
            "id": id,
        }), 200

    return redirect(url_for("admin_panel") + "#bandeja-moderacion")


@app.route("/login", methods=["GET", "POST"])
@app.route("/login.html", methods=["GET", "POST"])
@app.route("/pages/login.html", methods=["GET", "POST"])
def login():
    """Ruta de autenticación para administradores con contraseña maestra (FASE 11)."""
    if request.method == "POST":
        password = (request.form.get("password") or "").strip()
        if password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_panel"))
        return render_template("login.html", error="Contraseña incorrecta. Intenta nuevamente.")

    if session.get("admin_logged_in"):
        return redirect(url_for("admin_panel"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Cierra la sesión del administrador y redirige a la página de inicio."""
    session.pop("admin_logged_in", None)
    return redirect(url_for("index"))


# ==============================================================================
# ENDPOINTS DE API REST - CRUD COMPLETO DE TRAJES (FASE 13)
# ==============================================================================

@app.route("/api/trajes", methods=["GET"])
def get_trajes():
    """
    Retorna la lista de trajes publicados almacenados en carnaval.db en formato JSON.
    FASE 14 (Módulo 1): Filtra con SELECT * FROM trajes WHERE estado = 'publicado' ORDER BY id DESC.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trajes WHERE estado = 'publicado' ORDER BY id DESC")
    rows = cursor.fetchall()
    trajes = [enriquecer_traje(cursor, r) for r in rows]
    conn.close()
    return jsonify(trajes), 200


@app.route("/api/trajes/pendientes", methods=["GET"])
def get_trajes_pendientes():
    """
    FASE 14 (Módulo 1): Retorna los trajes en estado 'pendiente' para la Bandeja de Moderación.
    """
    if not session.get("admin_logged_in"):
        return jsonify({"error": "No autorizado. Sesión de administrador requerida."}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trajes WHERE estado = 'pendiente' ORDER BY id DESC")
    rows = cursor.fetchall()
    trajes = [enriquecer_traje(cursor, r) for r in rows]
    conn.close()
    return jsonify(trajes), 200


@app.route("/api/trajes/obras-maestras", methods=["GET"])
def get_obras_maestras():
    """Retorna únicamente los trajes publicados marcados como Obra Maestra (es_obra_maestra = 1)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trajes WHERE estado = 'publicado' AND es_obra_maestra = 1 ORDER BY id DESC")
    rows = cursor.fetchall()
    trajes = [enriquecer_traje(cursor, r) for r in rows]
    conn.close()
    return jsonify(trajes), 200


@app.route("/api/trajes", methods=["POST"])
def post_traje():
    """
    FASE 13 (Paso 3) & FASE 14: POST /api/trajes (Creación directa por Administrador).
    Recibe los campos de texto, el booleano es_obra_maestra (desde checkbox),
    asigna estado = 'publicado' y procesa múltiples imágenes insertándolas en fotos_traje.
    """
    if not session.get("admin_logged_in"):
        return jsonify({"error": "No autorizado. Sesión de administrador requerida."}), 401

    comparsero = (request.form.get("comparsero") or "").strip()
    comparsa = (request.form.get("comparsa") or "").strip()
    genero = (request.form.get("genero") or "Femenino").strip()
    materiales = (request.form.get("materiales") or "").strip()
    descripcion = (request.form.get("descripcion") or "").strip()
    diseno_original = (request.form.get("diseno_original") or "").strip()
    herreria_estructura = (request.form.get("herreria_estructura") or "").strip()
    es_obra_maestra = parsear_checkbox_obra_maestra(request.form)

    if not comparsero or not comparsa:
        return jsonify({"error": "Los campos 'comparsero' y 'comparsa' son obligatorios."}), 400

    # Soportar selección múltiple en input 'fotos' o 'foto'
    files = [f for f in request.files.getlist("fotos") if f and f.filename != ""]
    if not files:
        files = [f for f in request.files.getlist("foto") if f and f.filename != ""]

    if not files:
        return jsonify({"error": "No se seleccionó ningún archivo de imagen para el traje."}), 400

    titulos = request.form.getlist("titulos_fotos")
    try:
        principal_idx = int(request.form.get("foto_principal_index", 0))
    except (ValueError, TypeError):
        principal_idx = 0

    fotos_guardadas = guardar_archivos_fisicos(files, titulos, principal_idx)
    if not fotos_guardadas:
        return jsonify({"error": "No se pudieron procesar las fotografías enviadas."}), 400

    if not any(f["es_principal"] == 1 for f in fotos_guardadas):
        fotos_guardadas[0]["es_principal"] = 1

    foto_principal_url = next(f["ruta_imagen"] for f in fotos_guardadas if f["es_principal"] == 1)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO trajes (
            comparsero, comparsa, genero, materiales, foto_url,
            descripcion, diseno_original, herreria_estructura, es_obra_maestra, estado
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'publicado')
    """, (
        comparsero, comparsa, genero, materiales, foto_principal_url,
        descripcion, diseno_original, herreria_estructura, es_obra_maestra
    ))
    nuevo_id = cursor.lastrowid

    for f in fotos_guardadas:
        cursor.execute("""
            INSERT INTO fotos_traje (traje_id, ruta_imagen, titulo, es_principal)
            VALUES (?, ?, ?, ?)
        """, (nuevo_id, f["ruta_imagen"], f["titulo"], f["es_principal"]))

    conn.commit()

    cursor.execute("SELECT * FROM trajes WHERE id = ?", (nuevo_id,))
    nuevo_traje = enriquecer_traje(cursor, cursor.fetchone())
    conn.close()

    return jsonify({
        "mensaje": "Traje y galería registrados con éxito en el catálogo",
        "traje": nuevo_traje
    }), 201


@app.route("/api/trajes/editar/<int:id>", methods=["POST", "PUT"])
@app.route("/api/trajes/<int:id>", methods=["PUT"])
def editar_traje(id):
    """
    FASE 13 (Paso 3): NUEVA RUTA - POST/PUT /api/trajes/editar/<id>
    Ejecuta UPDATE en la base de datos con los nuevos textos, el estado del checkbox
    es_obra_maestra, y permite agregar/eliminar fotos asociadas y elegir la foto principal.
    """
    if not session.get("admin_logged_in"):
        return jsonify({"error": "No autorizado. Sesión de administrador requerida."}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trajes WHERE id = ?", (id,))
    traje_actual = cursor.fetchone()

    if traje_actual is None:
        conn.close()
        return jsonify({"error": "Traje no encontrado"}), 404

    data_source = request.form if request.form else (request.get_json(silent=True) or {})

    comparsero = (data_source.get("comparsero") or traje_actual["comparsero"] or "").strip()
    comparsa = (data_source.get("comparsa") or traje_actual["comparsa"] or "").strip()
    genero = (data_source.get("genero") or traje_actual["genero"] or "Femenino").strip()
    materiales = (data_source.get("materiales") if "materiales" in data_source else (traje_actual["materiales"] or "")).strip()
    descripcion = (data_source.get("descripcion") if "descripcion" in data_source else (traje_actual["descripcion"] or "")).strip()
    diseno_original = (data_source.get("diseno_original") if "diseno_original" in data_source else (traje_actual["diseno_original"] or "")).strip()
    herreria_estructura = (data_source.get("herreria_estructura") if "herreria_estructura" in data_source else (traje_actual["herreria_estructura"] or "")).strip()
    es_obra_maestra = parsear_checkbox_obra_maestra(data_source)

    if not comparsero or not comparsa:
        conn.close()
        return jsonify({"error": "Los campos 'comparsero' y 'comparsa' son obligatorios."}), 400

    # 1. Eliminar fotos marcadas para eliminación
    fotos_eliminar_ids = []
    if request.form:
        fotos_eliminar_ids.extend(request.form.getlist("fotos_eliminar"))
        fotos_eliminar_ids.extend(request.form.getlist("eliminar_fotos"))
    elif isinstance(data_source.get("fotos_eliminar"), list):
        fotos_eliminar_ids.extend(data_source.get("fotos_eliminar"))

    for raw_fid in fotos_eliminar_ids:
        for fid_part in str(raw_fid).split(","):
            fid_str = fid_part.strip()
            if fid_str.isdigit():
                cursor.execute("DELETE FROM fotos_traje WHERE id = ? AND traje_id = ?", (int(fid_str), id))

    # 2. Actualizar títulos de fotos existentes que permanecen
    if request.form:
        cursor.execute("SELECT id FROM fotos_traje WHERE traje_id = ?", (id,))
        remaining_ids = [r["id"] for r in cursor.fetchall()]
        for fid in remaining_ids:
            key = f"titulo_existente_{fid}"
            if key in request.form:
                nuevo_titulo = request.form.get(key, "").strip() or "Vista del Traje"
                cursor.execute("UPDATE fotos_traje SET titulo = ? WHERE id = ? AND traje_id = ?", (nuevo_titulo, fid, id))

    # 3. Procesar e insertar nuevas fotos subidas (si las hay)
    files = [f for f in request.files.getlist("fotos") if f and f.filename != ""]
    if not files:
        files = [f for f in request.files.getlist("foto") if f and f.filename != ""]

    titulos_nuevas = request.form.getlist("titulos_fotos") if request.form else []
    nuevas_fotos_guardadas = guardar_archivos_fisicos(files, titulos_nuevas, principal_idx=None)

    nuevas_fotos_db_ids = []
    for nf in nuevas_fotos_guardadas:
        cursor.execute("""
            INSERT INTO fotos_traje (traje_id, ruta_imagen, titulo, es_principal)
            VALUES (?, ?, ?, 0)
        """, (id, nf["ruta_imagen"], nf["titulo"]))
        nuevas_fotos_db_ids.append(cursor.lastrowid)

    # 4. Determinar foto principal según elección del usuario
    choice = (request.form.get("foto_principal_choice") or "").strip() if request.form else ""
    if choice.startswith("existing_"):
        fid_str = choice.replace("existing_", "").strip()
        if fid_str.isdigit():
            target_fid = int(fid_str)
            cursor.execute("UPDATE fotos_traje SET es_principal = 0 WHERE traje_id = ?", (id,))
            cursor.execute("UPDATE fotos_traje SET es_principal = 1 WHERE id = ? AND traje_id = ?", (target_fid, id))
    elif choice.startswith("new_"):
        idx_str = choice.replace("new_", "").strip()
        if idx_str.isdigit():
            new_idx = int(idx_str)
            if 0 <= new_idx < len(nuevas_fotos_db_ids):
                target_fid = nuevas_fotos_db_ids[new_idx]
                cursor.execute("UPDATE fotos_traje SET es_principal = 0 WHERE traje_id = ?", (id,))
                cursor.execute("UPDATE fotos_traje SET es_principal = 1 WHERE id = ? AND traje_id = ?", (target_fid, id))

    # 5. Garantizar que exista una foto principal y sincronizar foto_url en trajes
    cursor.execute("""
        SELECT id, ruta_imagen, es_principal 
        FROM fotos_traje 
        WHERE traje_id = ? 
        ORDER BY es_principal DESC, id ASC
    """, (id,))
    fotos_actualizadas = cursor.fetchall()

    foto_principal_url = traje_actual["foto_url"]
    if fotos_actualizadas:
        if not any(f["es_principal"] == 1 for f in fotos_actualizadas):
            primera_id = fotos_actualizadas[0]["id"]
            cursor.execute("UPDATE fotos_traje SET es_principal = 1 WHERE id = ?", (primera_id,))
            foto_principal_url = fotos_actualizadas[0]["ruta_imagen"]
        else:
            foto_principal_url = next(f["ruta_imagen"] for f in fotos_actualizadas if f["es_principal"] == 1)

    # 6. Ejecutar UPDATE en tabla trajes
    cursor.execute("""
        UPDATE trajes
        SET comparsero = ?,
            comparsa = ?,
            genero = ?,
            materiales = ?,
            foto_url = ?,
            descripcion = ?,
            diseno_original = ?,
            herreria_estructura = ?,
            es_obra_maestra = ?
        WHERE id = ?
    """, (
        comparsero, comparsa, genero, materiales, foto_principal_url,
        descripcion, diseno_original, herreria_estructura, es_obra_maestra, id
    ))

    conn.commit()

    cursor.execute("SELECT * FROM trajes WHERE id = ?", (id,))
    traje_final = enriquecer_traje(cursor, cursor.fetchone())
    conn.close()

    return jsonify({
        "mensaje": "Traje actualizado con éxito",
        "traje": traje_final
    }), 200


@app.route("/api/trajes/<int:id>", methods=["DELETE"])
@app.route("/api/trajes/eliminar/<int:id>", methods=["DELETE", "POST"])
def eliminar_traje(id):
    """
    Elimina un traje del catálogo junto con sus fotos asociadas y comentarios.
    Protegido por sesión de administrador.
    """
    if not session.get("admin_logged_in"):
        return jsonify({"error": "No autorizado. Sesión de administrador requerida."}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, comparsero FROM trajes WHERE id = ?", (id,))
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return jsonify({"error": "Traje no encontrado"}), 404

    cursor.execute("DELETE FROM fotos_traje WHERE traje_id = ?", (id,))
    cursor.execute("DELETE FROM comentarios WHERE traje_id = ?", (id,))
    cursor.execute("DELETE FROM trajes WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return jsonify({
        "mensaje": "Traje eliminado con éxito del catálogo",
        "id": id
    }), 200


@app.route("/api/trajes/filtrar", methods=["GET"])
def filtrar_trajes():
    """
    Endpoint de filtrado por Query String:
      - /api/trajes/filtrar?genero=Femenino
      - /api/trajes/filtrar?comparsa=Panambi
      - /api/trajes/filtrar?es_obra_maestra=1
    """
    genero = request.args.get("genero", "").strip()
    comparsa = request.args.get("comparsa", "").strip()
    busqueda = request.args.get("q", "").strip()
    obra_maestra = request.args.get("es_obra_maestra", "").strip()

    query = "SELECT * FROM trajes WHERE estado = 'publicado'"
    params = []

    if genero:
        query += " AND LOWER(genero) = LOWER(?)"
        params.append(genero)

    if comparsa:
        query += " AND LOWER(comparsa) LIKE LOWER(?)"
        params.append(f"%{comparsa}%")

    if obra_maestra in ("1", "0"):
        query += " AND es_obra_maestra = ?"
        params.append(int(obra_maestra))

    if busqueda:
        query += " AND (LOWER(comparsero) LIKE LOWER(?) OR LOWER(materiales) LIKE LOWER(?) OR LOWER(descripcion) LIKE LOWER(?))"
        params.extend([f"%{busqueda}%", f"%{busqueda}%", f"%{busqueda}%"])

    query += " ORDER BY id DESC"

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    trajes_filtrados = [enriquecer_traje(cursor, r) for r in rows]
    conn.close()

    return jsonify(trajes_filtrados), 200


@app.route("/api/trajes/<int:traje_id>", methods=["GET"])
def get_traje_por_id(traje_id):
    """Endpoint para consultar un traje individual por ID con su galería de fotos completa."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trajes WHERE id = ?", (traje_id,))
    row = cursor.fetchone()

    if row is None:
        conn.close()
        return jsonify({"error": "Traje no encontrado"}), 404

    traje = enriquecer_traje(cursor, row)
    conn.close()
    return jsonify(traje), 200


# ==============================================================================
# FASE 7: ENDPOINTS DEL SISTEMA DE COMENTARIOS Y PANEL DE MODERACIÓN
# ==============================================================================

@app.route("/api/comentarios/<int:traje_id>", methods=["GET"])
def get_comentarios_por_traje(traje_id):
    """Devuelve los comentarios de un traje específico ordenados por fecha descendente."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, traje_id, usuario, texto, fecha 
        FROM comentarios 
        WHERE traje_id = ? 
        ORDER BY fecha DESC, id DESC
    """, (traje_id,))
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows]), 200


@app.route("/api/comentarios", methods=["POST"])
def post_comentario():
    """Recibe JSON con traje_id, usuario y texto para insertar un nuevo comentario."""
    data = request.get_json(silent=True) or {}
    traje_id = data.get("traje_id")
    usuario = (data.get("usuario") or "").strip()
    texto = (data.get("texto") or "").strip()

    if not traje_id or not usuario or not texto:
        return jsonify({"error": "Los campos 'traje_id', 'usuario' y 'texto' son obligatorios."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO comentarios (traje_id, usuario, texto)
        VALUES (?, ?, ?)
    """, (traje_id, usuario, texto))
    nuevo_id = cursor.lastrowid
    conn.commit()

    cursor.execute("SELECT id, traje_id, usuario, texto, fecha FROM comentarios WHERE id = ?", (nuevo_id,))
    nuevo_comentario = dict(cursor.fetchone())
    conn.close()

    return jsonify({
        "mensaje": "Comentario registrado con éxito",
        "comentario": nuevo_comentario
    }), 201


@app.route("/api/comentarios/todos", methods=["GET"])
def get_todos_comentarios():
    """Devuelve todos los comentarios registrados en el sistema para el panel admin."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.traje_id, c.usuario, c.texto, c.fecha, t.comparsero, t.comparsa
        FROM comentarios c
        LEFT JOIN trajes t ON c.traje_id = t.id
        ORDER BY c.fecha DESC, c.id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows]), 200


@app.route("/api/comentarios/<int:id>", methods=["DELETE"])
def delete_comentario(id):
    """Elimina un comentario por su identificador único ID (protegido por sesión admin)."""
    if not session.get("admin_logged_in"):
        return jsonify({"error": "No autorizado. Sesión de administrador requerida."}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM comentarios WHERE id = ?", (id,))
    if cursor.fetchone() is None:
        conn.close()
        return jsonify({"error": "Comentario no encontrado"}), 404

    cursor.execute("DELETE FROM comentarios WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"mensaje": "Comentario eliminado con éxito", "id": id}), 200


# ==============================================================================
# RUTAS DE SERVICIO DE INTERFAZ WEB, VIDEOS Y ARCHIVOS ESTÁTICOS
# ==============================================================================

@app.route("/")
@app.route("/index.html")
def index():
    """
    Renderiza la página de inicio index.html mediante Jinja (render_template)
    para inyectar dinámicamente comparsas_unicas en el menú desplegable.
    """
    return render_template("index.html")


@app.route("/entrevistas")
@app.route("/entrevistas.html")
@app.route("/pages/entrevistas.html")
def ver_entrevistas():
    """Renderiza la página de entrevistas con soporte Jinja y reproductores <video controls width='100%'>."""
    return render_template("entrevistas.html")


@app.route("/materiales")
@app.route("/materiales.html")
@app.route("/pages/materiales.html")
def ver_materiales():
    """Renderiza el catálogo de materiales con menú dinámico de comparsas."""
    return render_template("materiales.html")


@app.route("/comparsas")
@app.route("/arandu-beleza.html")
@app.route("/pages/arandu-beleza.html")
def ver_catalogo_comparsas():
    """Renderiza el directorio interactivo de comparsas con menú dinámico de comparsas."""
    return render_template("arandu-beleza.html")


@app.route("/assets/videos/<path:filename>")
@app.route("/assets/video/<path:filename>")
@app.route("/static/assets/videos/<path:filename>")
@app.route("/static/assets/video/<path:filename>")
@app.route("/pages/assets/videos/<path:filename>")
@app.route("/pages/assets/video/<path:filename>")
def serve_videos(filename):
    """
    Expone los archivos de video en assets/videos/ y assets/video/ con soporte
    de HTTP Range requests (conditional=True) para reproducción HTML5 responsiva.
    """
    carpetas_video = [
        os.path.join(BASE_DIR, "assets", "videos"),
        os.path.join(BASE_DIR, "assets", "video"),
        os.path.join(STATIC_DIR, "assets", "videos"),
        os.path.join(STATIC_DIR, "assets", "video"),
    ]
    for folder in carpetas_video:
        candidate = os.path.join(folder, filename)
        if os.path.isfile(candidate):
            return send_from_directory(folder, filename, conditional=True)

    return jsonify({"error": f"Archivo de video '{filename}' no encontrado"}), 404


@app.route("/<path:path>")
def static_proxy(path):
    """
    Sirve archivos estáticos y páginas secundarias (/pages/*, /css/*, /js/*, /assets/*)
    permitiendo que todo el sitio web funcione de forma autónoma con Flask.
    """
    # Si se solicita una plantilla HTML disponible en templates/, renderizarla con Jinja
    basename = os.path.basename(path)
    if path.endswith(".html") and os.path.isfile(os.path.join(TEMPLATES_DIR, basename)):
        return render_template(basename)

    file_path = os.path.join(BASE_DIR, path)
    if os.path.isfile(file_path):
        return send_from_directory(BASE_DIR, path, conditional=True)

    static_file_path = os.path.join(STATIC_DIR, path)
    if os.path.isfile(static_file_path):
        return send_from_directory(STATIC_DIR, path, conditional=True)

    elif os.path.isdir(file_path) and os.path.isfile(os.path.join(file_path, "index.html")):
        return send_from_directory(file_path, "index.html")
    return jsonify({"error": "Recurso no encontrado"}), 404


if __name__ == "__main__":
    init_db()

    port = int(os.environ.get("PORT", 5000))
    print(f"\n=========================================================")
    print(f"  Servidor Hugo Fernández Arte Creativo encendido (FASE 14)")
    print(f"  - Web disponible en:  http://127.0.0.1:{port}")
    print(f"  - Feed Trajes:        http://127.0.0.1:{port}/trajes")
    print(f"  - Obras Maestras:     http://127.0.0.1:{port}/obras-maestras")
    print(f"  - Panel Admin CMS:    http://127.0.0.1:{port}/admin")
    print(f"=========================================================\n")

    app.run(host="0.0.0.0", port=port, debug=True)
