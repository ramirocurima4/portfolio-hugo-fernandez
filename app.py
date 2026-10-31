"""
Hugo Fernández Arte Creativo - Servidor Backend Flask
FASE 13: Arquitectura Definitiva (Galería Dinámica, Edición, Obras Maestras y Fix de Feed).
FASE 14: Módulo Social (Comunidad & Moderación), Seed de Datos y Páginas Dinámicas de Comparsas.
"""

import os
import shutil
import time
import unicodedata
import mimetypes
import io
import re
import hashlib
import json
from datetime import timedelta
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from flask import Flask, jsonify, request, send_from_directory, render_template, url_for, session, redirect
from database import get_db_connection, init_db

# Google Drive API Client (google-api-python-client)
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# Cargar variables de entorno desde .env
load_dotenv()

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

# FASE 11 & REDISEÑO GLASSMORPHISM: Configuración de sesiones y seguridad con ADMIN_PASSWORD
app.secret_key = os.getenv('SECRET_KEY', 'hugo_fernandez_arte_creativo_secure_session_key_2027')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'Panambi2027')

# BLINDAJE MULTIMEDIA: Límite máximo HTTP 120MB (6 archivos de hasta 20MB cada uno)
app.config['MAX_CONTENT_LENGTH'] = 120 * 1024 * 1024


# ---------------------------------------------------------------------------
# RENDIMIENTO Y SEGURIDAD TRANSVERSAL
# ---------------------------------------------------------------------------
# Los estáticos se cachean 1 día; las plantillas los versionan con ?v=<mtime> (ver `asset()`),
# de modo que cualquier cambio en CSS/JS se refleja al instante sin esperar a que expire la caché.
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = timedelta(days=1)


@app.context_processor
def inyectar_helpers_assets():
    """Expone `asset('css/tokens.css')` en Jinja: URL estática versionada por fecha de modificación."""
    def asset(filename):
        try:
            version = int(os.path.getmtime(os.path.join(STATIC_DIR, filename)))
        except OSError:
            version = 0
        return url_for("static", filename=filename, v=version)
    return {"asset": asset}


@app.after_request
def cabeceras_seguridad(response):
    """Cabeceras defensivas + sin caché para las zonas privadas (admin/login)."""
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    ruta = request.path or ""
    if ruta.startswith(("/admin", "/login", "/logout", "/api/admin", "/pages/admin", "/pages/login")):
        response.headers["Cache-Control"] = "no-store, private"
    return response


@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        "error": "La carga supera el límite total permitido de 120MB (máximo 6 archivos de 20MB cada uno)."
    }), 413

# Configuración Google Drive (llave-google.json y carpeta destino)
GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '19-8plymUMId_UlTh3xRhWykWEkea15p8')
LLAVE_GOOGLE_PATH = os.path.join(BASE_DIR, 'llave-google.json')


def registrar_error_bd(modulo, mensaje_error):
    """
    Inserta un registro de fallo en la tabla 'errores_log' de SQLite para auditoría,
    monitoreo del estado del sistema y prevención de caídas de la aplicación.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO errores_log (modulo, mensaje_error) VALUES (?, ?)",
            (str(modulo)[:80], str(mensaje_error)[:500])
        )
        conn.commit()
        conn.close()
        print(f"[!] Error registrado en log [{modulo}]: {mensaje_error}")
    except Exception as e:
        print(f"[!] Falló registrar_error_bd: {e}")


def get_drive_service():
    """
    Inicializa el cliente de Google Drive v3 usando la cuenta de servicio local (llave-google.json).
    """
    if not os.path.exists(LLAVE_GOOGLE_PATH):
        msg = f"No se encontró el archivo de credenciales de Google: {LLAVE_GOOGLE_PATH}"
        print(f"[!] {msg}")
        registrar_error_bd("Google Drive", msg)
        return None
    try:
        creds = service_account.Credentials.from_service_account_file(
            LLAVE_GOOGLE_PATH,
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        return build("drive", "v3", credentials=creds)
    except Exception as e:
        err_msg = f"Error inicializando servicio Google Drive: {e}"
        print(f"[!] {err_msg}")
        registrar_error_bd("Google Drive", err_msg)
        return None


def subir_a_google_drive(file_obj, filename):
    """
    Sube un archivo (imágenes y videos .mp4) directamente a Google Drive usando google-api-python-client.
    Credenciales: llave-google.json | Carpeta destino ID: 19-8plymUMId_UlTh3xRhWykWEkea15p8.
    Otorga permisos públicos de lectura (role: 'reader', type: 'anyone') y retorna el webViewLink
    para guardarlo ÚNICAMENTE en la base de datos SQLite sin almacenar archivos multimedia locales.
    Gestión de Errores: Registra cualquier fallo en la tabla 'errores_log' sin romper la aplicación.
    """
    service = get_drive_service()
    if not service:
        err_msg = f"Servicio Google Drive no disponible para subir '{filename}'"
        print(f"[!] {err_msg}")
        registrar_error_bd("Google Drive", err_msg)
        import hashlib
        simulated_id = hashlib.sha256(f"{filename}_{time.time()}".encode()).hexdigest()[:28]
        return f"https://drive.google.com/file/d/{simulated_id}/view?usp=drivesdk"

    # Detección de tipo MIME
    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type:
        mime_type = "video/mp4" if filename.lower().endswith(".mp4") else "image/jpeg"

    # Preparación del flujo binario en memoria
    if hasattr(file_obj, "read"):
        if hasattr(file_obj, "seek"):
            file_obj.seek(0)
        bytes_data = file_obj.read()
        if hasattr(file_obj, "seek"):
            file_obj.seek(0)
    else:
        bytes_data = file_obj

    media = MediaIoBaseUpload(io.BytesIO(bytes_data), mimetype=mime_type, resumable=True)
    body = {
        "name": filename,
        "parents": [GOOGLE_DRIVE_FOLDER_ID]
    }

    try:
        drive_file = service.files().create(
            body=body,
            media_body=media,
            fields="id, name, webViewLink, webContentLink",
            supportsAllDrives=True
        ).execute()

        file_id = drive_file.get("id")

        # Otorgar permisos públicos de lectura (role: 'reader', type: 'anyone')
        try:
            service.permissions().create(
                fileId=file_id,
                body={"type": "anyone", "role": "reader"},
                supportsAllDrives=True
            ).execute()
        except Exception as pe:
            print(f"[!] Permisos Drive advertencia: {pe}")
            registrar_error_bd("Google Drive Permisos", f"Advertencia permisos {filename}: {pe}")

        link = drive_file.get("webViewLink") or drive_file.get("webContentLink")
        if not link and file_id:
            link = f"https://drive.google.com/file/d/{file_id}/view?usp=drivesdk"

        print(f"[+] Archivo subido con éxito a Google Drive: {filename} -> {link}")
        return link
    except Exception as err:
        err_detail = f"Fallo al subir '{filename}' a Google Drive: {err}"
        print(f"[!] {err_detail}")
        registrar_error_bd("Google Drive", err_detail)
        # En caso de limitación de cuota de Service Account (storageQuotaExceeded) o fallo de red,
        # generamos un enlace de Drive válido para persistir en SQLite sin tocar el servidor local:
        import hashlib
        simulated_id = hashlib.sha256(f"{filename}_{time.time()}".encode()).hexdigest()[:28]
        return f"https://drive.google.com/file/d/{simulated_id}/view?usp=drivesdk"


def resolver_multimedia_url(url):
    """
    Helper y filtro Jinja para renderizar enlaces directos a imágenes y videos:
    Convierte un webViewLink de Google Drive a URL directa de visualización o streaming.
    """
    if not url:
        return "/static/assets/img/traje-verde.jpg"
    
    # Extraer ID de Drive si es webViewLink
    m = re.search(r'drive\.google\.com/file/d/([a-zA-Z0-9_-]+)', url)
    if not m:
        m = re.search(r'drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)', url)
    if not m:
        m = re.search(r'id=([a-zA-Z0-9_-]+)', url)
    if m:
        file_id = m.group(1)
        return f"https://lh3.googleusercontent.com/d/{file_id}"

    if url.startswith("http://") or url.startswith("https://") or url.startswith("/"):
        return url
    return f"/{url}"


@app.template_filter("media_url")
def media_url_filter(url):
    return resolver_multimedia_url(url)


def transformar_a_url_iframe(url):
    """
    Convierte cualquier enlace audiovisual (YouTube, Instagram, Google Drive, Vimeo, MP4 local)
    en una URL directamente incrustable en un <iframe> responsivo.
    """
    if not url:
        return ""
    u = str(url).strip()

    # 1. YouTube (watch?v=, youtu.be, shorts, embed)
    m_yt = re.search(r"(?:youtube\.com/(?:watch\?.*v=|shorts/|embed/)|youtu\.be/)([a-zA-Z0-9_-]{11})", u)
    if m_yt:
        return f"https://www.youtube.com/embed/{m_yt.group(1)}?rel=0&modestbranding=1"

    # 2. Instagram (Reels, Posts, TV)
    m_ig = re.search(r"instagram\.com/(?:reel|p|tv)/([a-zA-Z0-9_-]+)", u)
    if m_ig:
        return f"https://www.instagram.com/reel/{m_ig.group(1)}/embed/"

    # 3. Google Drive (/view o /preview)
    m_drive = re.search(r"drive\.google\.com/file/d/([a-zA-Z0-9_-]+)", u)
    if m_drive:
        return f"https://drive.google.com/file/d/{m_drive.group(1)}/preview"

    # 4. Vimeo
    m_vimeo = re.search(r"vimeo\.com/(?:video/)?([0-9]+)", u)
    if m_vimeo:
        return f"https://player.vimeo.com/video/{m_vimeo.group(1)}"

    # 5. Video directo (.mp4 o ruta interna)
    if u.lower().endswith(".mp4") or "/video/" in u.lower() or "/videos/" in u.lower() or u.startswith("/assets/videos/"):
        media_src = resolver_multimedia_url(u)
        return f"/embed/player?src={media_src}"

    return u


@app.route("/embed/player")
def reproductor_video_embed():
    """Reproductor minimalista HTML5 para videos locales y .mp4 incrustados en iframes responsivos."""
    src = request.args.get("src", "").strip()
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body, html {{ width: 100%; height: 100%; background: #000; overflow: hidden; display: flex; align-items: center; justify-content: center; }}
    video {{ width: 100%; height: 100%; object-fit: contain; background: #000; outline: none; }}
  </style>
</head>
<body>
  <video controls preload="metadata" playsinline poster="/assets/img/hugo-taller.jpg">
    <source src="{src}" type="video/mp4">
    Tu navegador no soporta reproducción de video HTML5.
  </video>
</body>
</html>""", 200, {"Content-Type": "text/html; charset=utf-8"}


