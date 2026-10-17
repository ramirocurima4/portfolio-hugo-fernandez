"""
Hugo Fernández Arte Creativo - Servidor Backend Flask
FASE 6: Servidor Web y API RESTful con SQLite para catálogo dinámico.
"""

import os
import shutil
import time
from werkzeug.utils import secure_filename
from flask import Flask, jsonify, request, send_from_directory, render_template, url_for
from database import get_db_connection, init_db

# FASE 8 & 10: Configuración de Flask para SSR y subida de archivos (CMS)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Flask(
    __name__,
    template_folder=TEMPLATES_DIR,
    static_folder=STATIC_DIR,
    static_url_path="/static"
)

# FASE 10: Configuración de carpeta de subida de imágenes (relativa a estructura estática)
app.config['UPLOAD_FOLDER'] = 'assets/img/'


# ==============================================================================
# FASE 8: SERVER-SIDE RENDERING (SSR) Y OPEN GRAPH PARA REDES SOCIALES
# ==============================================================================

@app.route("/traje/<int:id>")
def ver_traje_ssr(id):
    """
    Ruta con Server-Side Rendering (SSR) y etiquetas Open Graph.
    Permite generar Rich Previews al compartir en WhatsApp, Facebook o Twitter.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, comparsero, comparsa, genero, materiales, foto_url 
        FROM trajes 
        WHERE id = ?
    """, (id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return jsonify({"error": "Traje no encontrado"}), 404

    traje = dict(row)
    materiales_lista = [m.strip() for m in traje.get("materiales", "").rstrip(".").split(",") if m.strip()]

    return render_template("traje-detalle.html", traje=traje, materiales_lista=materiales_lista)


@app.route("/pages/traje-detalle.html")
def traje_detalle_legacy_proxy():
    """
    Mantiene compatibilidad con enlaces previos que consultan pages/traje-detalle.html?id=...
    sirviendo la versión SSR cuando se pasa un ID.
    """
    traje_id = request.args.get("id")
    if traje_id and traje_id.isdigit():
        return ver_traje_ssr(int(traje_id))
    
    file_path = os.path.join(BASE_DIR, "pages", "traje-detalle.html")
    if os.path.isfile(file_path):
        return send_from_directory(os.path.join(BASE_DIR, "pages"), "traje-detalle.html")
    return ver_traje_ssr(1)


# ==============================================================================
# RUTAS DE SERVICIO DE INTERFAZ WEB (FRONTEND ESTÁTICO)
# ==============================================================================

@app.route("/")
def index():
    """Sirve la página de inicio index.html."""
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/<path:path>")
def static_proxy(path):
    """
    Sirve archivos estáticos y páginas secundarias (/pages/*, /css/*, /js/*, /assets/*)
    permitiendo que todo el sitio web funcione de forma autónoma con Flask.
    """
    file_path = os.path.join(BASE_DIR, path)
    if os.path.isfile(file_path):
        return send_from_directory(BASE_DIR, path)

    static_file_path = os.path.join(STATIC_DIR, path)
    if os.path.isfile(static_file_path):
        return send_from_directory(STATIC_DIR, path)

    elif os.path.isdir(file_path) and os.path.isfile(os.path.join(file_path, "index.html")):
        return send_from_directory(file_path, "index.html")
    return jsonify({"error": "Recurso no encontrado"}), 404


# ==============================================================================
# ENDPOINTS DE API REST (CATÁLOGO DINÁMICO DE TRAJES)
# ==============================================================================

@app.route("/api/trajes", methods=["GET"])
def get_trajes():
    """
    Endpoint principal de API:
    Retorna la lista completa de trajes almacenados en carnaval.db en formato JSON.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, comparsero, comparsa, genero, materiales, foto_url FROM trajes ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()

    # Convertir sqlite3.Row a lista de diccionarios
    trajes = [dict(row) for row in rows]
    return jsonify(trajes), 200


@app.route("/api/trajes", methods=["POST"])
def post_traje():
    """
    Endpoint de creación de trajes (CMS Propio - FASE 10):
    Recibe multipart/form-data con imagen y campos de texto,
    guarda la imagen físicamente en UPLOAD_FOLDER y registra en SQLite.
    """
    if "foto" not in request.files:
        return jsonify({"error": "No se envió el archivo de imagen 'foto'"}), 400

    file = request.files["foto"]
    if file.filename == "":
        return jsonify({"error": "No se seleccionó ningún archivo de imagen"}), 400

    raw_filename = secure_filename(file.filename)
    if not raw_filename:
        raw_filename = f"traje_{int(time.time())}.jpg"

    # Evitar sobreescrituras accidentales
    base_name, ext = os.path.splitext(raw_filename)
    filename = raw_filename
    target_dir = os.path.join(BASE_DIR, "assets", "img")
    os.makedirs(target_dir, exist_ok=True)
    counter = 1
    while os.path.exists(os.path.join(target_dir, filename)):
        filename = f"{base_name}_{counter}{ext}"
        counter += 1

    # Guardar archivo físicamente en assets/img
    dest_path = os.path.join(target_dir, filename)
    file.save(dest_path)

    # Copiar a static/assets/img para asegurar disponibilidad en el static_folder de Flask
    static_img_dir = os.path.join(STATIC_DIR, "assets", "img")
    os.makedirs(static_img_dir, exist_ok=True)
    static_dest_path = os.path.join(static_img_dir, filename)
    shutil.copyfile(dest_path, static_dest_path)

    # Extraer campos de texto enviados en el formulario
    comparsero = (request.form.get("comparsero") or "").strip()
    comparsa = (request.form.get("comparsa") or "").strip()
    genero = (request.form.get("genero") or "Femenino").strip()
    materiales = (request.form.get("materiales") or "").strip()

    if not comparsero or not comparsa:
        return jsonify({"error": "Los campos 'comparsero' y 'comparsa' son obligatorios."}), 400

    # Guardar ruta relativa normalizada en la base de datos
    foto_url = f"assets/img/{filename}"

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO trajes (comparsero, comparsa, genero, materiales, foto_url)
        VALUES (?, ?, ?, ?, ?)
    """, (comparsero, comparsa, genero, materiales, foto_url))
    nuevo_id = cursor.lastrowid
    conn.commit()

    cursor.execute("SELECT id, comparsero, comparsa, genero, materiales, foto_url FROM trajes WHERE id = ?", (nuevo_id,))
    nuevo_traje = dict(cursor.fetchone())
    conn.close()

    return jsonify({
        "mensaje": "Traje registrado con éxito en el catálogo",
        "traje": nuevo_traje
    }), 201


