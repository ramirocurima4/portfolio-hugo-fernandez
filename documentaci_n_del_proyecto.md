# Portfolio Dinámico: Hugo Fernández - Arte Creativo & Carnaval 🎭

¡Hola! Soy **Ramiro Curimá**, estudiante de la Tecnicatura en Desarrollo de Software en San Roque, Corrientes. 

Vengo de una formación como técnico en reparación de equipos electromecánicos, y hoy aplico esa misma lógica de estructuras y conexiones al código. Este es mi primer gran proyecto Full-Stack y une mis habilidades técnicas con mi pasión: **el carnaval correntino**. 

Desarrollé esta plataforma a medida para mi tío, Hugo Fernández, Director y Coordinador General de vestuarios, para documentar y exhibir su trabajo "desde nuestro pueblo hasta las grandes pasarelas del Nolo Alías".

## 🚀 Características Principales

*   **Catálogo Dinámico:** Fichas de trajes renderizadas desde la base de datos (SSR).
*   **Experiencia Móvil Inmersiva:** Diseño *Mobile-First* con efecto `scroll-snap` (tipo reels) para la visualización de trajes, y vista de grilla clásica para comparsas.
*   **CMS Propio (Panel Admin):** Sistema oculto para cargar nuevos trajes, subir imágenes físicamente al servidor y moderar comentarios sin tocar código.
*   **Interacción Social:** Sistema de comentarios públicos en cada ficha de traje.
*   **SEO y Open Graph:** Etiquetas dinámicas para generar vistas previas enriquecidas al compartir los enlaces en WhatsApp o redes sociales.

## 🛠️ Tecnologías Utilizadas

*   **Backend:** Python 3, Flask, Werkzeug.
*   **Base de Datos:** SQLite (Embebida, archivo `carnaval.db`).
*   **Frontend:** HTML5, CSS3, JavaScript (Vanilla, Fetch API).

---

## ⚙️ Guía de Instalación y Ejecución (Para cambiar de PC)

Sigue estos pasos para levantar el proyecto desde cero en cualquier computadora nueva.

### 1. Clonar el repositorio
Abre la terminal en tu nueva PC y descarga el código:
```bash
git clone https://github.com/TuUsuario/portfolio-hugo-fernandez.git
cd portfolio-hugo-fernandez
```

### 2. Crear el Entorno Virtual (Aislado)
Para no mezclar las librerías de Python con las de tu computadora, crea un entorno virtual:
```bash
python -m venv venv
```

### 3. Activar el Entorno Virtual
*   **En Windows:**
    ```bash
    venv\Scripts\activate
    ```
*   **En Mac/Linux:**
    ```bash
    source venv/bin/activate
    ```
*(Sabrás que está activado porque aparecerá `(venv)` al principio de la línea en tu terminal).*

### 4. Instalar Dependencias
Instala Flask y las herramientas necesarias:
```bash
pip install Flask Werkzeug
```
*(Nota: Si más adelante agregas un archivo `requirements.txt`, puedes usar `pip install -r requirements.txt`)*

### 5. Iniciar el Servidor
Ejecuta el archivo principal:
```bash
python app.py
```
El servidor arrancará y verás en la consola que está corriendo en `http://127.0.0.1:5000/`.

---

## 🎛️ Uso del Panel de Administración (CMS)

Para gestionar la página web, ingresa desde tu navegador a:
**`http://127.0.0.1:5000/admin`**

Desde este panel podrás:
1.  **Cargar Trajes:** Completa el formulario, selecciona una foto de tu computadora y dale a subir. El servidor guardará la foto en `assets/img/` automáticamente y registrará los datos en SQLite.
2.  **Moderar Comentarios:** Verás una lista con todos los mensajes que dejó la gente. Tienes un botón rojo para eliminar cualquier comentario inapropiado.

---
*Desarrollado con pasión, mate y código en Corrientes, Argentina.* 🧉💻