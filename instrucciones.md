# Guía de Integración Frontend con API Flask y SQLite

Este documento detalla cómo conectar la interfaz de usuario con la API RESTful generada en `app.py`.

---

## 1. Endpoints Disponibles en el Backend

El servidor Flask expone los siguientes endpoints:

| Método | Endpoint | Descripción | Parámetros Query String |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/trajes` | Devuelve todos los trajes registrados en `carnaval.db`. | Ninguno |
| `GET` | `/api/trajes/filtrar` | Devuelve trajes filtrados dinámicamente. | `genero` (ej. `Femenino`, `Masculino`), `comparsa` (ej. `Panambí`), `q` (búsqueda general) |

### Ejemplo de Respuesta JSON:
```json
[
  {
    "id": 1,
    "comparsero": "El Ave Fénix Solar (Gran Bastonera)",
    "comparsa": "Arandú Beleza",
    "genero": "Femenino",
    "materiales": "Strass Checo Boreal, 350 Plumas Amazónicas Ocre, Faisanes de Collar, Duraluminio 3.8kg, Terciopelo de Seda",
    "foto_url": "https://images.unsplash.com/photo-1549488344-1f9b8d2bd1f3?q=80&w=800&auto=format&fit=crop"
  }
]
```

---

## 2. Cómo sustituir las tarjetas estáticas por tarjetas dinámicas en JavaScript

Para reemplazar el HTML cableado en `pages/arandu-beleza.html` y permitir que los trajes se carguen dinámicamente desde la base de datos, implementa la siguiente función en `js/main.js`:

```javascript
/**
 * Carga dinámica de trajes desde la API de Flask
 */
async function cargarTrajesDesdeAPI() {
  const gridContainer = document.querySelector('.comparseros-grid');
  if (!gridContainer) return;

  try {
    const response = await fetch('/api/trajes');
    if (!response.ok) {
      throw new Error(`Error en el servidor: ${response.status}`);
    }

    const trajes = await response.json();
    
    // Limpiar contenido estático previo
    gridContainer.innerHTML = '';

    // Dibujar cada tarjeta dinámicamente en el DOM
    trajes.forEach(traje => {
      const card = document.createElement('article');
      card.className = 'comparsero-card reveal';
      card.setAttribute('data-category', traje.genero.toLowerCase());
      card.setAttribute('data-tags', `${traje.comparsero}, ${traje.comparsa}, ${traje.materiales}`);

      card.innerHTML = `
        <div class="comparsero-thumb">
          <span class="comparsero-badge">${traje.genero} • ${traje.comparsa}</span>
          <img src="${traje.foto_url}" alt="${traje.comparsero}" loading="lazy">
        </div>
        <div class="comparsero-body">
          <div>
            <h2 class="comparsero-title">${traje.comparsero}</h2>
            <p class="comparsero-subtitle">${traje.comparsa}</p>
          </div>
          <a href="traje-detalle.html?id=${traje.id}" class="btn-ver-ficha">
            Ver Ficha del Traje <span class="arrow-icon">→</span>
          </a>
        </div>
      `;

      gridContainer.appendChild(card);
    });

    // Re-vincular los eventos del buscador y las pestañas
    if (typeof initGalleryFilterAndSearch === 'function') {
      initGalleryFilterAndSearch();
    }
    
    // Re-observar para activar animaciones fade-in / slide-up
    if (typeof initIntersectionObserver === 'function') {
      initIntersectionObserver();
    }

  } catch (error) {
    console.error('No se pudo cargar el catálogo dinámico:', error);
  }
}
```

---

## 3. Cómo Ejecutar el Servidor

Desde la terminal en el directorio raíz del proyecto:

```bash
python app.py
```

El servidor quedará disponible en:
- Interfaz Web: `http://127.0.0.1:5000`
- API REST: `http://127.0.0.1:5000/api/trajes`
