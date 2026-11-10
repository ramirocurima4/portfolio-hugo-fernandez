"""
Sistema de Módulos Enchufables - Hugo Fernández Arte Creativo
Permite registrar subsistemas y extensiones (como 'Atelier Horacio Gómez')
de forma desacoplada y modular sin alterar el motor principal de Flask,
la base de datos SQLite ni la integración con Google Drive.
"""
import os
import logging
from flask import Blueprint

logger = logging.getLogger(__name__)


def register_modules(app):
    """
    Registra automáticamente los módulos y blueprints enchufables del sistema.
    Inyecta flags y configuraciones modulares en el contexto global de Jinja2.
    """
    # Contexto global para plantillas (permite condicionales como {% if ATELIER_ENABLED %})
    @app.context_processor
    def inyectar_contexto_modulos():
        # Permite habilitar o deshabilitar el acceso al módulo mediante variable de entorno
        atelier_habilitado = os.getenv("ENABLE_ATELIER", "true").lower() in ("true", "1", "yes")
        return {
            "ATELIER_ENABLED": atelier_habilitado,
            "ENABLE_ATELIER": atelier_habilitado
        }

    # Registro del módulo Atelier Horacio Gómez
    try:
        from .atelier import atelier_bp
        app.register_blueprint(atelier_bp)
        print("[*] Módulo 'Atelier Horacio Gómez' registrado correctamente en /atelier")
    except Exception as ex:
        print(f"[!] Aviso: No se pudo inicializar el blueprint de Atelier: {ex}")
