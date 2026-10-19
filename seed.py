"""
Hugo Fernández Arte Creativo - Script Independiente de Seed de Datos (FASE 14)
Módulo 2: Páginas de Comparsas y Seed de Datos Automático del Carnaval Correntino.

Conecta a SQLite (carnaval.db), garantiza el esquema actualizado e inyecta 6 trajes
de prueba realistas del Carnaval de Corrientes ("Capital Nacional del Carnaval") con
estado 'publicado', créditos de herrería, diseño original, materiales de alta costura,
descripciones ricas y galería fotográfica en fotos_traje para las 6 agrupaciones:
  1. Arandú Beleza
  2. Sapucay
  3. Ará Berá
  4. Samba Total
  5. Copacabana
  6. Imperio Bahiano
"""

from database import get_db_connection, init_db

TRAJES_SEED_FASE_14 = [
    {
        "comparsero": "Hechicera del Paraná (Gran Bastonera de Escuela de Samba)",
        "comparsa": "Arandú Beleza",
        "genero": "Femenino",
        "materiales": (
            "12.000 Cristales Boreales Checos, 420 Plumas de Faisán Real y Avestruz Verde Esmeralda, "
            "Malla Ilusión Italiana, Casquete en Termoformado Dorado, Galones de Lurex"
        ),
        "foto_url": "https://images.unsplash.com/photo-1549488344-1f9b8d2bd1f3?q=80&w=900&auto=format&fit=crop",
        "descripcion": (
            "Obra alegórica inspirada en la mística guaraní y el espíritu de las aguas del río Paraná. "
            "Su estructura ergonómica de peso balanceado permite el despliegue rítmico frente a la batería "
            "de La Verde y Blanca bajo los reflectores del Corsódromo Nolo Alías."
        ),
        "diseno_original": "Mario 'Chino' Gómez & Equipo de Arte Arandú",
        "herreria_estructura": "Taller Escénico Nolo Alías (3.6 kg duraluminio aeronáutico con doble arco amortiguado)",
        "es_obra_maestra": 1,
        "estado": "publicado",
        "fotos_extra": [
            (
                "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=700&auto=format&fit=crop",
                "Detalle de Bordado Boreal & Cristales",
            ),
            (
                "https://images.unsplash.com/photo-1533227268428-f9ed0900fb3b?q=80&w=700&auto=format&fit=crop",
                "Tocado Imperial & Plumaje Amazónico",
            ),
        ],
    },
    {
        "comparsero": "Soberano del Sol Naciente (Rey de Comparsa)",
        "comparsa": "Sapucay",
        "genero": "Masculino",
        "materiales": (
            "Plumas de Faisán Dorado y Gallo Amazónico, 15.000 Piedras Engarzadas en Bronce, "
            "Terciopelo Imperial Rojo Rubí, Filigrana Metálica Soldada, Hombreras Cinceladas"
        ),
        "foto_url": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?q=80&w=900&auto=format&fit=crop",
        "descripcion": (
            "Majestuoso vestuario real que celebra el grito triunfal del Gallo en la calzada correntina. "
            "Destaca por su imponente espaldar radial con rayos de orfebrería dorada, pechera articulada "
            "y plumaje seleccionado de máxima envergadura."
        ),
        "diseno_original": "Horacio Gómez & Atelier del Gallo",
        "herreria_estructura": "Herrería Artística TIG Corrientes (4.8 kg acero al carbono ultraliviano y bronce pulido)",
        "es_obra_maestra": 1,
        "estado": "publicado",
        "fotos_extra": [
            (
                "https://images.unsplash.com/photo-1506152983158-b4a74a01c721?q=80&w=700&auto=format&fit=crop",
                "Espaldar Radial en Filigrana Dorada",
            ),
            (
                "https://images.unsplash.com/photo-1549488344-1f9b8d2bd1f3?q=80&w=700&auto=format&fit=crop",
                "Pechera & Orfebrería en Bronce",
            ),
        ],
    },
    {
        "comparsero": "Diosa del Rayo Celestial (Embajadora de Comparsa)",
        "comparsa": "Ará Berá",
        "genero": "Femenino",
        "materiales": (
            "14.500 Strass Cristal y Rojo Fuego, 500 Plumas de Avestruz Blanco Nieve, "
            "Galones Plateados, Corselete de Lentejuelas Láser, Botas Esculpidas a Medida"
        ),
        "foto_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=900&auto=format&fit=crop",
        "descripcion": (
            "Creado para encarnar la energía eléctrica del Rayo en la noche del carnaval correntino. "
            "Cada cristal fue bordado artesanalmente siguiendo líneas de destello centrífugo que multiplican "
            "la luz escénica en cada giro de pasarela."
        ),
        "diseno_original": "Comisión de Diseño Ará Berá & Hugo Fernández",
        "herreria_estructura": "Hugo Fernández & Taller de Estructuras (3.4 kg aluminio anodizado con arnés lumbar acolchado)",
        "es_obra_maestra": 1,
        "estado": "publicado",
        "fotos_extra": [
            (
                "https://images.unsplash.com/photo-1533227268428-f9ed0900fb3b?q=80&w=700&auto=format&fit=crop",
                "Corona de Rayos & Cristales Checos",
            ),
            (
                "https://images.unsplash.com/photo-1549488344-1f9b8d2bd1f3?q=80&w=700&auto=format&fit=crop",
                "Corselete Esculpido en Strass Rojo y Plata",
            ),
        ],
    },
    {
        "comparsero": "Emperador del Ritmo y la Percusión (Bastonero Mayor)",
        "comparsa": "Samba Total",
        "genero": "Masculino",
        "materiales": (
            "Cuero Ecológico Metalizado Azul y Plata, 8.500 Cristales Zafiro, Plumas de Pavo Real y Avestruz, "
            "Tachas Torneadas, Hombreras Anatómicas Articuladas"
        ),
        "foto_url": "https://images.unsplash.com/photo-1506152983158-b4a74a01c721?q=80&w=900&auto=format&fit=crop",
        "descripcion": (
            "Diseñado específicamente para resistir la cadencia explosiva de La Aplanadora del Ritmo durante "
            "todo el desfile en el corsódromo. Su ingeniería de distribución lumbar brinda libertad absoluta "
            "de samba no pé, giro y salto."
        ),
        "diseno_original": "Hugo Fernández (Dirección Creativa & Realización)",
        "herreria_estructura": "Taller Hugo Fernández (3.1 kg estructura articulada de alta movilidad)",
        "es_obra_maestra": 1,
        "estado": "publicado",
        "fotos_extra": [
            (
                "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?q=80&w=700&auto=format&fit=crop",
                "Arnés Lumbar de Alta Movilidad",
            ),
            (
                "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=700&auto=format&fit=crop",
                "Apliques Zafiro & Terminaciones en Cuero",
            ),
        ],
    },
    {
        "comparsero": "Emperatriz del Esplendor Dorado (Reina del Carnaval)",
        "comparsa": "Copacabana",
        "genero": "Femenino",
        "materiales": (
            "18.000 Cristales Swarovski y Strass Dorado, Perlas Cultivadas de Fantasía, "
            "450 Plumas de Avestruz Champagne, Tul Bordado en Hilos de Oro, Malla Metálica"
        ),
        "foto_url": "https://images.unsplash.com/photo-1533227268428-f9ed0900fb3b?q=80&w=900&auto=format&fit=crop",
        "descripcion": (
            "Homenaje a la tradición y la elegancia clásica de Copacabana, la comparsa decana y pionera "
            "del Carnaval Correntino. Un trabajo de alta costura artesanal con bordado milimétrico en hilos "
            "de oro y un tocado corona de triple altura."
        ),
        "diseno_original": "Gabinete Histórico de Diseño Copacabana",
        "herreria_estructura": "Orfebrería & Herrería del Litoral (4.1 kg estructura de abanico imperial en duraluminio)",
        "es_obra_maestra": 1,
        "estado": "publicado",
        "fotos_extra": [
            (
                "https://images.unsplash.com/photo-1549488344-1f9b8d2bd1f3?q=80&w=700&auto=format&fit=crop",
                "Bordado en Hilos de Oro & Perlas",
            ),
            (
                "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=700&auto=format&fit=crop",
                "Abanico Imperial en Plumas Champagne",
            ),
        ],
    },
    {
        "comparsero": "Guerrero de la Bahía Tropical (Solista de Batería)",
        "comparsa": "Imperio Bahiano",
        "genero": "Masculino",
        "materiales": (
            "Acetato Espejado Verde y Oro, 7.200 Piedras Facetadas Esmeralda, Plumas Amazónicas Bicolor, "
            "Cadenas Doradas Anodizadas, Grebas y Brazaletes Termoformados"
        ),
        "foto_url": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?q=80&w=900&auto=format&fit=crop",
        "descripcion": (
            "Inspirado en la fuerza afro-bahiana y el pulso vibrante de los tambores correntinos. "
            "Combina placas termoformadas de alto brillo con plumaje tropical resistente a la intemperie "
            "y al movimiento constante de la agrupación musical."
        ),
        "diseno_original": "Atelier Imperio Bahiano & Hugo Fernández",
        "herreria_estructura": "Estructura Dorsal Liviana TIG (3.3 kg duraluminio con anclaje rápido de seguridad)",
        "es_obra_maestra": 0,
        "estado": "publicado",
        "fotos_extra": [
            (
                "https://images.unsplash.com/photo-1506152983158-b4a74a01c721?q=80&w=700&auto=format&fit=crop",
                "Coraza Termoformada Esmeralda & Oro",
            ),
            (
                "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?q=80&w=700&auto=format&fit=crop",
                "Casquete & Plumaje Bicolor",
            ),
        ],
    },
]