@app.route("/api/trajes/filtrar", methods=["GET"])
def filtrar_trajes():
    """
    Endpoint de filtrado por Query String:
    Ejemplos de uso:
      - /api/trajes/filtrar?genero=Femenino
      - /api/trajes/filtrar?comparsa=Panambi
      - /api/trajes/filtrar?genero=Masculino&comparsa=Arandu
    """
    genero = request.args.get("genero", "").strip()
    comparsa = request.args.get("comparsa", "").strip()
    busqueda = request.args.get("q", "").strip()

    query = "SELECT id, comparsero, comparsa, genero, materiales, foto_url FROM trajes WHERE 1=1"
    params = []

    if genero:
        query += " AND LOWER(genero) = LOWER(?)"
        params.append(genero)

    if comparsa:
        query += " AND LOWER(comparsa) LIKE LOWER(?)"
        params.append(f"%{comparsa}%")

    if busqueda:
        query += " AND (LOWER(comparsero) LIKE LOWER(?) OR LOWER(materiales) LIKE LOWER(?))"
        params.extend([f"%{busqueda}%", f"%{busqueda}%"])

    query += " ORDER BY id ASC"

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    trajes_filtrados = [dict(row) for row in rows]
    return jsonify(trajes_filtrados), 200


@app.route("/api/trajes/<int:traje_id>", methods=["GET"])
def get_traje_por_id(traje_id):
    """
    Endpoint para consultar un traje individual por ID.
    Útil para hidratar dinámicamente la ficha técnica traje-detalle.html.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, comparsero, comparsa, genero, materiales, foto_url FROM trajes WHERE id = ?", (traje_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return jsonify({"error": "Traje no encontrado"}), 404

    return jsonify(dict(row)), 200


# ==============================================================================
# FASE 7: ENDPOINTS DEL SISTEMA DE COMENTARIOS Y PANEL DE MODERACIÓN
# ==============================================================================

@app.route("/admin")
def admin_panel():
    """
    Sirve el Dashboard de Gestión y Panel de Administración (CMS Propio - FASE 10):
    Permite cargar nuevos trajes con subida física de imágenes y moderar comentarios.
    """
    templates_admin = os.path.join(TEMPLATES_DIR, "admin.html")
    if os.path.isfile(templates_admin):
        return render_template("admin.html")
    pages_admin = os.path.join(BASE_DIR, "pages", "admin.html")
    if os.path.isfile(pages_admin):
        return send_from_directory(os.path.join(BASE_DIR, "pages"), "admin.html")
    return send_from_directory(BASE_DIR, "admin.html")


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
    """Elimina un comentario por su identificador único ID."""
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
# INSTRUCCIONES DE INTEGRACIÓN FRONTEND (JAVASCRIPT FETCH)
# ==============================================================================
"""
CÓMO CONSUMIR ESTA API DESDE JS EN EL FUTURO:
---------------------------------------------
Para reemplazar las tarjetas estáticas por datos dinámicos de la base de datos,
puedes usar este bloque en tu función de JavaScript (ej. en js/main.js):

