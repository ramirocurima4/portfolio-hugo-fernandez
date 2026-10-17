"""
Script para insertar un nuevo traje en la base de datos carnaval.db.
Hugo Fernández Arte Creativo - Taller de Carnaval
"""

import os
import sqlite3

# Ruta absoluta hacia la base de datos en la raíz del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "carnaval.db")


def insertar_nuevo_traje():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    nuevo_traje = (
        "Figura Destacada (Traje Verde)",
        "Arandú Beleza",
        "Femenino",
        "Plumas amazónicas verdes, pedrería dorada y esmeralda, estructura compacta de duraluminio, corselete y botas a medida.",
        "assets/img/traje-verde.jpg"
    )

    cursor.execute("""
        INSERT INTO trajes (comparsero, comparsa, genero, materiales, foto_url)
        VALUES (?, ?, ?, ?, ?)
    """, nuevo_traje)

    conn.commit()
    conn.close()

    print("Traje inyectado con éxito")


if __name__ == "__main__":
    insertar_nuevo_traje()