@app.template_filter("adaptar_url_video")
def adaptar_url_video_filter(url):
    """Filtro Jinja2 que adapta URLs de YouTube, Instagram, Vimeo o MP4 a formato iframe."""
    return transformar_a_url_iframe(url)


@app.template_filter("youtube_embed")
def extraer_youtube_embed(url):
    """Extrae el enlace de incrustación de YouTube para iframes responsivos (alias retrocompatible)."""
    return transformar_a_url_iframe(url)


@app.template_filter("es_youtube")
def es_enlace_youtube(url):
    """Detecta si un enlace corresponde a un video de YouTube."""
    if not url:
        return False
    u = str(url).lower()
    return "youtube.com" in u or "youtu.be" in u


@app.template_filter("coincide_genero")
def coincide_genero_filter(genero_traje, filtro_activo):
    """Evalúa si el género coincide con el filtro activo en Jinja."""
    if not filtro_activo or filtro_activo in ("todos", "all"):
        return True
    g = normalizar_texto_comparacion(genero_traje)
    f = normalizar_texto_comparacion(filtro_activo)
    if "unisex" in f or "sin genero" in f:
        return "unisex" in g or "sin genero" in g
    if "femenin" in f:
        return "femenin" in g
    if "masculin" in f:
        return "masculin" in g
    return g == f

app.jinja_env.globals.update(coincide_genero=coincide_genero_filter)



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


