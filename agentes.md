# Directivas de Diseño y Reglas del Proyecto - Hugo Fernández Arte Creativo

## Identidad Visual y Paleta Cromática
- **Fondo Primario:** `#0a0a0a` (Negro absoluto, elegancia escénica y teatral).
- **Acentos y Contenedores:** `#0a192f` (Azul noche profundo, alta costura).
- **Gradiente Dorado de Identidad:** `linear-gradient(45deg, #BF953F, #FCF6BA, #B38728, #FBF5B7)`
  - Usado para títulos principales, isotipos y acentos de lujo.
  - `-webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;`
- **Textos de Lectura:** 
  - Blancos `#ffffff` y grises claros `#e2e8f0` para máxima legibilidad.
  - Grises medios `#94a3b8` para metadatos, cargos y anotaciones técnicas.
- **Tipografías:**
  - Títulos: *Cinzel* (Google Fonts) / Serif clásico de alta costura.
  - Textos y Fichas: *Montserrat* / Sans-serif moderno y limpio.

## Principios de Arquitectura & UI/UX
1. **Rol de Hugo Fernández:** Hugo es el **Coordinador y Realizador General** de vestuarios. No siempre es el diseñador original ni el herrero; las fichas técnicas deben reflejar esta distinción con absoluto respeto y profesionalismo.
2. **Utilidad para Comparseros:** Las fichas no son solo vitrinas estéticas, son **guías técnicas de materiales y presupuestos** (con cantidades y dimensiones estimadas).
3. **Escalabilidad:** Estructura modular en `/css`, `/js`, `/pages`, `/assets`.
4. **Navegación Fluida:** Header sticky dinámico con logo a la derecha y dropdowns interactivos.
