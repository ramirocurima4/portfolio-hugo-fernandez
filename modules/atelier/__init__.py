"""
Módulo: Atelier Horacio Gómez
Submódulo preparado para la futura sección pesada del prestigioso taller.
Expone su propio Blueprint con rutas, controladores, assets y plantillas independientes.
"""
import os
from flask import Blueprint, render_template
from database import obtener_obras_atelier

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

atelier_bp = Blueprint(
    "atelier",
    __name__,
    url_prefix="/atelier",
    template_folder=os.path.join(BASE_DIR, "templates", "atelier"),
    static_folder=os.path.join(BASE_DIR, "static", "atelier"),
    static_url_path="/static/atelier"
)


@atelier_bp.route("", strict_slashes=False)
@atelier_bp.route("/", strict_slashes=False)
@atelier_bp.route("/index.html", strict_slashes=False)
def index():
    """
    Vista principal del Atelier Horacio Gómez.
    Renderiza la plantilla modular dedicada templates/atelier/index.html con las obras cargadas.
    """
    obras = []
    try:
        obras = obtener_obras_atelier()
    except Exception as e:
        print(f"[!] Error consultando obras de atelier: {e}")

    plantilla_atelier = os.path.join(BASE_DIR, "templates", "atelier", "index.html")
    if os.path.isfile(plantilla_atelier):
        return render_template("atelier/index.html", obras=obras)
    
    return render_template(
        "destaques.html",
        titulo_seccion="Atelier Horacio Gómez",
        subtitulo_seccion="Sección en fase de curaduría artística y catalogación de alta costura.",
        obras=obras
    )