async function cargarTrajesDesdeAPI() {
  const gridContainer = document.querySelector('.comparseros-grid');
  if (!gridContainer) return;

  try {
    const response = await fetch('/api/trajes');
    if (!response.ok) throw new Error('Error al conectar con la API');
    
    const trajes = await response.json();
    gridContainer.innerHTML = ''; // Limpiar tarjetas estáticas

    trajes.forEach(traje => {
      const card = document.createElement('article');
      card.className = 'comparsero-card reveal';
      card.setAttribute('data-category', traje.genero.toLowerCase());
      card.setAttribute('data-tags', `${traje.comparsero}, ${traje.comparsa}, ${traje.materiales}`);

      card.innerHTML = `
        <div class="comparsero-thumb">
          <span class="comparsero-badge">${traje.genero} • ${traje.comparsa}</span>
          <img src="${traje.foto_url}" alt="${traje.comparsero}" loading="lazy">
        </div>
        <div class="comparsero-body">
          <div>
            <h2 class="comparsero-title">${traje.comparsero}</h2>
            <p class="comparsero-subtitle">${traje.comparsa}</p>
          </div>
          <a href="traje-detalle.html?id=${traje.id}" class="btn-ver-ficha">
            Ver Ficha del Traje <span class="arrow-icon">→</span>
          </a>
        </div>
      `;
      gridContainer.appendChild(card);
    });

    // Re-ejecutar observers y listeners de filtro si es necesario
    if (typeof initGalleryFilterAndSearch === 'function') {
      initGalleryFilterAndSearch();
    }
  } catch (error) {
    console.error('Error cargando trajes:', error);
  }
}
"""

if __name__ == "__main__":
    # Asegurar que la base de datos exista al iniciar el servidor
    init_db()

    port = int(os.environ.get("PORT", 5000))
    print(f"\n=========================================================")
    print(f"  Servidor Hugo Fernández Arte Creativo encendido")
    print(f"  - Web disponible en:  http://127.0.0.1:{port}")
    print(f"  - API Todos:          http://127.0.0.1:{port}/api/trajes")
    print(f"  - API Filtro:         http://127.0.0.1:{port}/api/trajes/filtrar?genero=Femenino")
    print(f"=========================================================\n")

    app.run(host="0.0.0.0", port=port, debug=True)
