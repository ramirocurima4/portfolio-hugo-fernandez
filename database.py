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

    if "estado" not in columnas_actuales:
        cursor.execute("ALTER TABLE trajes ADD COLUMN estado VARCHAR DEFAULT 'pendiente'")
        cursor.execute("UPDATE trajes SET estado = 'publicado' WHERE estado IS NULL OR estado = 'pendiente'")
        print("[+] Migración SQLite FASE 14: Columna 'estado' agregada a tabla trajes.")

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
    conn.commit()

    # 5. Verificar si la tabla ya contiene registros de trajes
    cursor.execute("SELECT COUNT(*) FROM trajes")
    count_trajes = cursor.fetchone()[0]

    if count_trajes == 0:
        seed_data(conn)
    else:
        print(f"[*] Base de datos lista: 'trajes' ya contiene {count_trajes} registros.")
        migrar_fotos_existentes(conn)

    # 6. Verificar si la tabla de comentarios tiene datos iniciales
    cursor.execute("SELECT COUNT(*) FROM comentarios")
    count_comentarios = cursor.fetchone()[0]
    if count_comentarios == 0:
        seed_comentarios(conn)
    else:
        print(f"[*] Base de datos lista: 'comentarios' ya contiene {count_comentarios} registros.")

    conn.close()


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