def ejecutar_seed():
    """
    Inicializa la base de datos SQLite e inyecta los 6 trajes representativos de las
    comparsas del Carnaval Correntino (FASE 14) con estado 'publicado'.
    """
    init_db()

    conn = get_db_connection()
    cursor = conn.cursor()

    insertados = 0
    actualizados = 0

    for item in TRAJES_SEED_FASE_14:
        # Verificar si ya existe este traje específico para evitar duplicados en ejecuciones repetidas
        cursor.execute(
            "SELECT id FROM trajes WHERE comparsero = ? AND comparsa = ?",
            (item["comparsero"], item["comparsa"]),
        )
        existente = cursor.fetchone()

        if existente:
            traje_id = existente["id"]
            cursor.execute(
                """
                UPDATE trajes
                SET genero = ?,
                    materiales = ?,
                    foto_url = ?,
                    descripcion = ?,
                    diseno_original = ?,
                    herreria_estructura = ?,
                    es_obra_maestra = ?,
                    estado = 'publicado'
                WHERE id = ?
                """,
                (
                    item["genero"],
                    item["materiales"],
                    item["foto_url"],
                    item["descripcion"],
                    item["diseno_original"],
                    item["herreria_estructura"],
                    item["es_obra_maestra"],
                    traje_id,
                ),
            )
            actualizados += 1
        else:
            cursor.execute(
                """
                INSERT INTO trajes (
                    comparsero, comparsa, genero, materiales, foto_url,
                    descripcion, diseno_original, herreria_estructura, es_obra_maestra, estado
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["comparsero"],
                    item["comparsa"],
                    item["genero"],
                    item["materiales"],
                    item["foto_url"],
                    item["descripcion"],
                    item["diseno_original"],
                    item["herreria_estructura"],
                    item["es_obra_maestra"],
                    item["estado"],
                ),
            )
            traje_id = cursor.lastrowid
            insertados += 1

            # Insertar galería fotográfica asociada en fotos_traje
            cursor.execute(
                """
                INSERT INTO fotos_traje (traje_id, ruta_imagen, titulo, es_principal)
                VALUES (?, ?, ?, 1)
                """,
                (traje_id, item["foto_url"], "Vista Principal en Corsódromo"),
            )

            for ruta_extra, titulo_extra in item.get("fotos_extra", []):
                cursor.execute(
                    """
                    INSERT INTO fotos_traje (traje_id, ruta_imagen, titulo, es_principal)
                    VALUES (?, ?, ?, 0)
                    """,
                    (traje_id, ruta_extra, titulo_extra),
                )

    conn.commit()
    conn.close()

    print("=================================================================")
    print("  SEED DE DATOS AUTOMÁTICO - CARNAVAL CORRENTINO (FASE 14)")
    print(f"  [+] Trajes nuevos insertados: {insertados}")
    print(f"  [*] Trajes existentes sincronizados: {actualizados}")
    print("  [+] Comparsas cubiertas: Arandú Beleza, Sapucay, Ará Berá,")
    print("      Samba Total, Copacabana e Imperio Bahiano (estado='publicado').")
    print("=================================================================")


if __name__ == "__main__":
    ejecutar_seed()
