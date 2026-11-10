"""
Hugo Fernández Arte Creativo - Script de Inicialización de Base de Datos
Garantiza el esquema actualizado y la carga de la trayectoria oficial del currículum de Hugo Fernández en SQLite (carnaval.db).
"""

from database import get_db_connection, init_db


def ejecutar_seed():
    """
    Inicializa la base de datos SQLite y limpia cualquier registro de comparsas de prueba
    que no pertenezcan al currículum oficial de Hugo Fernández.
    """
    init_db()

    conn = get_db_connection()
    cursor = conn.cursor()

    # Eliminar registros de comparsas de relleno/prueba que no forman parte del CV de Hugo Fernández
    cursor.execute("""
        DELETE FROM fotos_traje
        WHERE traje_id IN (
            SELECT id FROM trajes
            WHERE comparsa IN ('Ará Berá', 'Ara Berá', 'Copacabana', 'Imperio Bahiano', 'Imperio Bahano')
               OR comparsero IN ('Comparsero Postulante Test', 'Test Comparsero')
        )
    """)
    cursor.execute("""
        DELETE FROM trajes
        WHERE comparsa IN ('Ará Berá', 'Ara Berá', 'Copacabana', 'Imperio Bahiano', 'Imperio Bahano')
           OR comparsero IN ('Comparsero Postulante Test', 'Test Comparsero')
    """)

    # Normalizar nombres de comparsas en trajes según el catálogo de trayectoria del CV
    cursor.execute("UPDATE trajes SET comparsa = 'Comparsa Panambí' WHERE comparsa = 'Panambí'")
    cursor.execute("UPDATE trajes SET comparsa = 'Sapucay del Taragüí' WHERE comparsa = 'Sapucay'")

    conn.commit()
    conn.close()
    print("[+] Base de datos sincronizada con el currículum oficial de Hugo Fernández.")


if __name__ == "__main__":
    ejecutar_seed()