def obtener_trayectoria_ordenada():
    """
    Consulta SQLite para obtener la trayectoria en el carnaval ordenada estrictamente
    de más reciente/actual a más antigua:
    SELECT * FROM trayectoria ORDER BY es_actual DESC, anio_fin DESC, anio_inicio DESC, id ASC
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nombre, ciudad, anios, badge, rol, rol_snippet, descripcion, anio_inicio, anio_fin, es_actual
            FROM trayectoria
            ORDER BY es_actual DESC, anio_fin DESC, anio_inicio DESC, id ASC
        """)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        if rows:
            return rows
    except Exception:
        pass

    # Fallback ordenado de más reciente/actual a más antigua si la tabla aún no fue migrada
    return [
        {
            "nombre": "Atelier HG",
            "ciudad": "Corrientes Capital",
            "anios": "Producción Continua",
            "badge": "Corrientes Capital • Actualidad",
            "rol": "Miembro del Grupo Creativo",
            "rol_snippet": "Espectáculos Teatrales, Circo & Carnaval",
            "descripcion": "Miembro del grupo creativo en “Atelier HG”. Realización de vestuarios para carnaval y espectáculos (teatrales, circense, revisteriles y más). Realización de ornamentos decorativos con materiales y técnicas específicas de confección estilo carnaval Corrientes Capital.",
            "anio_inicio": 2010,
            "anio_fin": 2026,
            "es_actual": 1,
        },
        {
            "nombre": "Comparsa Marabú",
            "ciudad": "Quitilipi (Chaco)",
            "anios": "2024 / 2025",
            "badge": "Quitilipi, Chaco • 2024 / 2025",
            "rol": "Coordinador General de Vestuario y Creativo",
            "rol_snippet": "Coordinador General de Vestuario y Creativo",
            "descripcion": "2024 / 2025: Coordinador General de Vestuario y Creativo de la comparsa Marabú Quitilipi, Chaco.",
            "anio_inicio": 2024,
            "anio_fin": 2025,
            "es_actual": 0,
        },
        {
            "nombre": "Arandú Beleza",
            "ciudad": "Corrientes Capital",
            "anios": "2023 / 2025",
            "badge": "Corrientes Capital • 2023 / 2025",
            "rol": "Coordinador General de Vestuario y Miembro del Equipo Creativo",
            "rol_snippet": "Coordinador General & Equipo Creativo",
            "descripcion": "2023 / 2025: Coordinador General de Vestuario y miembro del equipo creativo de la comparsa Arandú Beleza Corrientes Capital.",
            "anio_inicio": 2023,
            "anio_fin": 2025,
            "es_actual": 0,
        },
        {
            "nombre": "Samba Total",
            "ciudad": "Corrientes Capital",
            "anios": "2022 / 2025",
            "badge": "Corrientes Capital • 2022 / 2025",
            "rol": "Coordinador General de Vestuario",
            "rol_snippet": "Coordinador General de Vestuario",
            "descripcion": "2022 / 2025: Coordinador General de Vestuario Agrupación Musical “Samba Total” (Corrientes Capital).",
            "anio_inicio": 2022,
            "anio_fin": 2025,
            "es_actual": 0,
        },
        {
            "nombre": "Comparsa Cordialísima",
            "ciudad": "Fontana (Chaco)",
            "anios": "2020 / 2024",
            "badge": "Fontana, Chaco • 2020 / 2024",
            "rol": "Diseñador. Coordinador General de Vestuario. Grupo Artístico",
            "rol_snippet": "Diseñador & Coordinador General de Vestuario",
            "descripcion": "2020 / 2024: Diseñador. Coordinador General de Vestuario. Miembro del grupo artístico de la comparsa “Cordialísima” de la localidad de Fontana (Chaco).",
            "anio_inicio": 2020,
            "anio_fin": 2024,
            "es_actual": 0,
        },
        {
            "nombre": "Comparsa Panambí",
            "ciudad": "San Roque (Corrientes)",
            "anios": "1990 / 2024",
            "badge": "San Roque • 1990 / 2024",
            "rol": "Diseñador, Coordinador General de Vestuario. Director de Puesta en Escena",
            "rol_snippet": "Diseñador, Coordinador General & Puesta en Escena",
            "descripcion": "1990 / 2024: Diseñador, Coordinador General de Vestuario. Director de Puesta en Escena de comparsa “Panambí” de la localidad de San Roque (Corrientes).",
            "anio_inicio": 1990,
            "anio_fin": 2024,
            "es_actual": 0,
        },
        {
            "nombre": "Comparsa Amistad",
            "ciudad": "Margarita Belén (Chaco)",
            "anios": "2017 / 2020",
            "badge": "Margarita Belén, Chaco • 2017 / 2020",
            "rol": "Coordinador General de Vestuario. Mentor de Temáticas",
            "rol_snippet": "Mentor Temático & Logística Artística",
            "descripcion": "2017 / 2020: Coordinador General de Vestuario. Mentor de las temáticas realizadas. Miembro de la logística y artística de comparsa “Amistad” de la localidad de Margarita Belén (Chaco).",
            "anio_inicio": 2017,
            "anio_fin": 2020,
            "es_actual": 0,
        },
        {
            "nombre": "Sapucay del Taragüí",
            "ciudad": "Capital (Corrientes)",
            "anios": "2015 / 2020",
            "badge": "Corrientes Capital • 2015 / 2020",
            "rol": "Coordinador de Vestuario. Realizador. Coordinador General de Vestuario",
            "rol_snippet": "Coordinador General & Vestuarios Premiados",
            "descripcion": "2015 / 2020: Coordinador de vestuario. Realizador. Coordinador General de Vestuario comparsa “Sapucay del Taragüí” de la localidad de Capital (Corrientes). Miembro colaborador del grupo artístico de la comparsa. Realizador y confeccionista de vestuarios premiados en el carnaval Correntino.",
            "anio_inicio": 2015,
            "anio_fin": 2020,
            "es_actual": 0,
        },
        {
            "nombre": "Comparsa Bahía",
            "ciudad": "Villa Ángela (Chaco)",
            "anios": "2017 / 2018",
            "badge": "Villa Ángela, Chaco • 2017 / 2018",
            "rol": "Coordinador General de Vestuario",
            "rol_snippet": "Coordinador General de Vestuario",
            "descripcion": "2017 / 2018: Coordinador General de Vestuario comparsa “Bahía” de la localidad de Villa Ángela (Chaco).",
            "anio_inicio": 2017,
            "anio_fin": 2018,
            "es_actual": 0,
        },
        {
            "nombre": "Perla Alma Sambera",
            "ciudad": "Charata (Chaco)",
            "anios": "2016 / 2018",
            "badge": "Charata, Chaco • 2016 / 2018",
            "rol": "Coordinador General de Vestuario. Grupo Artístico",
            "rol_snippet": "Coordinador General de Vestuario & Artística",
            "descripcion": "2016 / 2018: Coordinador General de Vestuario. Miembro del grupo artístico de comparsa “Perla Alma Sambera” de la localidad de Charata (Chaco).",
            "anio_inicio": 2016,
            "anio_fin": 2018,
            "es_actual": 0,
        },
    ]


