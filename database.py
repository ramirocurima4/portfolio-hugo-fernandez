"""
Hugo Fernández Arte Creativo - Módulo de Base de Datos SQLite
FASE 13: Arquitectura Definitiva (Galería Dinámica, Edición, Obras Maestras y Fix de Feed).
"""

import sqlite3
import os

DB_NAME = "carnaval.db"
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_NAME)


def get_db_connection():
    """Retorna una conexión a la base de datos SQLite con formato de diccionario (sqlite3.Row) y claves foráneas activas."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """
    Inicializa el esquema de base de datos, ejecuta migraciones automáticas
    para las columnas de FASE 13 y puebla datos iniciales si no existen.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Creación de la tabla trajes (esquema definitivo FASE 13 & FASE 14)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comparsero TEXT NOT NULL,
            comparsa TEXT NOT NULL,
            genero TEXT NOT NULL,
            materiales TEXT NOT NULL,
            foto_url TEXT,
            descripcion TEXT,
            diseno_original TEXT,
            herreria_estructura TEXT,
            es_obra_maestra BOOLEAN DEFAULT 0,
            es_destaque BOOLEAN DEFAULT 0,
            enlace_boceto TEXT,
            estado VARCHAR DEFAULT 'pendiente'
        )
    """)

    # 2. Migración dinámica de columnas sobre la tabla trajes (si ya existía con esquema previo)
    cursor.execute("PRAGMA table_info(trajes)")
    columnas_actuales = [row["name"] for row in cursor.fetchall()]

    if "descripcion" not in columnas_actuales:
        cursor.execute("ALTER TABLE trajes ADD COLUMN descripcion TEXT")
        print("[+] Migración SQLite: Columna 'descripcion' agregada a tabla trajes.")

    if "diseno_original" not in columnas_actuales:
        cursor.execute("ALTER TABLE trajes ADD COLUMN diseno_original TEXT")
        print("[+] Migración SQLite: Columna 'diseno_original' agregada a tabla trajes.")

    if "herreria_estructura" not in columnas_actuales:
        cursor.execute("ALTER TABLE trajes ADD COLUMN herreria_estructura TEXT")
        print("[+] Migración SQLite: Columna 'herreria_estructura' agregada a tabla trajes.")

    if "es_obra_maestra" not in columnas_actuales:
        cursor.execute("ALTER TABLE trajes ADD COLUMN es_obra_maestra BOOLEAN DEFAULT 0")
        cursor.execute("UPDATE trajes SET es_obra_maestra = 1 WHERE id IN (1, 2, 3, 4)")
        print("[+] Migración SQLite: Columna 'es_obra_maestra' agregada a tabla trajes.")

    if "es_destaque" not in columnas_actuales:
        cursor.execute("ALTER TABLE trajes ADD COLUMN es_destaque BOOLEAN DEFAULT 0")
        if "es_obra_maestra" in columnas_actuales:
            cursor.execute("UPDATE trajes SET es_destaque = 1 WHERE es_obra_maestra = 1")
        else:
            cursor.execute("UPDATE trajes SET es_destaque = 1 WHERE id IN (1, 2, 3, 4)")
        print("[+] Migración SQLite: Columna 'es_destaque' agregada a tabla trajes.")

    if "enlace_boceto" not in columnas_actuales:
        cursor.execute("ALTER TABLE trajes ADD COLUMN enlace_boceto TEXT")
        print("[+] Migración SQLite: Columna 'enlace_boceto' agregada a tabla trajes.")

    if "fecha_creacion" not in columnas_actuales:
        cursor.execute("ALTER TABLE trajes ADD COLUMN fecha_creacion TIMESTAMP")
        cursor.execute("UPDATE trajes SET fecha_creacion = CURRENT_TIMESTAMP WHERE fecha_creacion IS NULL")
        print("[+] Migración SQLite: Columna 'fecha_creacion' agregada a tabla trajes.")

    # Asegurar que los trajes destacados iniciales tengan bocetos de demostración para el slider
    cursor.execute("""
        UPDATE trajes 
        SET enlace_boceto = 'https://images.unsplash.com/photo-1579783902614-a3fb3927b675?q=80&w=800&auto=format&fit=crop'
        WHERE id = 1 AND (enlace_boceto IS NULL OR enlace_boceto = '')
    """)

    if "estado" not in columnas_actuales:
        cursor.execute("ALTER TABLE trajes ADD COLUMN estado VARCHAR DEFAULT 'pendiente'")
        cursor.execute("UPDATE trajes SET estado = 'publicado' WHERE estado IS NULL OR estado = 'pendiente'")
        print("[+] Migración SQLite FASE 14: Columna 'estado' agregada a tabla trajes.")

    if "fotos_json" not in columnas_actuales:
        cursor.execute("ALTER TABLE trajes ADD COLUMN fotos_json TEXT")
        print("[+] Migración SQLite: Columna 'fotos_json' agregada a tabla trajes.")

    # Sincronizar fotos_json para trajes existentes desde fotos_traje
    cursor.execute("SELECT id FROM trajes WHERE fotos_json IS NULL OR fotos_json = ''")
    trajes_sin_json = [r["id"] for r in cursor.fetchall()]
    for tid in trajes_sin_json:
        cursor.execute("SELECT ruta_imagen FROM fotos_traje WHERE traje_id = ? ORDER BY es_principal DESC, id ASC", (tid,))
        rutas = [row["ruta_imagen"] for row in cursor.fetchall() if row["ruta_imagen"]]
        if not rutas:
            cursor.execute("SELECT foto_url FROM trajes WHERE id = ?", (tid,))
            f_row = cursor.fetchone()
            if f_row and f_row["foto_url"]:
                rutas = [f_row["foto_url"]]
        import json as _json
        cursor.execute("UPDATE trajes SET fotos_json = ? WHERE id = ?", (_json.dumps(rutas), tid))

    # 3. Creación de la tabla fotos_traje (FASE 12 & 13: Galería Dinámica Múltiple)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fotos_traje (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            traje_id INTEGER NOT NULL,
            ruta_imagen TEXT NOT NULL,
            titulo TEXT,
            es_principal BOOLEAN DEFAULT 0,
            FOREIGN KEY (traje_id) REFERENCES trajes (id) ON DELETE CASCADE
        )
    """)

    # 4. Creación de la tabla comentarios (FASE 7)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comentarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            traje_id INTEGER NOT NULL,
            usuario TEXT NOT NULL,
            texto TEXT NOT NULL,
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (traje_id) REFERENCES trajes (id) ON DELETE CASCADE
        )
    """)

    # 5. Creación de la tabla visitas (Métricas & Tráfico Dashboard SaaS)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visitas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ruta TEXT NOT NULL,
            ip_hash TEXT NOT NULL
        )
    """)

    # 6. Creación de la tabla errores_log (Auditoría & Resiliencia Google Drive)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS errores_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modulo TEXT NOT NULL,
            mensaje_error TEXT NOT NULL
        )
    """)

    # 7. Creación de la tabla trayectoria (Carrusel de Trayectoria ordenado de más reciente/actual a más antigua)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trayectoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            ciudad TEXT NOT NULL,
            anios TEXT NOT NULL,
            badge TEXT NOT NULL,
            rol TEXT NOT NULL,
            rol_snippet TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            anio_inicio INTEGER DEFAULT 2000,
            anio_fin INTEGER DEFAULT 2025,
            es_actual BOOLEAN DEFAULT 0
        )
    """)

    # 8. Creación de la tabla entrevistas (Módulo Híbrido Audiovisual & Prensa CMS)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entrevistas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            url_enlace TEXT NOT NULL,
            enlace_youtube_o_diario TEXT,
            plataforma TEXT NOT NULL DEFAULT 'YouTube',
            tipo_medio TEXT NOT NULL DEFAULT 'video',
            fecha TEXT NOT NULL,
            medio TEXT,
            descripcion TEXT
        )
    """)

    cursor.execute("PRAGMA table_info(entrevistas)")
    columnas_entrevistas = [r["name"] for r in cursor.fetchall()]

    if "url_enlace" not in columnas_entrevistas:
        cursor.execute("ALTER TABLE entrevistas ADD COLUMN url_enlace TEXT")
        print("[+] Migración SQLite: Columna 'url_enlace' agregada a tabla entrevistas.")

    if "plataforma" not in columnas_entrevistas:
        cursor.execute("ALTER TABLE entrevistas ADD COLUMN plataforma TEXT DEFAULT 'YouTube'")
        print("[+] Migración SQLite: Columna 'plataforma' agregada a tabla entrevistas.")

    if "tipo_medio" not in columnas_entrevistas:
        cursor.execute("ALTER TABLE entrevistas ADD COLUMN tipo_medio TEXT DEFAULT 'video'")
        print("[+] Migración SQLite: Columna 'tipo_medio' agregada a tabla entrevistas.")

    if "enlace_youtube_o_diario" not in columnas_entrevistas:
        cursor.execute("ALTER TABLE entrevistas ADD COLUMN enlace_youtube_o_diario TEXT")
        print("[+] Migración SQLite: Columna 'enlace_youtube_o_diario' agregada a tabla entrevistas.")

    # Sincronizar datos y valores preexistentes de entrevistas
    cursor.execute("""
        UPDATE entrevistas 
        SET url_enlace = COALESCE(NULLIF(url_enlace, ''), enlace_youtube_o_diario, '')
        WHERE url_enlace IS NULL OR url_enlace = ''
    """)
    cursor.execute("""
        UPDATE entrevistas 
        SET enlace_youtube_o_diario = COALESCE(NULLIF(enlace_youtube_o_diario, ''), url_enlace, '')
        WHERE enlace_youtube_o_diario IS NULL OR enlace_youtube_o_diario = ''
    """)
    cursor.execute("""
        UPDATE entrevistas 
        SET plataforma = COALESCE(NULLIF(plataforma, ''), medio, 'Diario')
        WHERE plataforma IS NULL OR plataforma = ''
    """)
    cursor.execute("""
        UPDATE entrevistas 
        SET tipo_medio = CASE 
            WHEN (url_enlace LIKE '%youtu%' OR url_enlace LIKE '%.mp4%' OR url_enlace LIKE '%video%' OR url_enlace LIKE '%instagram%') THEN 'video' 
            ELSE 'articulo' 
        END
        WHERE tipo_medio IS NULL OR tipo_medio = ''
    """)
    conn.commit()

    # 5. Verificar si la tabla ya contiene registros de trajes
    cursor.execute("SELECT COUNT(*) FROM trajes")
    count_trajes = cursor.fetchone()[0]

    if count_trajes == 0:
        seed_data(conn)
    else:
        print(f"[*] Base de datos lista: 'trajes' ya contiene {count_trajes} registros.")
        migrar_fotos_existentes(conn)

    # Normalizar valores previos de género Unisex y asegurar que exista al menos un traje Unisex / Sin Género
    cursor.execute("""
        UPDATE trajes
        SET genero = 'Unisex / Sin Género'
        WHERE LOWER(genero) IN ('unisex', 'unisex / especial', 'sin genero', 'sin género')
    """)
    cursor.execute("SELECT COUNT(*) FROM trajes WHERE genero = 'Unisex / Sin Género' AND estado = 'publicado'")
    if cursor.fetchone()[0] == 0:
        seed_traje_unisex(conn)
    conn.commit()

    # 6. Verificar si la tabla de comentarios tiene datos iniciales
    cursor.execute("SELECT COUNT(*) FROM comentarios")
    count_comentarios = cursor.fetchone()[0]
    if count_comentarios == 0:
        seed_comentarios(conn)
    else:
        print(f"[*] Base de datos lista: 'comentarios' ya contiene {count_comentarios} registros.")

    # 7. Verificar si la tabla trayectoria tiene datos iniciales
    cursor.execute("SELECT COUNT(*) FROM trayectoria")
    count_trayectoria = cursor.fetchone()[0]
    if count_trayectoria == 0:
        seed_trayectoria(conn)

    # 8. Verificar si la tabla entrevistas tiene datos iniciales
    cursor.execute("SELECT COUNT(*) FROM entrevistas")
    count_entrevistas = cursor.fetchone()[0]
    if count_entrevistas == 0:
        seed_entrevistas(conn)
    else:
        print(f"[*] Base de datos lista: 'entrevistas' ya contiene {count_entrevistas} registros.")

    conn.close()


def seed_traje_unisex(conn):
    """Garantiza que exista al menos un traje en la categoría 'Unisex / Sin Género' en el catálogo."""
    cursor = conn.cursor()
    foto_url = "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?q=80&w=900&auto=format&fit=crop"
    cursor.execute("""
        INSERT INTO trajes (
            comparsero, comparsa, genero, materiales, foto_url,
            descripcion, diseno_original, herreria_estructura, es_obra_maestra, es_destaque, estado
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 1, 'publicado')
    """, (
        "Espíritu de la Fantasía Taragüí (Figura Alegórica)",
        "Arandú Beleza",
        "Unisex / Sin Género",
        "Acetato Termoformado Iridescente, 10.500 Cristales Boreales, 380 Plumas de Faisán y Avestruz, Arnés Anatómico Universal en Duraluminio 3.2kg",
        foto_url,
        "Fantasía alegórica escénica de diseño sin género concebida para proyectar simetría escultórica, ergonomía universal y máximo destello lumínico en la calzada del Corsódromo Nolo Alías.",
        "Hugo Fernández & Equipo Creativo",
        "Taller de Herrería Hugo Fernández (3.2 kg duraluminio balanceado)",
    ))
    t_id = cursor.lastrowid
    cursor.execute("""
        INSERT INTO fotos_traje (traje_id, ruta_imagen, titulo, es_principal)
        VALUES (?, ?, 'Vista Principal en Calzada', 1)
    """, (t_id, foto_url))
    conn.commit()
    print("[+] Seed SQLite: Traje 'Unisex / Sin Género' insertado en el catálogo.")


def seed_trayectoria(conn):
    """Puebla la tabla 'trayectoria' con las 10 agrupaciones del CV de Hugo Fernández y sus períodos."""
    cursor = conn.cursor()
    registros = [
        (
            "Atelier HG",
            "Corrientes Capital",
            "Producción Continua",
            "Corrientes Capital • Actualidad",
            "Miembro del Grupo Creativo",
            "Espectáculos Teatrales, Circo & Carnaval",
            "Miembro del grupo creativo en “Atelier HG”. Realización de vestuarios para carnaval y espectáculos (teatrales, circense, revisteriles y más). Realización de ornamentos decorativos con materiales y técnicas específicas de confección estilo carnaval Corrientes Capital.",
            2010,
            2026,
            1,
        ),
        (
            "Comparsa Marabú",
            "Quitilipi (Chaco)",
            "2024 / 2025",
            "Quitilipi, Chaco • 2024 / 2025",
            "Coordinador General de Vestuario y Creativo",
            "Coordinador General de Vestuario y Creativo",
            "2024 / 2025: Coordinador General de Vestuario y Creativo de la comparsa Marabú Quitilipi, Chaco.",
            2024,
            2025,
            0,
        ),
        (
            "Arandú Beleza",
            "Corrientes Capital",
            "2023 / 2025",
            "Corrientes Capital • 2023 / 2025",
            "Coordinador General de Vestuario y Miembro del Equipo Creativo",
            "Coordinador General & Equipo Creativo",
            "2023 / 2025: Coordinador General de Vestuario y miembro del equipo creativo de la comparsa Arandú Beleza Corrientes Capital.",
            2023,
            2025,
            0,
        ),
        (
            "Samba Total",
            "Corrientes Capital",
            "2022 / 2025",
            "Corrientes Capital • 2022 / 2025",
            "Coordinador General de Vestuario",
            "Coordinador General de Vestuario",
            "2022 / 2025: Coordinador General de Vestuario Agrupación Musical “Samba Total” (Corrientes Capital).",
            2022,
            2025,
            0,
        ),
        (
            "Comparsa Cordialísima",
            "Fontana (Chaco)",
            "2020 / 2024",
            "Fontana, Chaco • 2020 / 2024",
            "Diseñador. Coordinador General de Vestuario. Grupo Artístico",
            "Diseñador & Coordinador General de Vestuario",
            "2020 / 2024: Diseñador. Coordinador General de Vestuario. Miembro del grupo artístico de la comparsa “Cordialísima” de la localidad de Fontana (Chaco).",
            2020,
            2024,
            0,
        ),
        (
            "Comparsa Panambí",
            "San Roque (Corrientes)",
            "1990 / 2024",
            "San Roque • 1990 / 2024",
            "Diseñador, Coordinador General de Vestuario. Director de Puesta en Escena",
            "Diseñador, Coordinador General & Puesta en Escena",
            "1990 / 2024: Diseñador, Coordinador General de Vestuario. Director de Puesta en Escena de comparsa “Panambí” de la localidad de San Roque (Corrientes).",
            1990,
            2024,
            0,
        ),
        (
            "Comparsa Amistad",
            "Margarita Belén (Chaco)",
            "2017 / 2020",
            "Margarita Belén, Chaco • 2017 / 2020",
            "Coordinador General de Vestuario. Mentor de Temáticas",
            "Mentor Temático & Logística Artística",
            "2017 / 2020: Coordinador General de Vestuario. Mentor de las temáticas realizadas. Miembro de la logística y artística de comparsa “Amistad” de la localidad de Margarita Belén (Chaco).",
            2017,
            2020,
            0,
        ),
        (
            "Sapucay del Taragüí",
            "Capital (Corrientes)",
            "2015 / 2020",
            "Corrientes Capital • 2015 / 2020",
            "Coordinador de Vestuario. Realizador. Coordinador General de Vestuario",
            "Coordinador General & Vestuarios Premiados",
            "2015 / 2020: Coordinador de vestuario. Realizador. Coordinador General de Vestuario comparsa “Sapucay del Taragüí” de la localidad de Capital (Corrientes). Miembro colaborador del grupo artístico de la comparsa. Realizador y confeccionista de vestuarios premiados en el carnaval Correntino.",
            2015,
            2020,
            0,
        ),
        (
            "Comparsa Bahía",
            "Villa Ángela (Chaco)",
            "2017 / 2018",
            "Villa Ángela, Chaco • 2017 / 2018",
            "Coordinador General de Vestuario",
            "Coordinador General de Vestuario",
            "2017 / 2018: Coordinador General de Vestuario comparsa “Bahía” de la localidad de Villa Ángela (Chaco).",
            2017,
            2018,
            0,
        ),
        (
            "Perla Alma Sambera",
            "Charata (Chaco)",
            "2016 / 2018",
            "Charata, Chaco • 2016 / 2018",
            "Coordinador General de Vestuario. Grupo Artístico",
            "Coordinador General de Vestuario & Artística",
            "2016 / 2018: Coordinador General de Vestuario. Miembro del grupo artístico de comparsa “Perla Alma Sambera” de la localidad de Charata (Chaco).",
            2016,
            2018,
            0,
        ),
    ]
    cursor.executemany("""
        INSERT INTO trayectoria (
            nombre, ciudad, anios, badge, rol, rol_snippet, descripcion, anio_inicio, anio_fin, es_actual
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, registros)
    conn.commit()
    print(f"[+] Seed de trayectoria insertada: {len(registros)} comparsas registradas en orden cronológico.")


