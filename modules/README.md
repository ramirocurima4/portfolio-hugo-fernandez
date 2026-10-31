# Arquitectura de Módulos Enchufables - Hugo Fernández Arte Creativo

Este directorio implementa un patrón de arquitectura modular desacoplada para el CMS y Portfolio en Flask.

## Estructura

```
modules/
├── __init__.py           # Registro dinámico de módulos y blueprints (register_modules)
├── atelier/              # Módulo dedicado "Atelier Horacio Gómez"
│   ├── __init__.py       # Blueprint con prefijo /atelier
│   └── ...
└── README.md
```

## Características
1. **No invasivo:** No altera el core de `app.py`, ni `database.py`, ni los límites de subida de Google Drive ni SQLite.
2. **Feature Flags:** Controlable vía variables de entorno (`ENABLE_ATELIER=true|false`).
3. **Plantillas y Assets Aislados:** Cada módulo puede tener sus propios subdirectorios en `templates/<modulo>` y `static/<modulo>`.