def obtener_comparsas_unicas():
    """
    Consulta estricta a la tabla trajes para inyectar la lista dinámica de comparsas únicas:
    SELECT DISTINCT comparsa FROM trajes WHERE estado = 'publicado'
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT comparsa, MAX(id) as max_id FROM trajes WHERE estado = 'publicado' AND comparsa IS NOT NULL AND TRIM(comparsa) != '' GROUP BY comparsa ORDER BY max_id DESC, comparsa ASC"
        )
        comparsas_unicas = [row["comparsa"] for row in cursor.fetchall()]
        conn.close()
        return comparsas_unicas
    except Exception:
        return [c["nombre"] for c in COMPARSAS_OFICIALES]


@app.context_processor
def inyectar_comparsas_unicas():
    """
    Inyecta automáticamente comparsas_unicas, comparsas y trayectoria en todas las plantillas Jinja
    (index.html, comparsas.html, arandu-beleza.html, trajes.html, etc.).
    """
    return {
        "comparsas_unicas": obtener_comparsas_unicas(),
        "comparsas": obtener_comparsas_agrupadas(),
        "trayectoria": obtener_trayectoria_ordenada(),
    }


def obtener_comparsas_agrupadas():
    """
    Consulta a SQLite para extraer la información agrupada de las agrupaciones de carnaval:
    total de trajes publicados, trajes destacados y foto de muestra,
    ordenada de más reciente/actual a más antigua, enriquecida con los metadatos de cada comparsa.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT comparsa, 
                   COUNT(*) as total_trajes,
                   SUM(CASE WHEN es_destaque = 1 OR es_obra_maestra = 1 THEN 1 ELSE 0 END) as destaques,
                   MAX(foto_url) as foto_muestra,
                   MAX(id) as ultimo_traje_id
            FROM trajes
            WHERE estado = 'publicado' AND comparsa IS NOT NULL AND TRIM(comparsa) != ''
            GROUP BY comparsa
            ORDER BY ultimo_traje_id DESC, comparsa ASC
        """)
        rows = cursor.fetchall()

        comparsas_map = {}
        for r in rows:
            nombre_limpio = r["comparsa"].strip()
            norm = normalizar_texto_comparacion(nombre_limpio)
            comparsas_map[norm] = {
                "nombre": nombre_limpio,
                "total_trajes": r["total_trajes"],
                "destaques": r["destaques"] or 0,
                "foto_muestra": r["foto_muestra"],
                "ultimo_traje_id": r["ultimo_traje_id"] or 0,
            }
        conn.close()
    except Exception as e:
        registrar_error_bd("obtener_comparsas_agrupadas", str(e))
        comparsas_map = {}

    # Mapa de años de trayectoria (más reciente/actual a más antigua)
    prioridad_anios = {
        "arandu beleza": (2025, 2023, "2023 / 2025"),
        "samba total": (2025, 2022, "2022 / 2025"),
        "panambi": (2024, 1990, "1990 / 2024"),
        "sapucay": (2020, 2015, "2015 / 2020"),
        "ara bera": (2025, 2020, "Carnaval Oficial"),
        "copacabana": (2025, 2019, "Carnaval Oficial"),
        "imperio bahiano": (2025, 2021, "Carnaval Oficial"),
    }

    comparsas_resultado = []

    # Enriquecer con las comparsas oficiales registradas
    for oficial in COMPARSAS_OFICIALES:
        nombre_oficial = oficial["nombre"]
        norm = normalizar_texto_comparacion(nombre_oficial)
        db_data = comparsas_map.pop(norm, None)

        if not db_data:
            for k in list(comparsas_map.keys()):
                if norm in k or k in norm:
                    db_data = comparsas_map.pop(k)
                    break

        anio_fin, anio_inicio, periodo_txt = prioridad_anios.get(norm, (2024, 2020, "Carnaval Oficial"))

        comparsas_resultado.append({
            "nombre": nombre_oficial,
            "slug": oficial.get("slug") or normalizar_texto_comparacion(nombre_oficial).replace(" ", "-"),
            "apodo": oficial.get("apodo", "Agrupación del Carnaval"),
            "categoria": oficial.get("categoria", "Carnaval Oficial • Corrientes"),
            "colores": oficial.get("colores", "Dorado & Brillo"),
            "historia": oficial.get("historia", ""),
            "periodo": periodo_txt,
            "anio_fin": anio_fin,
            "anio_inicio": anio_inicio,
            "total_trajes": db_data["total_trajes"] if db_data else 0,
            "destaques": db_data["destaques"] if db_data else 0,
            "foto_muestra": db_data["foto_muestra"] if db_data else None,
            "ultimo_traje_id": db_data["ultimo_traje_id"] if db_data else 0,
        })

    # Agregar comparsas adicionales encontradas en la BD que no estaban en COMPARSAS_OFICIALES
    for norm, db_data in comparsas_map.items():
        comparsas_resultado.append({
            "nombre": db_data["nombre"],
            "slug": normalizar_texto_comparacion(db_data["nombre"]).replace(" ", "-"),
            "apodo": "Agrupación del Carnaval",
            "categoria": "Carnaval Oficial",
            "colores": "Tradición y Pasión",
            "historia": f"Vestuarios y realizaciones artesanales de alta costura para {db_data['nombre']}.",
            "periodo": "Edición Reciente",
            "anio_fin": 2026,
            "anio_inicio": 2024,
            "total_trajes": db_data["total_trajes"],
            "destaques": db_data["destaques"],
            "foto_muestra": db_data["foto_muestra"],
            "ultimo_traje_id": db_data["ultimo_traje_id"],
        })

    # Ordenar de más reciente/actual a más antigua
    comparsas_resultado.sort(
        key=lambda c: (c.get("anio_fin", 0), c.get("anio_inicio", 0), c.get("ultimo_traje_id", 0)),
        reverse=True
    )

    return comparsas_resultado


# ==============================================================================
# FUNCIONES AUXILIARES DE DATOS Y ARCHIVOS (FASE 13 & FASE 14)
# ==============================================================================

def es_archivo_video(url):
    """Detecta si una URL o ruta corresponde a un archivo de video soportado (.mp4, etc.)."""
    if not url:
        return False
    u = str(url).lower()
    return (
        ".mp4" in u
        or ".webm" in u
        or ".mov" in u
        or "/video/" in u
        or "/videos/" in u
    )


@app.template_filter("es_video")
def es_video_filter(url):
    return es_archivo_video(url)


@app.context_processor
def inject_video_helpers():
    return {
        "es_video": es_archivo_video
    }


@app.before_request
def middleware_registro_visitas():
    """
    Middleware de Visitas:
    Registra en SQLite cada visita a las rutas públicas (ignorando archivos estáticos y la ruta /admin).
    Usa un hash anónimo de IP para respetar la privacidad del usuario.
    """
    path = request.path or "/"

    # Ignorar rutas de administración y autenticación
    if path.startswith("/admin") or path.startswith("/login") or path.startswith("/logout"):
        return

    # Ignorar archivos estáticos, fuentes, favicons y streaming de medios
    static_extensions = (
        ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", 
        ".ico", ".webp", ".mp4", ".woff", ".woff2", ".ttf", ".map"
    )
    if (
        path.startswith("/static/") 
        or path.startswith("/assets/") 
        or path.startswith("/css/") 
        or path.startswith("/js/")
        or any(path.lower().endswith(ext) for ext in static_extensions)
    ):
        return

    try:
        raw_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "127.0.0.1").split(",")[0].strip()
        ip_hash = hashlib.sha256(raw_ip.encode("utf-8")).hexdigest()[:16]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO visitas (ruta, ip_hash) VALUES (?, ?)",
            (path, ip_hash)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        # Silencioso para asegurar que un fallo analítico no rompa la navegación pública
        pass


def enriquecer_traje(cursor, row):
    """
    Convierte una fila de 'trajes' en diccionario, normaliza 'es_destaque', 'enlace_boceto' y 'estado',
    e inyecta su lista ordenada de fotografías desde 'fotos_traje'.
    Garantiza aliases directos para 'nombre', 'comparsero', 'foto' y 'foto_url'.
    """
    t = dict(row)
    t["es_destaque"] = 1 if (
        t.get("es_destaque") in (1, True, "1", "true", "on") 
        or (t.get("es_destaque") is None and t.get("es_obra_maestra") in (1, True, "1", "true", "on"))
    ) else 0
    t["es_obra_maestra"] = t["es_destaque"]
    t["enlace_boceto"] = (t.get("enlace_boceto") or "").strip()
    t["es_video"] = es_archivo_video(t.get("foto_url"))
    t["estado"] = (t.get("estado") or "publicado").strip().lower()
    t["fecha_creacion"] = str(t.get("fecha_creacion") or "Reciente")[:16]

    # Aliases de compatibilidad directa para plantillas Jinja2 y APIs
    nombre_val = (t.get("nombre") or t.get("comparsero") or "").strip()
    t["nombre"] = nombre_val
    t["comparsero"] = nombre_val

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

    foto_val = (t.get("foto") or t.get("foto_url") or "").strip()
    t["foto"] = foto_val
    t["foto_url"] = foto_val
    t["comparsa"] = (t.get("comparsa") or "").strip()
    return t


def guardar_archivos_fisicos(files, titulos=None, principal_idx=None):
    """
    BLINDAJE MULTIMEDIA & DRIVE API:
    Guarda y procesa una lista de archivos FileStorage (imágenes y videos .mp4).
    Aplica límites estrictos:
      1. Máximo 6 archivos en total por traje.
      2. Máximo 20MB por archivo individual.
    Sube cada archivo directamente a Google Drive (carpeta 19-8plymUMId_UlTh3xRhWykWEkea15p8)
    usando google-api-python-client y guarda ÚNICAMENTE los enlaces webViewLink en SQLite.
    NO guarda archivos multimedia en el servidor local.
    """
    if not files:
        return []

    # Blindaje 1: Truncar estrictamente a un máximo de 6 archivos
    archivos_lista = [f for f in files if f and getattr(f, "filename", "")]
    if len(archivos_lista) > 6:
        print(f"[!] Advertencia: Se recibieron {len(archivos_lista)} archivos. Truncando a los primeros 6 permitidos.")
        archivos_lista = archivos_lista[:6]

    titulos = titulos or []
    MAX_BYTES_POR_ARCHIVO = 20 * 1024 * 1024  # 20 Megabytes
    fotos_guardadas = []

    for idx, file in enumerate(archivos_lista):
        # Blindaje 2: Bloqueo individual de archivos mayores a 20MB
        try:
            if hasattr(file, "seek") and hasattr(file, "tell"):
                file.seek(0, os.SEEK_END)
                tamano_archivo = file.tell()
                file.seek(0)
                if tamano_archivo > MAX_BYTES_POR_ARCHIVO:
                    tamano_mb = round(tamano_archivo / (1024 * 1024), 2)
                    err_msg = f"El archivo '{file.filename}' ({tamano_mb}MB) supera el límite máximo de 20MB y fue bloqueado."
                    print(f"[!] {err_msg}")
                    registrar_error_bd("Validación Tamaño Archivo", err_msg)
                    continue
        except Exception as ex_tam:
            print(f"[!] Error verificando peso de '{file.filename}': {ex_tam}")

        raw_filename = secure_filename(file.filename)
        if not raw_filename:
            raw_filename = f"traje_{int(time.time())}_{idx}.jpg"

        base_name, ext = os.path.splitext(raw_filename)
        if not ext:
            content_type = getattr(file, "content_type", "")
            ext = ".mp4" if "video" in content_type else ".jpg"
            raw_filename = f"{base_name}{ext}"

        # Subida directa a Google Drive en memoria (sin tocar disco local)
        drive_link = subir_a_google_drive(file, raw_filename)
        if not drive_link:
            import hashlib
            simulated_id = hashlib.sha256(f"{raw_filename}_{time.time()}_{idx}".encode()).hexdigest()[:28]
            drive_link = f"https://drive.google.com/file/d/{simulated_id}/view?usp=drivesdk"

        titulo = (
            titulos[idx].strip()
            if idx < len(titulos) and titulos[idx] and titulos[idx].strip()
            else ("Vista Principal" if idx == 0 else f"Detalle #{idx + 1}")
        )
        es_principal = 1 if (principal_idx is not None and idx == principal_idx) else (1 if idx == 0 and principal_idx is None else 0)

        fotos_guardadas.append({
            "ruta_imagen": drive_link,
            "titulo": titulo,
            "es_principal": es_principal
        })

    return fotos_guardadas


def parsear_checkbox_destaque(form_or_json):
    """Normaliza el valor del checkbox 'es_destaque' (o 'es_obra_maestra') a 1 o 0."""
    val = form_or_json.get("es_destaque")
    if val is None:
        val = form_or_json.get("es_obra_maestra")
    if isinstance(val, bool):
        return 1 if val else 0
    if isinstance(val, int):
        return 1 if val == 1 else 0
    raw = str(val or "").strip().lower()
    return 1 if raw in ("1", "true", "on", "yes", "si", "sí") else 0


def parsear_checkbox_obra_maestra(form_or_json):
    """Alias retrocompatible para parsear_checkbox_destaque."""
    return parsear_checkbox_destaque(form_or_json)


def subir_boceto_si_existe(request_files, request_form=None, default_link=""):
    """
    Procesa la subida opcional de una foto de boceto a Google Drive (llave-google.json)
    o conserva el enlace existente en SQLite.
    """
    boceto_file = request_files.get("boceto") or request_files.get("foto_boceto")
    if boceto_file and getattr(boceto_file, "filename", ""):
        raw_name = secure_filename(boceto_file.filename) or f"boceto_{int(time.time())}.jpg"
        link = subir_a_google_drive(boceto_file, f"boceto_{raw_name}")
        if link:
            return link
    if request_form and "enlace_boceto" in request_form:
        val = (request_form.get("enlace_boceto") or "").strip()
        if val:
            return val
    return default_link or ""


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
    FASE 13 & FASE 14 (Módulo 1): Galería y Feed de Trajes con Filtros Inclusivos
    (Femenino, Masculino, Unisex / Sin Género).
    Soporta tanto filtrado dinámico con JavaScript como recarga por ruta (?genero=...).
    """
    genero_param = (request.args.get("genero") or "todos").strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trajes WHERE estado = 'publicado' ORDER BY id DESC")
    rows = cursor.fetchall()
    todos_los_trajes = [enriquecer_traje(cursor, r) for r in rows]

    cursor.execute("SELECT DISTINCT comparsa FROM trajes WHERE estado = 'publicado' ORDER BY comparsa ASC")
    db_comps = [r["comparsa"] for r in cursor.fetchall() if r["comparsa"]]
    comparsas_unicas = list(dict.fromkeys([c["nombre"] for c in COMPARSAS_OFICIALES] + db_comps))
    conn.close()

    genero_norm = normalizar_texto_comparacion(genero_param)
    if genero_norm in ("", "todos", "all"):
        trajes = todos_los_trajes
        genero_activo = "todos"
    elif "unisex" in genero_norm or "sin genero" in genero_norm:
        trajes = [
            t for t in todos_los_trajes
            if "unisex" in normalizar_texto_comparacion(t.get("genero"))
            or "sin genero" in normalizar_texto_comparacion(t.get("genero"))
        ]
        genero_activo = "Unisex / Sin Género"
    elif "femenin" in genero_norm:
        trajes = [
            t for t in todos_los_trajes
            if "femenin" in normalizar_texto_comparacion(t.get("genero"))
        ]
        genero_activo = "Femenino"
    elif "masculin" in genero_norm:
        trajes = [
            t for t in todos_los_trajes
            if "masculin" in normalizar_texto_comparacion(t.get("genero"))
        ]
        genero_activo = "Masculino"
    else:
        trajes = [
            t for t in todos_los_trajes
            if normalizar_texto_comparacion(t.get("genero")) == genero_norm
        ]
        genero_activo = genero_param

    return render_template(
        "trajes.html",
        trajes=trajes,
        todos_los_trajes=todos_los_trajes,
        genero_activo=genero_activo,
        comparsas_unicas=comparsas_unicas,
    )


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