def migrar_fotos_existentes(conn):
    """
    Garantiza que todos los trajes preexistentes cuenten con al menos una entrada
    marcada como principal en la tabla fotos_traje (FASE 12 & 13).
    """
    cursor = conn.cursor()
    cursor.execute("SELECT id, foto_url, comparsero FROM trajes")
    trajes = cursor.fetchall()
    migradas = 0

    for t in trajes:
        traje_id = t["id"]
        foto_url = t["foto_url"]
        if foto_url:
            cursor.execute("SELECT COUNT(*) FROM fotos_traje WHERE traje_id = ?", (traje_id,))
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO fotos_traje (traje_id, ruta_imagen, titulo, es_principal)
                    VALUES (?, ?, ?, 1)
                """, (traje_id, foto_url, "Vista Principal"))
                migradas += 1

    if migradas > 0:
        conn.commit()
        print(f"[+] Migración FASE 13: {migradas} fotos de trajes existentes sincronizadas en 'fotos_traje'.")


def seed_comentarios(conn):
    """Inserta comentarios iniciales de prueba para moderación y visualización."""
    cursor = conn.cursor()
    comentarios_iniciales = [
        (1, "Valeria R.", "Una obra de arte absoluta. El espaldar en vivo durante la noche de corsódromo fue impactante."),
        (1, "Esteban Gómez", "Increíble balance de pesos y terminaciones en strass."),
        (4, "Carla M.", "Excelente trabajo en la estructura de duraluminio y las terminaciones del corselete.")
    ]
    cursor.executemany("""
        INSERT INTO comentarios (traje_id, usuario, texto)
        VALUES (?, ?, ?)
    """, comentarios_iniciales)
    conn.commit()
    print(f"[+] Seed de comentarios insertada: {len(comentarios_iniciales)} comentarios cargados.")


def seed_entrevistas(conn):
    """Puebla la tabla 'entrevistas' con las notas y videos audiovisuales iniciales de Hugo Fernández."""
    cursor = conn.cursor()
    entrevistas_iniciales = [
        (
            "Entrevista Exclusiva: Los Secretos del Taller y el Armado de Espaldares",
            "/assets/videos/entrevista.mp4",
            "/assets/videos/entrevista.mp4",
            "Diario",
            "video",
            "Temporada Oficial",
            "Diario Época Digital",
            "Un recorrido íntimo por el taller de Hugo Fernández revelando el proceso de equilibrado de herrería, coordinación de equipo y engarce de miles de cristales para las noches de competencia."
        ),
        (
            "Solista Valentina (Parte I): Despliegue Escénico y Movimiento",
            "/assets/videos/Solista_Valentina-vid1.mp4",
            "/assets/videos/Solista_Valentina-vid1.mp4",
            "YouTube",
            "video",
            "Edición Reciente",
            "Registro en Vivo • Corsódromo",
            "Demostración real en movimiento del balance ergonómico de arnés, articulación de espaldar y refracción lumínica de cristales checos en pleno desfile."
        ),
        (
            "Solista Valentina (Parte II): Plumaje Amazónico y Terminaciones",
            "/assets/videos/Solista_Valentina-vid2.mp4",
            "/assets/videos/Solista_Valentina-vid2.mp4",
            "YouTube",
            "video",
            "Carnaval Correntino",
            "Cámara en Calzada",
            "Primeros planos de la estructura dorsal liviana y la respuesta dinámica del plumaje seleccionado frente al ritmo de batería."
        ),
        (
            "Solista Valentina (Parte III): Detrás de Escena y Calce Final",
            "/assets/videos/Solista_Valentina-vid3.mp4",
            "/assets/videos/Solista_Valentina-vid3.mp4",
            "Taller",
            "video",
            "Taller Hugo Fernández",
            "Backstage & Montaje",
            "Verificación técnica de sujeción, comodidad de corselete y destello de pedrería antes de salir a la calzada del corsódromo."
        ),
        (
            "Hugo Fernández y la Vanguardia del Carnaval: 'Cada traje es una arquitectura viva'",
            "https://diarioepoca.com/1381285-hugo-fernandez-el-arte-del-carnaval",
            "https://diarioepoca.com/1381285-hugo-fernandez-el-arte-del-carnaval",
            "Diario",
            "articulo",
            "Edición Especial",
            "Diario Época",
            "Crónica y entrevista a fondo sobre las tres décadas de vanguardia de Hugo Fernández en la confección de trajes icónicos para Arandú Beleza, Copacabana y Samba Total."
        )
    ]
    cursor.executemany("""
        INSERT INTO entrevistas (titulo, url_enlace, enlace_youtube_o_diario, plataforma, tipo_medio, fecha, medio, descripcion)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, entrevistas_iniciales)
    conn.commit()
    print(f"[+] Seed de entrevistas insertada: {len(entrevistas_iniciales)} entrevistas iniciales cargadas.")


