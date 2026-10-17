"""
Hugo Fernández Arte Creativo - Módulo de Base de Datos SQLite
FASE 6: Inicialización de carnaval.db, creación de esquema y Seed Data.
"""

import sqlite3
import os

DB_NAME = "carnaval.db"
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_NAME)


def get_db_connection():
    """Retorna una conexión a la base de datos SQLite con formato de diccionario (sqlite3.Row)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Crea la tabla trajes y puebla los datos iniciales si no existen."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Creación de la tabla trajes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comparsero TEXT NOT NULL,
            comparsa TEXT NOT NULL,
            genero TEXT NOT NULL,
            materiales TEXT NOT NULL,
            foto_url TEXT NOT NULL
        )
    """)

    # FASE 7: Creación de la tabla comentarios
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

    # Verificar si la tabla ya contiene registros de trajes
    cursor.execute("SELECT COUNT(*) FROM trajes")
    count_trajes = cursor.fetchone()[0]

    if count_trajes == 0:
        seed_data(conn)
    else:
        print(f"[*] Base de datos lista: 'trajes' ya contiene {count_trajes} registros.")

    # Verificar si la tabla de comentarios tiene datos iniciales
    cursor.execute("SELECT COUNT(*) FROM comentarios")
    count_comentarios = cursor.fetchone()[0]
    if count_comentarios == 0:
        seed_comentarios(conn)
    else:
        print(f"[*] Base de datos lista: 'comentarios' ya contiene {count_comentarios} registros.")

    conn.close()


def seed_comentarios(conn):
    """Inserta comentarios iniciales de prueba para moderación y visualización."""
    cursor = conn.cursor()
    comentarios_iniciales = [
        (1, "Valeria R.", "Una obra de arte absoluta. El espaldar en vivo durante la noche de corsódromo fue impactante."),
        (1, "Esteban Gómez", "Increíble balance de pesos y terminaciones en strass."),
        (5, "Carla M.", "Excelente trabajo en la estructura de duraluminio y las terminaciones del corselete verde.")
    ]
    cursor.executemany("""
        INSERT INTO comentarios (traje_id, usuario, texto)
        VALUES (?, ?, ?)
    """, comentarios_iniciales)
    conn.commit()
    print(f"[+] Seed de comentarios insertada: {len(comentarios_iniciales)} comentarios cargados.")


def seed_data(conn):
    """Inserta registros de prueba (Seed Data) representativos del carnaval."""
    cursor = conn.cursor()
    trajes_iniciales = [
        (
            "El Ave Fénix Solar (Gran Bastonera)",
            "Arandú Beleza",
            "Femenino",
            "Strass Checo Boreal, 350 Plumas Amazónicas Ocre, Faisanes de Collar, Duraluminio 3.8kg, Terciopelo de Seda",
            "https://images.unsplash.com/photo-1549488344-1f9b8d2bd1f3?q=80&w=800&auto=format&fit=crop"
        ),
        (
            "Guerrero de las Profundidades (Solista)",
            "Arandú Beleza",
            "Masculino",
            "Acetato Espejado Azul, Herrería Acerada 4.2kg, 280 Plumas Zafiro, Remaches y Garras Doradas",
            "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?q=80&w=800&auto=format&fit=crop"
        ),
        (
            "Diosa de las Aguas Doradas (Reina)",
            "Panambí",
            "Femenino",
            "9.000 Cristales Checos, 1.200 Perlas de Fantasía, Plumas de Faisán Real, Malla Metálica Ligera",
            "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=800&auto=format&fit=crop"
        ),
        (
            "Emperador Místico del Iberá (Bastonero)",
            "Samba Total",
            "Masculino",
            "Cuero Ecológico Reforzado, Tachas Doradas, Espaldar Radial TIG 3.9kg, Plumas de Avestruz Amazonas",
            "https://images.unsplash.com/photo-1506152983158-b4a74a01c721?q=80&w=800&auto=format&fit=crop"
        )
    ]

    cursor.executemany("""
        INSERT INTO trajes (comparsero, comparsa, genero, materiales, foto_url)
        VALUES (?, ?, ?, ?, ?)
    """, trajes_iniciales)

    conn.commit()
    print(f"[+] Seed Data insertada exitosamente: {len(trajes_iniciales)} trajes cargados en {DB_NAME}.")


if __name__ == "__main__":
    init_db()