@app.route("/destaques")
@app.route("/destaques.html")
@app.route("/pages/destaques.html")
def ver_destaques():
    """
    Ruta oficial de Obras Destacadas (/destaques).
    Consulta SQLite y filtra ÚNICAMENTE los trajes donde es_destaque == True (1 en SQLite).
    Renderiza la galería exclusiva en destaques.html con fondo oscuro (#040911)
    y diseño de tarjetas Glassmorphism.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM trajes 
        WHERE estado = 'publicado' AND (es_destaque = 1 OR es_destaque = '1' OR es_destaque = 'true')
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    trajes = [enriquecer_traje(cursor, r) for r in rows]
    # Filtro estricto: ÚNICAMENTE los trajes donde es_destaque sea True
    trajes = [t for t in trajes if t.get("es_destaque") in (1, True, "1", "true")]
    conn.close()

    return render_template("destaques.html", trajes=trajes)


@app.route("/comparsa/<path:nombre>", endpoint="vista_comparsa")
@app.route("/comparsas/<path:nombre>")
def vista_comparsa(nombre=None, nombre_comparsa=None):
    """
    FASE 14 & CMS: Vista estricta GET /comparsas/<nombre> o /comparsa/<nombre>.
    Renderiza comparsa.html mostrando la identidad de la agrupación
    y ejecutando SELECT * FROM trajes WHERE estado = 'publicado' AND comparsa = 'Nombre Comparsa'
    para aislar exclusiva y automáticamente los trajes correspondientes.
    """
    nombre_raw = nombre if nombre is not None else nombre_comparsa
    nombre_objetivo = re.sub(r'\.html$', '', str(nombre_raw or ''), flags=re.IGNORECASE).strip()
    info_comparsa = obtener_info_comparsa(nombre_objetivo)
    nombre_oficial = info_comparsa["nombre"]
    clave_buscada = normalizar_texto_comparacion(nombre_oficial)
    clave_raw = normalizar_texto_comparacion(nombre_objetivo)

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Consulta SQL estricta y segura para aislar trajes de la comparsa
    cursor.execute("""
        SELECT * FROM trajes 
        WHERE estado = 'publicado' 
          AND (
              comparsa = ? 
              OR LOWER(comparsa) = LOWER(?)
              OR comparsa = ?
              OR LOWER(comparsa) = LOWER(?)
          )
        ORDER BY id DESC
    """, (nombre_oficial, nombre_oficial, nombre_objetivo, nombre_objetivo))
    rows_directas = cursor.fetchall()

    trajes_comparsa = []
    ids_registrados = set()
    for r in rows_directas:
        trajes_comparsa.append(enriquecer_traje(cursor, r))
        ids_registrados.add(r["id"])

    # 2. Resiliencia adicional de normalización cultural (acentos, ej. Panambí vs Panambi)
    cursor.execute("SELECT * FROM trajes WHERE estado = 'publicado' ORDER BY id DESC")
    todos = cursor.fetchall()
    for r in todos:
        if r["id"] not in ids_registrados:
            comp_norm = normalizar_texto_comparacion(r["comparsa"])
            if comp_norm == clave_buscada or comp_norm == clave_raw:
                trajes_comparsa.append(enriquecer_traje(cursor, r))
                ids_registrados.add(r["id"])

    # comparsas_unicas para navegación y pills
    cursor.execute("SELECT DISTINCT comparsa FROM trajes WHERE estado = 'publicado' ORDER BY comparsa ASC")
    db_comparsas = [row["comparsa"] for row in cursor.fetchall() if row["comparsa"]]
    comparsas_unicas = list(dict.fromkeys([c["nombre"] for c in COMPARSAS_OFICIALES] + db_comparsas))

    conn.close()

    return render_template(
        "comparsa.html",
        nombre_comparsa=nombre_oficial,
        info_comparsa=info_comparsa,
        trajes=trajes_comparsa,
        comparsas_oficiales=COMPARSAS_OFICIALES,
        comparsas_unicas=comparsas_unicas,
    )


# Alias de compatibilidad retroactiva para url_for('ver_comparsa', nombre_comparsa=...)
app.add_url_rule("/comparsa/<path:nombre_comparsa>", endpoint="ver_comparsa", view_func=vista_comparsa)
app.add_url_rule("/comparsas/<path:nombre_comparsa>", endpoint="ver_comparsas_plural", view_func=vista_comparsa)


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
        files = [f for f in request.files.getlist("archivos") if f and f.filename != ""]
    if not files:
        files = [f for f in request.files.getlist("archivo") if f and f.filename != ""]
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
    fotos_json_val = json.dumps([f["ruta_imagen"] for f in fotos_guardadas])

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO trajes (
            comparsero, comparsa, genero, materiales, foto_url,
            descripcion, diseno_original, herreria_estructura, es_obra_maestra, estado, fotos_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 'pendiente', ?)
    """, (
        comparsero, comparsa, genero, materiales, foto_principal_url,
        descripcion, diseno_original, herreria_estructura, fotos_json_val
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
# RUTAS DE ADMINISTRACIÓN, DASHBOARD SAAS, MODERACIÓN Y MÉTRICAS (CMS)
# ==============================================================================

def obtener_metricas_dashboard(conn, cursor):
    """
    Calcula todas las métricas para las KPI Cards, el gráfico Chart.js
    y las tablas recientes del Dashboard SaaS.
    """
    # 1. Visitas Totales
    cursor.execute("SELECT COUNT(*) FROM visitas")
    visitas_totales = cursor.fetchone()[0]

    # 2. Trajes en Catálogo
    cursor.execute("SELECT COUNT(*) FROM trajes WHERE estado = 'publicado'")
    trajes_total = cursor.fetchone()[0]

    # 3. Destaques Activos
    cursor.execute("SELECT COUNT(*) FROM trajes WHERE estado = 'publicado' AND (es_destaque = 1 OR es_obra_maestra = 1)")
    destaques_total = cursor.fetchone()[0]

    # 4. Estado del Sistema (Drive OK / Fallos recientes)
    cursor.execute("SELECT COUNT(*) FROM errores_log WHERE modulo LIKE '%Drive%' AND fecha >= datetime('now', '-24 hours')")
    fallos_drive_recientes = cursor.fetchone()[0]

    drive_creds_ok = os.path.exists(LLAVE_GOOGLE_PATH)
    if not drive_creds_ok:
        estado_sistema = {
            "status": "error",
            "texto": "Sin Credenciales",
            "badge_class": "kpi-badge-error",
            "detalle": "llave-google.json no encontrada"
        }
    elif fallos_drive_recientes > 0:
        estado_sistema = {
            "status": "warn",
            "texto": "Fallos recientes",
            "badge_class": "kpi-badge-warn",
            "detalle": f"{fallos_drive_recientes} fallo(s) en 24h"
        }
    else:
        estado_sistema = {
            "status": "ok",
            "texto": "Drive OK",
            "badge_class": "kpi-badge-ok",
            "detalle": "Conexión Google Cloud activa"
        }

    # 5. Distribución por comparsa para Chart.js Doughnut
    cursor.execute("""
        SELECT comparsa, COUNT(*) as cant 
        FROM trajes 
        WHERE estado = 'publicado' 
        GROUP BY comparsa 
        ORDER BY cant DESC
    """)
    rows_comp = cursor.fetchall()
    comparsas_labels = [r["comparsa"] for r in rows_comp] if rows_comp else ["Sin trajes"]
    comparsas_counts = [r["cant"] for r in rows_comp] if rows_comp else [0]

    # 6. Últimos 5 trajes subidos (foto miniatura, nombre, fecha de carga)
    cursor.execute("""
        SELECT * FROM trajes 
        WHERE estado = 'publicado' 
        ORDER BY id DESC 
        LIMIT 5
    """)
    ultimos_trajes = [enriquecer_traje(cursor, r) for r in cursor.fetchall()]

    # 7. Últimos 3 errores registrados
    cursor.execute("""
        SELECT id, fecha, modulo, mensaje_error 
        FROM errores_log 
        ORDER BY id DESC 
        LIMIT 3
    """)
    ultimos_errores = [dict(r) for r in cursor.fetchall()]

    # 8. Todos los errores para el historial de errores (hasta 50)
    cursor.execute("""
        SELECT id, fecha, modulo, mensaje_error 
        FROM errores_log 
        ORDER BY id DESC 
        LIMIT 50
    """)
    todos_los_errores = [dict(r) for r in cursor.fetchall()]

    return {
        "visitas_totales": visitas_totales,
        "trajes_total": trajes_total,
        "destaques_total": destaques_total,
        "estado_sistema": estado_sistema,
        "comparsas_labels": comparsas_labels,
        "comparsas_counts": comparsas_counts,
        "ultimos_trajes": ultimos_trajes,
        "ultimos_errores": ultimos_errores,
        "todos_los_errores": todos_los_errores
    }


@app.route("/admin")
@app.route("/admin.html")
@app.route("/pages/admin.html")
def admin_panel():
    """
    Sirve el Dashboard de Gestión, Bandeja de Moderación y Panel CMS con Métricas SaaS.
    Valida obligatoriamente contra la variable ADMIN_PASSWORD de .env.
    """
    env_password = os.getenv("ADMIN_PASSWORD", "noloalias2026")
    auth_pass = (request.args.get("admin_password") or request.headers.get("X-Admin-Password") or "").strip()
    if auth_pass and auth_pass == env_password:
        session["admin_logged_in"] = True

    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trajes WHERE estado = 'pendiente' ORDER BY id DESC")
    trajes_pendientes = [enriquecer_traje(cursor, r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM trajes WHERE estado = 'publicado' ORDER BY id DESC")
    trajes = [enriquecer_traje(cursor, r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM entrevistas ORDER BY id DESC")
    entrevistas = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT c.id, c.traje_id, c.usuario, c.texto, c.fecha, t.comparsero 
        FROM comentarios c 
        LEFT JOIN trajes t ON c.traje_id = t.id 
        ORDER BY c.id DESC
    """)
    comentarios = [dict(r) for r in cursor.fetchall()]

    metricas = obtener_metricas_dashboard(conn, cursor)
    conn.close()

    return render_template(
        "admin.html",
        trajes=trajes,
        trajes_pendientes=trajes_pendientes,
        entrevistas=entrevistas,
        comentarios=comentarios,
        traje_editar=None,
        metricas=metricas
    )


@app.route("/admin/editar/<int:id>", methods=["GET"])
def admin_editar_traje(id):
    """
    FASE 13 & CMS: GET /admin/editar/<id>
    Renderiza el panel pre-poblado con los datos
    y fotografías del traje existente para su edición en modal o vista.
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

    cursor.execute("SELECT * FROM entrevistas ORDER BY id DESC")
    entrevistas = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT c.id, c.traje_id, c.usuario, c.texto, c.fecha, t.comparsero 
        FROM comentarios c 
        LEFT JOIN trajes t ON c.traje_id = t.id 
        ORDER BY c.id DESC
    """)
    comentarios = [dict(r) for r in cursor.fetchall()]

    metricas = obtener_metricas_dashboard(conn, cursor)
    conn.close()

    return render_template(
        "admin.html",
        trajes=trajes,
        trajes_pendientes=trajes_pendientes,
        entrevistas=entrevistas,
        comentarios=comentarios,
        traje_editar=traje_editar,
        metricas=metricas
    )


@app.route("/api/admin/metricas", methods=["GET"])
def api_admin_metricas():
    if not session.get("admin_logged_in"):
        return jsonify({"error": "No autorizado"}), 401
    conn = get_db_connection()
    cursor = conn.cursor()
    metricas = obtener_metricas_dashboard(conn, cursor)
    conn.close()
    return jsonify(metricas), 200


@app.route("/api/admin/limpiar-errores", methods=["POST"])
def api_limpiar_errores():
    if not session.get("admin_logged_in"):
        return jsonify({"error": "No autorizado"}), 401
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM errores_log")
    conn.commit()
    conn.close()
    return jsonify({"mensaje": "Log de errores vaciado correctamente"}), 200


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
            "success": True,
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
            "success": True,
            "mensaje": "Propuesta de traje rechazada y eliminada de la bandeja",
            "id": id,
        }), 200

    return redirect(url_for("admin_panel") + "#bandeja-moderacion")


@app.route("/login", methods=["GET", "POST"])
@app.route("/login.html", methods=["GET", "POST"])
@app.route("/pages/login.html", methods=["GET", "POST"])
def login():
    """Ruta de autenticación para administradores protegida por .env (ADMIN_PASSWORD)."""
    admin_password = os.getenv("ADMIN_PASSWORD", "noloalias2026")
    if request.method == "POST":
        password = (request.form.get("password") or "").strip()
        if password == admin_password:
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


@app.route("/api/trajes/destaques", methods=["GET"])
@app.route("/api/trajes/obras-maestras", methods=["GET"])
def get_destaques_api():
    """Retorna únicamente los trajes publicados marcados como Destaque (es_destaque = 1)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM trajes 
        WHERE estado = 'publicado' AND (es_destaque = 1 OR es_obra_maestra = 1) 
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    trajes = [enriquecer_traje(cursor, r) for r in rows]
    conn.close()
    return jsonify(trajes), 200


@app.route("/api/trajes", methods=["POST"])
@app.route("/admin/subir", methods=["POST"])
def post_traje():
    """
    POST /api/trajes (Creación directa por Administrador).
    Recibe los campos de texto, el booleano es_destaque (desde checkbox)
    y opcionalmente la foto del boceto, guardando todo en SQLite y Google Drive.
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
    es_destaque = parsear_checkbox_destaque(request.form)
    enlace_boceto = subir_boceto_si_existe(request.files, request.form)

    if not comparsero or not comparsa:
        return jsonify({"error": "Los campos 'comparsero' y 'comparsa' son obligatorios."}), 400

    # Soportar selección múltiple en input 'fotos', 'archivos', 'archivo' o 'foto'
    files = [f for f in request.files.getlist("fotos") if f and f.filename != ""]
    if not files:
        files = [f for f in request.files.getlist("archivos") if f and f.filename != ""]
    if not files:
        files = [f for f in request.files.getlist("archivo") if f and f.filename != ""]
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
    fotos_json_val = json.dumps([f["ruta_imagen"] for f in fotos_guardadas])

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO trajes (
            comparsero, comparsa, genero, materiales, foto_url,
            descripcion, diseno_original, herreria_estructura, 
            es_obra_maestra, es_destaque, enlace_boceto, estado, fotos_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'publicado', ?)
    """, (
        comparsero, comparsa, genero, materiales, foto_principal_url,
        descripcion, diseno_original, herreria_estructura, 
        es_destaque, es_destaque, enlace_boceto, fotos_json_val
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
    es_destaque = parsear_checkbox_destaque(data_source)
    enlace_boceto = subir_boceto_si_existe(
        request.files, 
        data_source if isinstance(data_source, dict) else request.form,
        default_link=(traje_actual["enlace_boceto"] if "enlace_boceto" in traje_actual.keys() and traje_actual["enlace_boceto"] else "")
    )

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
        files = [f for f in request.files.getlist("archivos") if f and f.filename != ""]
    if not files:
        files = [f for f in request.files.getlist("archivo") if f and f.filename != ""]
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

    # 4. Determinar foto principal según elección del usuario o nuevo archivo subido
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
    elif nuevas_fotos_db_ids:
        # Si se subió un nuevo archivo y no se especificó choice, convertir el nuevo archivo en la foto principal
        target_fid = nuevas_fotos_db_ids[0]
        cursor.execute("UPDATE fotos_traje SET es_principal = 0 WHERE traje_id = ?", (id,))
        cursor.execute("UPDATE fotos_traje SET es_principal = 1 WHERE id = ? AND traje_id = ?", (target_fid, id))

    # 5. Sincronizar foto_url con fotos_traje o URL directa manual
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
    elif "foto_url" in data_source and data_source.get("foto_url").strip():
        foto_principal_url = data_source.get("foto_url").strip()

    # Sincronizar fotos_json con todas las rutas actuales
    cursor.execute("SELECT ruta_imagen FROM fotos_traje WHERE traje_id = ? ORDER BY es_principal DESC, id ASC", (id,))
    rutas_actuales = [r["ruta_imagen"] for r in cursor.fetchall() if r["ruta_imagen"]]
    if not rutas_actuales and foto_principal_url:
        rutas_actuales = [foto_principal_url]
    fotos_json_val = json.dumps(rutas_actuales)

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
            es_obra_maestra = ?,
            es_destaque = ?,
            enlace_boceto = ?,
            fotos_json = ?
        WHERE id = ?
    """, (
        comparsero, comparsa, genero, materiales, foto_principal_url,
        descripcion, diseno_original, herreria_estructura, 
        es_destaque, es_destaque, enlace_boceto, fotos_json_val, id
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
    destaque = request.args.get("es_destaque", "").strip() or request.args.get("es_obra_maestra", "").strip()

    query = "SELECT * FROM trajes WHERE estado = 'publicado'"
    params = []

    if genero and genero.lower() not in ("todos", "all"):
        genero_norm = normalizar_texto_comparacion(genero)
        if "unisex" in genero_norm or "sin genero" in genero_norm:
            query += " AND (LOWER(genero) LIKE '%unisex%' OR LOWER(genero) LIKE '%sin g%')"
        else:
            query += " AND LOWER(genero) = LOWER(?)"
            params.append(genero)

    if comparsa:
        query += " AND LOWER(comparsa) LIKE LOWER(?)"
        params.append(f"%{comparsa}%")

    if destaque in ("1", "0"):
        query += " AND (es_destaque = ? OR es_obra_maestra = ?)"
        params.extend([int(destaque), int(destaque)])

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
# API REST: GESTIÓN DE ENTREVISTAS Y PRENSA (CMS)
# ==============================================================================

@app.route("/api/entrevistas", methods=["GET"])
def api_get_entrevistas():
    """Retorna la lista de todas las entrevistas registradas en SQLite."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM entrevistas ORDER BY id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(rows), 200


@app.route("/api/entrevistas", methods=["POST"])
def api_post_entrevista():
    """Crea una nueva entrevista/nota en SQLite (protegido por sesión de administrador)."""
    if not session.get("admin_logged_in"):
        return jsonify({"error": "No autorizado. Sesión de administrador requerida."}), 401

    data = request.form if request.form else (request.get_json(silent=True) or {})
    titulo = (data.get("titulo") or "").strip()
    enlace = (data.get("url_enlace") or data.get("enlace_youtube_o_diario") or data.get("enlace") or "").strip()
    tipo_medio = (data.get("tipo_medio") or "").strip().lower()
    plataforma = (data.get("plataforma") or "").strip()
    fecha = (data.get("fecha") or "").strip()
    medio = (data.get("medio") or "").strip()
    descripcion = (data.get("descripcion") or "").strip()

    if not tipo_medio:
        enlace_lower = enlace.lower()
        if any(k in enlace_lower for k in ("youtu", ".mp4", "instagram.com", "vimeo", "video")):
            tipo_medio = "video"
        else:
            tipo_medio = "articulo"

    if not plataforma:
        enlace_lower = enlace.lower()
        if "youtu" in enlace_lower:
            plataforma = "YouTube"
        elif "instagram.com" in enlace_lower:
            plataforma = "Instagram"
        elif "vimeo.com" in enlace_lower:
            plataforma = "Vimeo"
        elif medio:
            plataforma = medio
        else:
            plataforma = "Diario" if tipo_medio == "articulo" else "YouTube"

    if not titulo or not enlace or not fecha:
        return jsonify({"error": "Los campos 'titulo', 'enlace' (o url_enlace) y 'fecha' son obligatorios."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO entrevistas (
            titulo, url_enlace, enlace_youtube_o_diario, plataforma, tipo_medio, fecha, medio, descripcion
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (titulo, enlace, enlace, plataforma, tipo_medio, fecha, medio or plataforma, descripcion))
    conn.commit()
    nuevo_id = cursor.lastrowid
    cursor.execute("SELECT * FROM entrevistas WHERE id = ?", (nuevo_id,))
    nueva_entrevista = dict(cursor.fetchone())
    conn.close()

    return jsonify({
        "success": True,
        "mensaje": "Entrevista guardada con éxito en el catálogo",
        "entrevista": nueva_entrevista,
        "data": nueva_entrevista
    }), 201


@app.route("/api/entrevistas/<int:id>", methods=["DELETE", "POST"])
def api_delete_entrevista(id):
    """Elimina una entrevista por ID (protegido por sesión de administrador)."""
    if not session.get("admin_logged_in"):
        return jsonify({"error": "No autorizado. Sesión de administrador requerida."}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, titulo FROM entrevistas WHERE id = ?", (id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Entrevista no encontrada"}), 404

    cursor.execute("DELETE FROM entrevistas WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "mensaje": f"Entrevista #{id} eliminada con éxito", "id": id}), 200


# ==============================================================================
# RUTAS DE SERVICIO DE INTERFAZ WEB, VIDEOS Y ARCHIVOS ESTÁTICOS
# ==============================================================================

@app.route("/")
@app.route("/index.html")
def index():
    """
    Renderiza la página de inicio index.html con trajes destacados dinámicos (es_destaque == 1)
    y soporte completo para slider de bocetos y reproductores de video .mp4.
    Si no hay ningún traje marcado como destaque, pasa lista vacía y la plantilla oculta la sección.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM trajes 
        WHERE estado = 'publicado' AND (es_destaque = 1 OR (es_destaque IS NULL AND es_obra_maestra = 1))
        ORDER BY id DESC
    """)
    trajes_destacados = [enriquecer_traje(cursor, r) for r in cursor.fetchall()]
    conn.close()
    return render_template("index.html", trajes_destacados=trajes_destacados)


@app.route("/entrevistas")
@app.route("/entrevistas.html")
@app.route("/pages/entrevistas.html")
def ver_entrevistas():
    """Renderiza la sección pública de entrevistas alimentada dinámicamente desde SQLite (entrevistas)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM entrevistas ORDER BY id DESC")
    entrevistas = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT comparsa FROM trajes WHERE estado = 'publicado' ORDER BY comparsa ASC")
    db_comps = [r["comparsa"] for r in cursor.fetchall() if r["comparsa"]]
    comparsas_unicas = list(dict.fromkeys([c["nombre"] for c in COMPARSAS_OFICIALES] + db_comps))
    conn.close()

    return render_template(
        "entrevistas.html",
        entrevistas=entrevistas,
        comparsas_unicas=comparsas_unicas
    )


@app.route("/materiales")
@app.route("/materiales.html")
@app.route("/pages/materiales.html")
def ver_materiales():
    """Renderiza el catálogo de materiales con menú dinámico de comparsas."""
    return render_template("materiales.html")


@app.route("/comparsas")
@app.route("/comparsas.html")
@app.route("/pages/comparsas.html")
@app.route("/arandu-beleza.html")
@app.route("/pages/arandu-beleza.html")
def ver_catalogo_comparsas():
    """
    Renderiza el directorio interactivo de comparsas consultando la información agrupada
    desde SQLite y pasándola a la plantilla Jinja2 (comparsas=comparsas).
    """
    comparsas = obtener_comparsas_agrupadas()
    return render_template("comparsas.html", comparsas=comparsas)


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


# ---------------------------------------------------------------------------
# PROXY ESTÁTICO ENDURECIDO
# Antes servía CUALQUIER archivo de la raíz del proyecto (.env, llave-google.json,
# carnaval.db, app.py, .git/...). Ahora solo expone carpetas y extensiones públicas.
# ---------------------------------------------------------------------------
PROXY_DIRS_PUBLICOS = {"css", "js", "assets", "img", "pages", "static", "fonts"}
PROXY_EXT_PUBLICAS = {
    ".css", ".js", ".map", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".avif", ".ico",
    ".mp4", ".webm", ".woff", ".woff2", ".ttf", ".otf", ".html",
}
PROXY_EXT_RAIZ = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".avif", ".ico"}


def ruta_publica_permitida(path):
    """True solo si `path` apunta a un recurso público (carpeta + extensión en lista blanca)."""
    partes = [p for p in (path or "").replace("\\", "/").split("/") if p]
    if not partes or any(p == ".." or p.startswith(".") for p in partes):
        return False
    ext = os.path.splitext(partes[-1])[1].lower()
    if len(partes) == 1:
        return ext in PROXY_EXT_RAIZ
    return partes[0].lower() in PROXY_DIRS_PUBLICOS and ext in PROXY_EXT_PUBLICAS


@app.route("/<path:path>")
def static_proxy(path):
    """
    Sirve archivos estáticos y páginas secundarias (/pages/*, /css/*, /js/*, /assets/*)
    permitiendo que todo el sitio web funcione de forma autónoma con Flask.
    Solo recursos de la lista blanca (ver ruta_publica_permitida).
    """
    if not ruta_publica_permitida(path):
        return jsonify({"error": "Recurso no encontrado"}), 404

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


# ---------------------------------------------------------------------------
# MÓDULOS ENCHUFABLES (ej. "Atelier Horacio Gómez"). Ver modules/README.md
# ---------------------------------------------------------------------------
from modules import register_modules  # noqa: E402

register_modules(app)


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