def seed_data(conn):
    """Inserta registros de prueba iniciales (Seed Data) representativos con créditos, obras maestras y galerías."""
    cursor = conn.cursor()
    trajes_iniciales = [
        (
            "El Ave Fénix Solar (Gran Bastonera)",
            "Arandú Beleza",
            "Femenino",
            "Strass Checo Boreal, 350 Plumas Amazónicas Ocre, Faisanes de Collar, Duraluminio 3.8kg, Terciopelo de Seda",
            "https://images.unsplash.com/photo-1549488344-1f9b8d2bd1f3?q=80&w=800&auto=format&fit=crop",
            "Inspirado en el renacer del fuego y la luz escénica del corsódromo correntino, combinando ergonomía de alta movilidad para la bastonera principal.",
            "Marcos Romero (Diseño Escénico)",
            "Taller Escénico Corrientes (3.8 kg duraluminio con arnés anatómico)",
            1
        ),
        (
            "Guerrero de las Profundidades (Solista)",
            "Arandú Beleza",
            "Masculino",
            "Acetato Espejado Azul, Herrería Acerada 4.2kg, 280 Plumas Zafiro, Remaches y Garras Doradas",
            "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?q=80&w=800&auto=format&fit=crop",
            "Coraza pectoral en termoformado espejado con garras de fundición dorada y espaldar alado con doble arco amortiguado para soportar el ritmo de batería.",
            "Hugo Fernández & Equipo de Arte",
            "Herrería Artística TIG (4.2 kg acero al carbono liviano)",
            1
        ),
        (
            "Diosa de las Aguas Doradas (Reina)",
            "Panambí",
            "Femenino",
            "9.000 Cristales Checos, 1.200 Perlas de Fantasía, Plumas de Faisán Real, Malla Metálica Ligera",
            "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=800&auto=format&fit=crop",
            "Orfebrería en fundición dorada con refracción boreal y cascada de perlas de fantasía sobre malla metálica ligera para máxima prestancia real.",
            "Javier Benítez (Orfebrería Teatral)",
            "Estructura Dorsal Ultraliviana (2.9 kg)",
            1
        ),
        (
            "Emperador Místico del Iberá (Bastonero)",
            "Samba Total",
            "Masculino",
            "Cuero Ecológico Reforzado, Tachas Doradas, Espaldar Radial TIG 3.9kg, Plumas de Avestruz Amazonas",
            "https://images.unsplash.com/photo-1506152983158-b4a74a01c721?q=80&w=800&auto=format&fit=crop",
            "Espaldar radial soldado en TIG con distribución de carga lumbar, arnés anatómico de duraluminio y apliques de cuero ecológico con gemas doradas.",
            "Hugo Fernández",
            "Taller de Herrería Hugo Fernández (3.9 kg balanceado)",
            1
        )
    ]

    for t in trajes_iniciales:
        cursor.execute("""
            INSERT INTO trajes (comparsero, comparsa, genero, materiales, foto_url, descripcion, diseno_original, herreria_estructura, es_obra_maestra, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'publicado')
        """, t)
        t_id = cursor.lastrowid

        # Insertar fotos en la tabla fotos_traje
        foto_principal = t[4]
        cursor.execute("""
            INSERT INTO fotos_traje (traje_id, ruta_imagen, titulo, es_principal)
            VALUES (?, ?, ?, 1)
        """, (t_id, foto_principal, "Vista Principal"))

        # Fotos de detalle complementarias para la galería
        cursor.execute("""
            INSERT INTO fotos_traje (traje_id, ruta_imagen, titulo, es_principal)
            VALUES (?, ?, ?, 0)
        """, (t_id, "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=600&auto=format&fit=crop", "Cristales & Bordado"))

        cursor.execute("""
            INSERT INTO fotos_traje (traje_id, ruta_imagen, titulo, es_principal)
            VALUES (?, ?, ?, 0)
        """, (t_id, "https://images.unsplash.com/photo-1533227268428-f9ed0900fb3b?q=80&w=600&auto=format&fit=crop", "Tocado & Plumas"))

    conn.commit()
    print(f"[+] Seed Data FASE 13 insertada exitosamente: {len(trajes_iniciales)} trajes y galerías cargadas en {DB_NAME}.")


if __name__ == "__main__":
    init_db()
