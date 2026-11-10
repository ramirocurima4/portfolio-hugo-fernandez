/**
 * Hugo Fernández Arte Creativo - Main JavaScript
 * Control de Header Dinámico (Sticky Scroll), Intersection Observer para animaciones,
 * Pestañas de Filtrado, Buscador Dinámico en Tiempo Real (Fase 2), Visor de Galería y UX Móvil.
 */

document.addEventListener('DOMContentLoaded', () => {
  if (window.__MAIN_JS_INITIALIZED__) return;
  window.__MAIN_JS_INITIALIZED__ = true;

  initStickyHeader();
  initCarnavalCountdown();
  initIntersectionObserver();
  initMobileMenu();
  initTrayectoriaInteractiva();
  initModalPerfilTecnico();
  initModalAptitudesTaller();
  initFiltrosGaleriaTrajes();
  cargarTrajes();
  cargarTrajesFeedMobile();
  initTrajeGalleryThumbs();
  initImageComparison();
  initFichaDetalleDinamica();
  initComentariosTraje();
});

/**
 * Efecto en el Sticky Header
 * Transición de fondo semitransparente a un color sólido (var(--azul-noche))
 * cuando el usuario se desplaza hacia abajo en la página.
 */
function initStickyHeader() {
  const header = document.querySelector('.site-header');
  if (!header) return;

  const handleScroll = () => {
    const scrollPosition = window.scrollY || document.documentElement.scrollTop;
    if (scrollPosition > 50) {
      header.classList.add('header-scrolled');
    } else {
      header.classList.remove('header-scrolled');
    }
  };

  // Escucha con throttle pasivo para optimizar el rendimiento de pintado
  window.addEventListener('scroll', handleScroll, { passive: true });
  // Comprobación inicial por si la página carga con scroll previo
  handleScroll();
}

/**
 * Animaciones de aparición con Intersection Observer
 * Permite que los trajes, imágenes, bloques de texto y tarjetas se revelen suavemente
 * (fade in / slide up) conforme van entrando en el viewport.
 */
function initIntersectionObserver() {
  const animatedElements = document.querySelectorAll(
    '.reveal, .fade-in, .slide-up, .hero-content, .hero-media-wrapper, .material-card, .traje-showcase, .entrevista-card, .servicio-card, .trayectoria-card, .comparsero-card, .coordinacion-card, .immersive-traje-card'
  );

  if (!animatedElements.length) return;

  if (!('IntersectionObserver' in window)) {
    animatedElements.forEach(el => el.classList.add('visible'));
    return;
  }

  const observerOptions = {
    root: null,
    rootMargin: '0px 0px -60px 0px',
    threshold: 0.15
  };

  const appearanceObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  animatedElements.forEach(element => {
    if (!element.classList.contains('fade-in') && 
        !element.classList.contains('slide-up') && 
        !element.classList.contains('reveal')) {
      element.classList.add('reveal');
    }
    appearanceObserver.observe(element);
  });
}

/**
 * Estado global en memoria para el catálogo dinámico de trajes (Fase 6)
 */
const catalogoTrajesState = {
  todos: [],
  categoriaActiva: 'all',
  busquedaActiva: ''
};

/**
 * Función auxiliar para sanitizar cadenas en Template Literals
 */
function escapeHTML(str) {
  if (typeof str !== 'string') return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * Normaliza cadenas de género o categoría eliminando acentos y convirtiendo a minúsculas
 */
function normalizarGeneroTexto(texto) {
  if (!texto) return '';
  return String(texto)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

/**
 * Evalúa si el género de un traje coincide con el filtro activo (Femenino, Masculino, Unisex / Sin Género, Todos)
 */
function coincideFiltroGenero(generoTraje, filtroActivo) {
  const f = normalizarGeneroTexto(filtroActivo);
  if (!f || f === 'all' || f === 'todos') return true;
  const g = normalizarGeneroTexto(generoTraje);
  if (f.includes('unisex') || f.includes('sin genero')) {
    return g.includes('unisex') || g.includes('sin genero');
  }
  if (f.includes('femenin')) {
    return g.includes('femenin');
  }
  if (f.includes('masculin')) {
    return g.includes('masculin');
  }
  return g === f;
}

/**
 * PASO 1: Carga asíncrona de trajes desde la API REST (SQLite / Flask)
 * Selecciona el contenedor .grilla-miniaturas, lo vacía e hidrata dinámicamente.
 * Respeta las grillas SSR (.comparseros-grid) que ya fueron renderizadas por Jinja2.
 */
async function cargarTrajes() {
  const gridContainer = document.querySelector('.grilla-miniaturas');
  if (!gridContainer) return;

  // Si ya fue renderizado por SSR con tarjetas reales, no sobrescribir
  if (gridContainer.children.length > 0 && gridContainer.querySelector('.comparsero-card')) {
    return;
  }

  // Estado visual de carga elegante
  gridContainer.innerHTML = `
    <div style="grid-column: 1 / -1; text-align: center; padding: 3rem 1rem; color: var(--dorado-solido);">
      <p style="font-size: 1.1rem; letter-spacing: 1px; margin-bottom: 0.5rem;">✦ Sincronizando catálogo con el taller de Hugo Fernández...</p>
      <span style="font-size: 0.85rem; color: var(--texto-gris-medio);">Cargando trajes desde la base de datos...</span>
    </div>
  `;

  try {
    const response = await fetch('/api/trajes');
    if (!response.ok) {
      throw new Error(`Error en el servidor: ${response.status}`);
    }

    const trajes = await response.json();
    catalogoTrajesState.todos = Array.isArray(trajes) ? trajes : [];

    // Inicializar listeners del buscador y botones de filtro sobre el arreglo en memoria
    initFilterAndSearchListeners();

    // Renderizar grilla con los datos cargados
    aplicarFiltrosYRenderizar();
  } catch (error) {
    console.error('Error al cargar trajes desde /api/trajes:', error);
    gridContainer.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 3rem 1rem; color: #ff6b6b; border: 1px solid rgba(255, 107, 107, 0.2); border-radius: 8px; background: rgba(10, 25, 47, 0.6);">
        <p style="font-weight: 600; margin-bottom: 0.5rem;">⚠️ No se pudo sincronizar el catálogo con la base de datos.</p>
        <p style="font-size: 0.85rem; color: var(--texto-gris-medio);">Asegurate de que el servidor Flask esté iniciado con <code>py app.py</code>.</p>
      </div>
    `;
  }
}

/**
 * Resuelve rutas de imágenes asegurando compatibilidad entre root y /pages/
 */
function resolverRutaImagen(url) {
  if (!url) return '';
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:') || url.startsWith('/')) {
    return url;
  }
  const isInPages = window.location.pathname.includes('/pages/');
  if (isInPages && !url.startsWith('../')) {
    return `../${url}`;
  }
  return url;
}

/**
 * Renderiza el arreglo de trajes dentro del contenedor .grilla-miniaturas
 * usando Template Literals y data attributes para persistencia.
 */
function renderizarGrillaMiniaturas(trajes) {
  const gridContainer = document.querySelector('.grilla-miniaturas, .comparseros-grid');
  if (!gridContainer) return;

  // Vaciar el contenedor antes de dibujar y reiniciar posición de scroll
  gridContainer.innerHTML = '';
  gridContainer.scrollTop = 0;

  const noResultsEl = document.querySelector('.search-no-results');
  const queryDisplay = document.getElementById('search-query-display');

  // Control de aviso si no hay coincidencias
  if (trajes.length === 0) {
    if (noResultsEl) {
      noResultsEl.classList.add('is-visible');
      if (queryDisplay) {
        queryDisplay.textContent = catalogoTrajesState.busquedaActiva 
          ? `"${catalogoTrajesState.busquedaActiva}"` 
          : 'el filtro seleccionado';
      }
    }
    return;
  }

  if (noResultsEl) {
    noResultsEl.classList.remove('is-visible');
  }

  // Iterar sobre los datos recibidos y generar cada .tarjeta-miniatura
  trajes.forEach((traje, index) => {
    const card = document.createElement('article');
    card.className = `comparsero-card tarjeta-miniatura reveal visible delay-${(index % 3) + 1}`;
    card.style.cursor = 'pointer';
    
    // Inyección de atributos data-id y dataset completo para hidratar traje-detalle.html
    card.setAttribute('data-id', traje.id);
    card.setAttribute('data-category', (traje.genero || '').toLowerCase());
    card.dataset.id = traje.id;
    card.dataset.traje = JSON.stringify(traje);

    const safeFoto = escapeHTML(resolverRutaImagen(traje.foto_url || ''));
    const safeComparsero = escapeHTML(traje.comparsero || 'Traje de Carnaval');
    const safeComparsa = escapeHTML(traje.comparsa || 'Comparsa Oficial');
    const safeGenero = escapeHTML(traje.genero || 'Unisex');

    const isVideo = safeFoto.toLowerCase().includes('.mp4') || safeFoto.toLowerCase().includes('/video');
    const hasBoceto = traje.enlace_boceto && String(traje.enlace_boceto).trim().length > 0;
    const safeBoceto = hasBoceto ? escapeHTML(resolverRutaImagen(traje.enlace_boceto)) : '';

    let mediaHtml = '';
    if (isVideo) {
      mediaHtml = `
        <video controls width="100%" class="destaque-video-player" style="height: 100%; object-fit: cover;" preload="metadata">
          <source src="${safeFoto}" type="video/mp4">
        </video>
      `;
    } else if (hasBoceto) {
      mediaHtml = `
        <div class="ba-slider-container" data-ba-slider style="height: 100%;">
          <img src="${safeFoto}" alt="Después: ${safeComparsero}" class="ba-img ba-after-img" loading="lazy">
          <div class="ba-before-wrapper">
            <img src="${safeBoceto}" alt="Antes: Boceto ${safeComparsero}" class="ba-img ba-before-img" loading="lazy">
          </div>
          <span class="ba-badge ba-badge-before">Antes</span>
          <span class="ba-badge ba-badge-after">Después</span>
          <div class="ba-divider"><div class="ba-handle"><span>↔</span></div></div>
          <input type="range" min="0" max="100" value="50" class="ba-range-input" aria-label="Deslizar para comparar">
        </div>
      `;
    } else {
      mediaHtml = `<img src="${safeFoto}" alt="${safeComparsero}" loading="lazy">`;
    }

    const isDestaque = traje.es_destaque || traje.es_obra_maestra;
    const destaqueBadge = isDestaque ? ' • ★ Destaque' : '';

    // FASE 8: Enlace y redirección a la ruta SSR /traje/${traje.id}
    card.innerHTML = `
      <div class="comparsero-thumb tarjeta-thumb">
        <span class="comparsero-badge tarjeta-badge">${safeGenero} • ${safeComparsa}${destaqueBadge}</span>
        ${mediaHtml}
      </div>
      <div class="comparsero-body tarjeta-body">
        <div>
          <h2 class="comparsero-title tarjeta-title">${safeComparsero}</h2>
          <p class="comparsero-subtitle tarjeta-subtitle">
            <span>🎭</span> ${safeComparsa} • <span>✦</span> ${safeGenero}
          </p>
        </div>
        <a href="/traje/${traje.id}" class="btn-ver-ficha" data-id="${traje.id}">
          Ver Ficha del Traje <span class="arrow-icon">→</span>
        </a>
      </div>
    `;

    // Persistir en sessionStorage y evento click en la tarjeta completa para redirección
    const navegarADetalle = () => {
      try {
        sessionStorage.setItem('selectedTraje', JSON.stringify(traje));
      } catch (e) {
        console.warn('Error al almacenar en sessionStorage:', e);
      }
    };

    const btnFicha = card.querySelector('.btn-ver-ficha');
    if (btnFicha) {
      btnFicha.addEventListener('click', navegarADetalle);
    }

    card.addEventListener('click', (e) => {
      if (!e.target.closest('a') && !e.target.closest('input') && !e.target.closest('video')) {
        navegarADetalle();
        window.location.href = `/traje/${traje.id}`;
      }
    });

    gridContainer.appendChild(card);
  });

  initImageComparison();
}

/**
 * PASO 2: Filtrado dinámico en memoria y re-renderizado
 * En lugar de ocultar elementos con CSS, filtra el array de datos
 * por coincidencia en comparsero, comparsa, genero o materiales y vuelve a dibujar.
 */
function aplicarFiltrosYRenderizar() {
  const query = catalogoTrajesState.busquedaActiva.toLowerCase().trim();
  const categoria = catalogoTrajesState.categoriaActiva.toLowerCase();

  const filtrados = catalogoTrajesState.todos.filter(traje => {
    // Coincidencia por categoría de botón (Todos / Femenino / Masculino / Unisex / Sin Género)
    const generoTraje = (traje.genero || '').toLowerCase();
    const coincideCategoria = coincideFiltroGenero(generoTraje, categoria);

    // Coincidencia por búsqueda de texto
    const comparsero = (traje.comparsero || '').toLowerCase();
    const comparsa = (traje.comparsa || '').toLowerCase();
    const materiales = (traje.materiales || '').toLowerCase();

    const coincideBusqueda = query === '' ||
      comparsero.includes(query) ||
      comparsa.includes(query) ||
      generoTraje.includes(query) ||
      materiales.includes(query);

    return coincideCategoria && coincideBusqueda;
  });

  // Re-renderizado de la grilla con el array ya filtrado
  renderizarGrillaMiniaturas(filtrados);
}

/**
 * Configuración de eventos para el buscador y las pestañas de categoría
 */
function initFilterAndSearchListeners() {
  const searchInput = document.querySelector('.search-input');
  const clearBtn = document.querySelector('.search-clear-btn');
  const filterButtons = document.querySelectorAll('.filter-btn');

  // Buscador dinámico en tiempo real
  if (searchInput && !searchInput.dataset.listenerBound) {
    searchInput.dataset.listenerBound = 'true';
    searchInput.addEventListener('input', (e) => {
      catalogoTrajesState.busquedaActiva = e.target.value;

      if (clearBtn) {
        if (catalogoTrajesState.busquedaActiva.length > 0) {
          clearBtn.classList.add('is-active');
        } else {
          clearBtn.classList.remove('is-active');
        }
      }

      aplicarFiltrosYRenderizar();
    });

    if (clearBtn && !clearBtn.dataset.listenerBound) {
      clearBtn.dataset.listenerBound = 'true';
      clearBtn.addEventListener('click', () => {
        searchInput.value = '';
        catalogoTrajesState.busquedaActiva = '';
        clearBtn.classList.remove('is-active');
        searchInput.focus();
        aplicarFiltrosYRenderizar();
      });
    }
  }

  // Pestañas de filtrado (Todos / Femenino / Masculino / Unisex / Sin Género)
  filterButtons.forEach(button => {
    if (!button.dataset.listenerBound) {
      button.dataset.listenerBound = 'true';
      button.addEventListener('click', () => {
        filterButtons.forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');
        catalogoTrajesState.categoriaActiva = button.getAttribute('data-filter') || 'all';
        aplicarFiltrosYRenderizar();
      });
    }
  });
}

/**
 * Filtros Inclusivos en la Galería Pública de Trajes (/trajes)
 * Permite alternar dinámicamente entre Todos, Femenino, Masculino y Unisex / Sin Género
 * sin recargar o manteniendo sincronizado el parámetro ?genero= en la URL.
 */
function initFiltrosGaleriaTrajes() {
  const filterBtns = document.querySelectorAll('.trajes-filter-btn');
  const feedContainer = document.getElementById('feed-principal');
  if (!filterBtns.length || !feedContainer) return;

  const emptyMsg = document.getElementById('trajes-empty-filter');
  const countBadge = document.getElementById('trajes-filter-count');

  const aplicarFiltroDOM = (filtroSeleccionado, actualizarURL = true) => {
    const cards = Array.from(feedContainer.querySelectorAll('.immersive-traje-card, .tarjeta-feed'));
    let visibles = 0;

    cards.forEach((card) => {
      const generoCard = card.getAttribute('data-genero') || card.dataset.genero || '';
      const esVisible = coincideFiltroGenero(generoCard, filtroSeleccionado);
      if (esVisible) {
        card.style.display = '';
        card.classList.remove('is-filtered-out');
        visibles += 1;
      } else {
        card.style.display = 'none';
        card.classList.add('is-filtered-out');
      }
    });

    filterBtns.forEach(btn => {
      const btnFilter = btn.getAttribute('data-filter') || 'todos';
      const isActive = normalizarGeneroTexto(btnFilter) === normalizarGeneroTexto(filtroSeleccionado);
      btn.classList.toggle('active', isActive);
      btn.setAttribute('aria-pressed', isActive ? 'true' : 'false');
    });

    if (countBadge) {
      countBadge.textContent = `${visibles} ${visibles === 1 ? 'obra' : 'obras'}`;
    }

    if (emptyMsg) {
      emptyMsg.style.display = visibles === 0 ? 'block' : 'none';
    }

    if (actualizarURL && window.history && window.history.replaceState) {
      const url = new URL(window.location.href);
      const norm = normalizarGeneroTexto(filtroSeleccionado);
      if (!norm || norm === 'todos' || norm === 'all') {
        url.searchParams.delete('genero');
      } else {
        url.searchParams.set('genero', filtroSeleccionado);
      }
      window.history.replaceState({}, '', url.toString());
    }
  };

  filterBtns.forEach(btn => {
    if (!btn.dataset.filterBound) {
      btn.dataset.filterBound = 'true';
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const filtro = btn.getAttribute('data-filter') || 'todos';
        aplicarFiltroDOM(filtro, true);
      });
    }
  });

  // Aplicar filtro inicial si viene en la URL (?genero=...)
  const urlParams = new URLSearchParams(window.location.search);
  const generoParam = urlParams.get('genero');
  if (generoParam) {
    aplicarFiltroDOM(generoParam, false);
  } else {
    aplicarFiltroDOM('todos', false);
  }
}

/**
 * PASO 2: Consumo de Datos en la Ficha Individual (pages/traje-detalle.html)
 * Se ejecuta únicamente cuando el usuario está en la página traje-detalle.html.
 * Lee el parámetro id de la URL, consulta la API REST e inyecta los datos en el DOM.
 */
async function initFichaDetalleDinamica() {
  // Validación de contexto: ejecutarse únicamente en traje-detalle.html
  const isDetallePage = window.location.pathname.includes('traje-detalle.html') || 
                        Boolean(document.getElementById('detalle-titulo') || document.getElementById('traje-title-txt'));
  if (!isDetallePage) return;

  // Leer el parámetro id de la URL usando URLSearchParams
  const urlParams = new URLSearchParams(window.location.search);
  const idParam = urlParams.get('id');
  if (!idParam) return;

  let trajeData = null;

  // 1. Intentar recuperar desde sessionStorage para velocidad instantánea
  try {
    const cached = sessionStorage.getItem('selectedTraje');
    if (cached) {
      const parsed = JSON.parse(cached);
      if (String(parsed.id) === String(idParam)) {
        trajeData = parsed;
      }
    }
  } catch (e) {
    console.warn('Error al leer sessionStorage:', e);
  }

  // 2. Si no estaba en sessionStorage, consultar al endpoint específico /api/trajes/<id>
  if (!trajeData) {
    try {
      const res = await fetch(`/api/trajes/${idParam}`);
      if (res.ok) {
        trajeData = await res.json();
      } else {
        // Fallback: consultar el listado general /api/trajes
        const resList = await fetch('/api/trajes');
        if (resList.ok) {
          const listado = await resList.json();
          trajeData = listado.find(t => String(t.id) === String(idParam));
        }
      }
    } catch (e) {
      console.warn(`Error al consultar la API de trajes:`, e);
    }
  }

  // 3. Inyectar datos en el DOM de la ficha individual
  if (trajeData) {
    hidratarFichaDetalle(trajeData);
  }
}

/**
 * Inyecta los datos en el DOM de la ficha:
 * - Cambia el src de la imagen principal por foto_url
 * - Cambia el título principal por el nombre del comparsero y la comparsa
 * - Inyecta la cadena de materiales en la sección del desglose técnico (reemplazando placeholders)
 */
function hidratarFichaDetalle(traje) {
  const tituloEl = document.getElementById('detalle-titulo') || document.getElementById('traje-title-txt');
  const imagenEl = document.getElementById('detalle-imagen') || document.getElementById('main-preview-img');
  const materialesEl = document.getElementById('detalle-materiales') || document.getElementById('materiales-container');
  const badgeRol = document.getElementById('traje-badge-rol');
  const metaComparsa = document.getElementById('meta-comparsa');
  const metaRol = document.getElementById('meta-rol');
  const metaRealizacion = document.getElementById('credito-realizacion');
  const pContainer = document.getElementById('traje-desc-paragraphs');
  const rImg = document.getElementById('comparison-real-img');

  // Cambia el título principal por el nombre del comparsero y la comparsa
  if (tituloEl) {
    tituloEl.textContent = `${traje.comparsero} - ${traje.comparsa}`;
  }

  // Cambia el src de la imagen principal por la foto_url
  if (imagenEl && traje.foto_url) {
    const rutaResuelta = resolverRutaImagen(traje.foto_url);
    imagenEl.src = rutaResuelta;
    imagenEl.alt = `${traje.comparsero} (${traje.comparsa})`;
  }

  // Inyecta la cadena de materiales en el desglose técnico como píldoras horizontales minimalistas
  if (materialesEl && traje.materiales) {
    materialesEl.innerHTML = '';
    const cleanMateriales = traje.materiales.replace(/\.$/, '');
    const listaMateriales = cleanMateriales.split(',').map(m => m.trim()).filter(Boolean);

    materialesEl.innerHTML = listaMateriales.map((item) => `
      <span class="material-pill">
        <span class="tag-bullet">✦</span>
        <span class="tag-name">${escapeHTML(item)}</span>
      </span>
    `).join('');
  }

  // Acentos adicionales de identidad y coherencia escénica
  if (badgeRol) {
    badgeRol.textContent = `${traje.genero} • ${traje.comparsa}`;
  }
  if (metaComparsa) {
    metaComparsa.textContent = traje.comparsa;
  }
  if (metaRol) {
    metaRol.textContent = `${traje.genero} (${traje.comparsa})`;
  }
  if (metaRealizacion) {
    metaRealizacion.textContent = 'Hugo Fernández';
  }

  // FASE 12: Créditos de Diseño Original y Herrería
  if (traje.diseno_original) {
    const disenoEl = document.getElementById('credito-diseno');
    if (disenoEl) disenoEl.textContent = traje.diseno_original;
  }
  if (traje.herreria_estructura) {
    const herreriaEl = document.getElementById('credito-herreria');
    if (herreriaEl) herreriaEl.textContent = traje.herreria_estructura;
  }

  // FASE 12: Párrafo inspiracional / descripción enriquecida
  if (pContainer) {
    if (traje.descripcion) {
      pContainer.innerHTML = `<p>${escapeHTML(traje.descripcion)}</p>`;
    } else {
      pContainer.innerHTML = `
        <p>Vestuario oficial coordinado y realizado para la figura de <strong>${escapeHTML(traje.comparsero)}</strong> de la comparsa <strong>${escapeHTML(traje.comparsa)}</strong>.</p>
        <p>Confeccionado artesanalmente bajo la dirección técnica de Hugo Fernández, integrando herrería de alta absorción de movimiento, distribución ergonómica de cargas y materiales escénicos seleccionados para máxima visibilidad en corsódromo.</p>
      `;
    }
  }

  // FASE 13: Galería de fotos dinámica con todas las fotos del traje
  if (Array.isArray(traje.fotos) && traje.fotos.length > 0) {
    const thumbsContainer = document.getElementById('gallery-thumbs-container') || document.querySelector('.gallery-thumbs');
    if (thumbsContainer) {
      thumbsContainer.innerHTML = traje.fotos.map(f => `
        <div class="gallery-thumb-item" title="Click para ampliar detalle">
          <img src="${escapeHTML(resolverRutaImagen(f.ruta_imagen))}" 
               alt="${escapeHTML(f.titulo || 'Detalle')}" loading="lazy">
          <span class="thumb-caption">${escapeHTML(f.titulo || (f.es_principal ? 'Vista Principal' : 'Detalle'))}</span>
        </div>
      `).join('');
      initTrajeGalleryThumbs();
    }
  }

  // Sincronizar imagen de realidad en slider comparativo
  if (rImg && traje.foto_url) {
    rImg.src = resolverRutaImagen(traje.foto_url);
  }
}

/**
 * FASE 13: Carga dinámica y sin filtros hardcodeados del Feed Vertical Inmersivo (Scroll Snap)
 * Selecciona los contenedores .feed-trajes-mobile y los alimenta con todos los trajes registrados en SQLite.
 */
async function cargarTrajesFeedMobile() {
  const feedContainers = document.querySelectorAll('.feed-trajes-mobile');
  if (!feedContainers.length) return;

  try {
    const res = await fetch('/api/trajes');
    if (!res.ok) return;
    const trajes = await res.json();
    if (!Array.isArray(trajes) || trajes.length === 0) return;

    feedContainers.forEach(container => {
      const hasStaticPlaceholders = container.querySelectorAll('a[href*="fenix-solar"], a[href*="guerrero-profundidades"]').length > 0;
      if (hasStaticPlaceholders || container.children.length === 0) {
        container.innerHTML = '';
        trajes.forEach((traje, idx) => {
          const card = document.createElement('article');
          card.className = `tarjeta-feed immersive-traje-card reveal visible delay-${(idx % 3) + 1}`;
          card.setAttribute('data-id', traje.id);
          card.setAttribute('data-genero', traje.genero || 'Femenino');

          const foto = escapeHTML(resolverRutaImagen(traje.foto_url || ''));
          const comparsero = escapeHTML(traje.comparsero || 'Traje de Carnaval');
          const comparsa = escapeHTML(traje.comparsa || 'Comparsa');
          const genero = escapeHTML(traje.genero || 'Oficial');
          const isDestaque = traje.es_destaque || traje.es_obra_maestra;
          const obraBadge = isDestaque ? ' • ★ Destaque' : '';
          const desc = escapeHTML(traje.descripcion || traje.materiales || 'Vestuario oficial de carnaval realizado y coordinado integralmente en el taller de Hugo Fernández.');

          const isVideo = foto.toLowerCase().includes('.mp4') || foto.toLowerCase().includes('/video');
          const hasBoceto = traje.enlace_boceto && String(traje.enlace_boceto).trim().length > 0;
          const safeBoceto = hasBoceto ? escapeHTML(resolverRutaImagen(traje.enlace_boceto)) : '';

          let feedMediaHtml = '';
          if (isVideo) {
            feedMediaHtml = `
              <video controls width="100%" class="destaque-video-player" style="height: 100%; object-fit: cover;" preload="metadata">
                <source src="${foto}" type="video/mp4">
              </video>
            `;
          } else if (hasBoceto) {
            feedMediaHtml = `
              <div class="ba-slider-container" data-ba-slider style="height: 100%;">
                <img src="${foto}" alt="Después: ${comparsero}" class="ba-img ba-after-img" loading="lazy">
                <div class="ba-before-wrapper">
                  <img src="${safeBoceto}" alt="Antes: Boceto ${comparsero}" class="ba-img ba-before-img" loading="lazy">
                </div>
                <span class="ba-badge ba-badge-before">Antes</span>
                <span class="ba-badge ba-badge-after">Después</span>
                <div class="ba-divider"><div class="ba-handle"><span>↔</span></div></div>
                <input type="range" min="0" max="100" value="50" class="ba-range-input" aria-label="Deslizar para comparar">
              </div>
            `;
          } else {
            feedMediaHtml = `<img src="${foto}" alt="${comparsero} - ${comparsa}" loading="lazy">`;
          }

          card.innerHTML = `
            <div class="immersive-traje-img-box">
              ${feedMediaHtml}
            </div>
            <div class="immersive-traje-overlay">
              <div class="immersive-info">
                <span class="immersive-badge">${genero} • ${comparsa}${obraBadge}</span>
                <h3 class="immersive-title">${comparsero}</h3>
                <p class="immersive-desc">${desc}</p>
              </div>
              <div class="immersive-action">
                <a href="/traje/${traje.id}" class="btn-hero-primary" style="padding: 0.5rem 1rem; font-size: 0.85rem;">
                  Consultar Ficha Técnica →
                </a>
              </div>
            </div>
          `;
          container.appendChild(card);
        });
        initImageComparison();
      }
    });
  } catch (err) {
    console.warn('Error al cargar feed móvil de trajes:', err);
  }
}

/**
 * Interactividad en la Galería del Traje (templates/traje-detalle.html)
 * Al hacer clic en cualquiera de las miniaturas, la imagen principal y su etiqueta se actualizan
 * dinámicamente con una transición suave.
 */
function initTrajeGalleryThumbs() {
  const mainImage = document.querySelector('.gallery-main img');
  const badgeTxt = document.getElementById('gallery-badge-txt');
  const thumbCards = document.querySelectorAll('.gallery-thumb-item');

  if (!mainImage || !thumbCards.length) return;

  thumbCards.forEach(card => {
    card.addEventListener('click', () => {
      const thumb = card.querySelector('img');
      const caption = card.querySelector('.thumb-caption');
      if (!thumb) return;

      const newSrc = thumb.getAttribute('src');
      const newAlt = thumb.getAttribute('alt');
      const newTitle = caption ? caption.textContent.trim() : newAlt;

      if (!newSrc || mainImage.getAttribute('src') === newSrc) return;

      mainImage.style.opacity = '0.3';
      mainImage.style.transform = 'scale(0.98)';

      setTimeout(() => {
        mainImage.setAttribute('src', newSrc);
        if (newAlt) mainImage.setAttribute('alt', newAlt);
        if (badgeTxt && newTitle) badgeTxt.textContent = newTitle;
        mainImage.style.opacity = '1';
        mainImage.style.transform = 'scale(1)';
      }, 180);
    });
  });
}

/**
 * Soporte Mobile & UX:
 * Apertura/cierre de la barra de navegación en pantallas móviles y control de dropdowns
 */
function initMobileMenu() {
  const toggleBtn = document.querySelector('.mobile-toggle');
  const mainNav = document.querySelector('.main-nav');
  const dropdowns = document.querySelectorAll('.dropdown');

  if (toggleBtn && mainNav) {
    toggleBtn.addEventListener('click', () => {
      mainNav.classList.toggle('nav-open');
      const expanded = toggleBtn.getAttribute('aria-expanded') === 'true';
      toggleBtn.setAttribute('aria-expanded', String(!expanded));
    });
  }

  // Permite abrir submenús al tocar en dispositivos táctiles/móviles
  dropdowns.forEach(dropdown => {
    const trigger = dropdown.querySelector('.nav-link');
    if (trigger) {
      trigger.addEventListener('click', (e) => {
        if (window.innerWidth <= 768) {
          e.preventDefault();
          dropdown.classList.toggle('mobile-expanded');
        }
      });
    }
  });

  // Cerrar menú móvil al hacer click fuera
  document.addEventListener('click', (e) => {
    if (mainNav && mainNav.classList.contains('nav-open')) {
      if (!mainNav.contains(e.target) && !toggleBtn.contains(e.target)) {
        mainNav.classList.remove('nav-open');
        if (toggleBtn) toggleBtn.setAttribute('aria-expanded', 'false');
      }
    }
  });
}

/**
 * Vidriera Interactiva - Slider Boceto (Antes) vs Traje (Después)
 * Control interactivo con clip-path y soporte fluido para cursor, mouse drag y touch móvil.
 */
function initImageComparison() {
  // Manejo de todos los sliders Antes / Después ([data-ba-slider] y .ba-slider-container)
  const sliders = document.querySelectorAll('[data-ba-slider], .ba-slider-container');
  sliders.forEach(container => {
    const range = container.querySelector('.ba-range-input, input[type="range"]');
    const beforeWrapper = container.querySelector('.ba-before-wrapper');
    const divider = container.querySelector('.ba-divider');

    const update = (val) => {
      const clamped = Math.max(0, Math.min(100, parseFloat(val) || 50));
      container.style.setProperty('--ba-pos', `${clamped}%`);
      if (beforeWrapper) {
        beforeWrapper.style.clipPath = `polygon(0 0, ${clamped}% 0, ${clamped}% 100%, 0 100%)`;
        beforeWrapper.style.webkitClipPath = `polygon(0 0, ${clamped}% 0, ${clamped}% 100%, 0 100%)`;
      }
      if (divider) {
        divider.style.left = `${clamped}%`;
      }
    };

    if (range) {
      range.addEventListener('input', (e) => update(e.target.value));
      range.addEventListener('change', (e) => update(e.target.value));
      update(range.value || 50);
    }
  });

  // Compatibilidad con contenedor individual legado
  const legacyContainer = document.querySelector('.image-comparison-container');
  const legacySlider = document.querySelector('.comparison-range-slider');
  const legacyOverlay = document.querySelector('.comparison-after');
  const legacyDivider = document.querySelector('.comparison-divider');

  if (legacyContainer && legacySlider && legacyOverlay && legacyDivider) {
    const updateLegacy = (value) => {
      const clampedValue = Math.max(0, Math.min(100, parseFloat(value) || 50));
      legacyOverlay.style.width = `${clampedValue}%`;
      legacyDivider.style.left = `${clampedValue}%`;
    };
    legacySlider.addEventListener('input', (e) => updateLegacy(e.target.value));
    legacySlider.addEventListener('change', (e) => updateLegacy(e.target.value));
    updateLegacy(legacySlider.value || 50);
  }
}

/**
 * FASE 7: Sistema de Comentarios - Carga dinámica y envío asíncrono en Ficha de Traje
 */
async function initComentariosTraje() {
  const listaContainer = document.getElementById('comentarios-lista');
  const form = document.getElementById('form-comentario');
  if (!listaContainer || !form) return;

  const urlParams = new URLSearchParams(window.location.search);
  const trajeId = urlParams.get('id') || 1;

  // Carga inicial de comentarios del traje
  await cargarComentariosDeTraje(trajeId);

  // Manejo del formulario de envío
  if (!form.dataset.listenerBound) {
    form.dataset.listenerBound = 'true';
    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      const usuarioInput = document.getElementById('comentario-usuario');
      const textoInput = document.getElementById('comentario-texto');
      const statusEl = document.getElementById('comentario-status');
      const submitBtn = document.getElementById('btn-enviar-comentario');

      const usuario = usuarioInput.value.trim();
      const texto = textoInput.value.trim();

      if (!usuario || !texto) return;

      submitBtn.disabled = true;
      submitBtn.textContent = 'Enviando...';
      if (statusEl) statusEl.textContent = '';

      try {
        const response = await fetch('/api/comentarios', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            traje_id: parseInt(trajeId, 10),
            usuario: usuario,
            texto: texto
          })
        });

        if (!response.ok) {
          throw new Error(`Error en el servidor: ${response.status}`);
        }

        textoInput.value = '';
        if (statusEl) {
          statusEl.style.color = '#2ecc71';
          statusEl.textContent = '✓ Comentario publicado con éxito';
        }

        // Actualizar la lista en el DOM sin recargar la página
        await cargarComentariosDeTraje(trajeId);

        setTimeout(() => {
          if (statusEl) statusEl.textContent = '';
        }, 3500);

      } catch (err) {
        console.error('Error al enviar comentario:', err);
        if (statusEl) {
          statusEl.style.color = '#e74c3c';
          statusEl.textContent = '⚠️ No se pudo publicar el comentario. Intenta nuevamente.';
        }
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Enviar Comentario →';
      }
    });
  }
}

/**
 * Consulta el endpoint GET /api/comentarios/<traje_id> y actualiza el DOM
 */
async function cargarComentariosDeTraje(trajeId) {
  const listaContainer = document.getElementById('comentarios-lista');
  const contadorEl = document.getElementById('comentarios-contador');
  if (!listaContainer) return;

  try {
    const res = await fetch(`/api/comentarios/${trajeId}`);
    if (!res.ok) throw new Error('Error al consultar comentarios');

    const comentarios = await res.json();
    if (contadorEl) contadorEl.textContent = comentarios.length;

    if (comentarios.length === 0) {
      listaContainer.innerHTML = `
        <div class="comentarios-vacio">
          <p>Aún no hay comentarios sobre este traje.</p>
          <span style="font-size: 0.85rem; color: var(--dorado-solido);">¡Sé el primero en compartir tu opinión o recuerdo del corsódromo!</span>
        </div>
      `;
      return;
    }

    listaContainer.innerHTML = comentarios.map(com => `
      <article class="comentario-item" id="comentario-${com.id}">
        <div class="comentario-item-header">
          <span class="comentario-item-user">
            <span>🎭</span> ${escapeHTML(com.usuario)}
          </span>
          <span class="comentario-item-fecha">${escapeHTML(com.fecha || '')}</span>
        </div>
        <p class="comentario-item-texto">${escapeHTML(com.texto)}</p>
      </article>
    `).join('');

  } catch (err) {
    console.error('Error al cargar comentarios:', err);
    listaContainer.innerHTML = `
      <div class="comentarios-vacio" style="border-color: rgba(231, 76, 60, 0.3);">
        <p style="color: #e74c3c;">No se pudieron cargar los comentarios.</p>
      </div>
    `;
  }
}

/**
 * ============================================================================
 * FASE 14 (MÓDULO 3: LIBRE ALBEDRÍO UX - DECISIÓN AUTÓNOMA DOCUMENTADA)
 * ============================================================================
 * Mejoras Autónomas implementadas para potenciar la inmersión del "Carnaval Correntino":
 * 1. Contador Regresivo en Tiempo Real en el Header (`initCarnavalCountdown`):
 *    Calcula dinámicamente el tiempo restante para la noche inaugural de los
 *    Carnavales Oficiales de Corrientes en el Corsódromo "Nolo Alías" (último
 *    viernes de enero de la próxima edición) e inyecta una barra superior
 *    no destructiva con acceso directo a `/comunidad/subir`.
 * 2. Animación CSS de "Brillo / Purpurina" (`destelloPurpurinaCarnaval` en `estilos.css`):
 *    Efecto especular diagonal sobre las tarjetas `.coordinacion-card` y
 *    `.obra-maestra-glitter` que simula el reflejo de los cristales boreales
 *    bajo los reflectores del corsódromo.
 * 3. Metadatos Open Graph (OG) Enriquecidos + Botón WhatsApp (`traje-detalle.html`):
 *    Renderizado SSR de etiquetas `og:title`, `og:description`, `og:image`,
 *    `og:site_name` y `og:type` para que al compartir cualquier traje por
 *    WhatsApp se previsualice automáticamente su foto, figura y comparsa.
 */
function initCarnavalCountdown() {
  const header = document.querySelector('.site-header');
  if (!header) return;

  // Determinar la fecha de la noche inaugural de Carnaval en el Corsódromo Nolo Alías 2027
  const obtenerFechaProximoCarnaval = () => {
    const ahora = new Date();
    // Noche inaugural Nolo Alías 2027: 29 de Enero de 2027 a las 22:00 hs (GMT-3)
    let anioObjetivo = Math.max(2027, ahora.getFullYear());
    let fechaCarnaval = new Date(`${anioObjetivo}-01-29T22:00:00-03:00`);
    if (isNaN(fechaCarnaval.getTime())) {
      fechaCarnaval = new Date(anioObjetivo, 0, 29, 22, 0, 0);
    }
    if (ahora.getTime() >= fechaCarnaval.getTime()) {
      anioObjetivo += 1;
      fechaCarnaval = new Date(`${anioObjetivo}-01-29T22:00:00-03:00`);
      if (isNaN(fechaCarnaval.getTime())) {
        fechaCarnaval = new Date(anioObjetivo, 0, 29, 22, 0, 0);
      }
    }
    return { fecha: fechaCarnaval, anio: anioObjetivo };
  };

  const { fecha: targetDate, anio: edicionAnio } = obtenerFechaProximoCarnaval();

  let bar = document.querySelector('.carnaval-countdown-bar');
  if (!bar) {
    bar = document.createElement('div');
    bar.className = 'carnaval-countdown-bar';
    bar.setAttribute('aria-label', 'Cuenta regresiva para el próximo Carnaval Correntino');
    bar.innerHTML = `
      <span class="carnaval-countdown-label">
        <span>🎭</span> Rumbo al Carnaval de Corrientes ${edicionAnio} (Nolo Alías):
      </span>
      <div class="carnaval-countdown-timer" id="carnaval-countdown-timer">
        <span class="countdown-unit"><span id="cd-dias">00</span><small>d</small></span>
        <span class="countdown-unit"><span id="cd-horas">00</span><small>h</small></span>
        <span class="countdown-unit"><span id="cd-min">00</span><small>m</small></span>
        <span class="countdown-unit"><span id="cd-seg">00</span><small>s</small></span>
      </div>
      <a href="/comunidad/subir" class="carnaval-countdown-cta">
        ✨ SUBÍ TU TRAJE
      </a>
    `;
    header.insertBefore(bar, header.firstChild);
  }

  const actualizarReloj = () => {
    const diff = Math.max(0, targetDate.getTime() - Date.now());
    const dias = Math.floor(diff / (1000 * 60 * 60 * 24));
    const horas = Math.floor((diff / (1000 * 60 * 60)) % 24);
    const min = Math.floor((diff / (1000 * 60)) % 60);
    const seg = Math.floor((diff / 1000) % 60);

    const diasEl = document.getElementById('cd-dias') || bar.querySelector('#cd-dias');
    const horasEl = document.getElementById('cd-horas') || bar.querySelector('#cd-horas');
    const minEl = document.getElementById('cd-min') || bar.querySelector('#cd-min');
    const segEl = document.getElementById('cd-seg') || bar.querySelector('#cd-seg');

    if (diasEl) diasEl.textContent = String(dias).padStart(2, '0');
    if (horasEl) horasEl.textContent = String(horas).padStart(2, '0');
    if (minEl) minEl.textContent = String(min).padStart(2, '0');
    if (segEl) segEl.textContent = String(seg).padStart(2, '0');
  };

  actualizarReloj();
  setInterval(actualizarReloj, 1000);
}

/**
 * Carrusel de Trayectoria en el Carnaval (Multi-Vista Responsiva)
 * - Muestra 3 comparsas por vista en pantallas grandes (> 960px), 2 en tablets (641-960px) y 1 en móviles (<= 640px).
 * - Ordenado desde la consulta SQL de más reciente/actual a más antigua.
 * - Flechas de navegación Anterior / Siguiente (#btn-tray-prev, #btn-tray-next), indicador dinámico y modal Glassmorphism.
 */
function initTrayectoriaInteractiva() {
  const container = document.getElementById('trayectoria-container') || document.querySelector('.trayectoria-slider-container');
  if (!container) return;

  const slides = Array.from(container.querySelectorAll('.comparsa-btn-card, .trayectoria-slide, .comparsa-compact-card'));
  if (!slides.length) return;

  const prevBtn = document.getElementById('btn-tray-prev');
  const nextBtn = document.getElementById('btn-tray-next');
  const indicator = document.getElementById('tray-indicator');

  let currentIndex = 0;
  const totalSlides = slides.length;

  function getItemsPerView() {
    if (window.innerWidth > 960) return Math.min(3, totalSlides);
    if (window.innerWidth > 640) return Math.min(2, totalSlides);
    return 1;
  }

  function renderSlide(index) {
    const itemsPerView = getItemsPerView();
    const maxStartIndex = Math.max(0, totalSlides - itemsPerView);

    if (index < 0) index = 0;
    if (index > maxStartIndex) index = maxStartIndex;
    currentIndex = index;

    slides.forEach((slide, idx) => {
      const isVisible = idx >= currentIndex && idx < currentIndex + itemsPerView;
      if (isVisible) {
        slide.style.display = 'flex';
        slide.classList.add('active');
        slide.setAttribute('aria-hidden', 'false');
      } else {
        slide.style.display = 'none';
        slide.classList.remove('active');
        slide.setAttribute('aria-hidden', 'true');
      }
    });

    if (indicator) {
      if (itemsPerView > 1) {
        const endIdx = Math.min(currentIndex + itemsPerView, totalSlides);
        indicator.textContent = `${currentIndex + 1} – ${endIdx} de ${totalSlides}`;
      } else {
        indicator.textContent = `${currentIndex + 1} de ${totalSlides}`;
      }
    }

    if (prevBtn) {
      prevBtn.disabled = (currentIndex <= 0);
      prevBtn.setAttribute('aria-disabled', String(currentIndex <= 0));
    }
    if (nextBtn) {
      nextBtn.disabled = (currentIndex >= maxStartIndex);
      nextBtn.setAttribute('aria-disabled', String(currentIndex >= maxStartIndex));
    }
  }

  if (prevBtn && !prevBtn.dataset.listenerBound) {
    prevBtn.dataset.listenerBound = 'true';
    prevBtn.addEventListener('click', (e) => {
      e.preventDefault();
      if (currentIndex > 0) {
        renderSlide(currentIndex - 1);
      }
    });
  }

  if (nextBtn && !nextBtn.dataset.listenerBound) {
    nextBtn.dataset.listenerBound = 'true';
    nextBtn.addEventListener('click', (e) => {
      e.preventDefault();
      const maxStartIndex = Math.max(0, totalSlides - getItemsPerView());
      if (currentIndex < maxStartIndex) {
        renderSlide(currentIndex + 1);
      }
    });
  }

  // Recalcular vista cuando cambia el tamaño de pantalla (Mobile / Tablet / Desktop 3 columnas)
  window.addEventListener('resize', () => {
    renderSlide(currentIndex);
  }, { passive: true });

  // Soporte de gestos táctiles (Swipe) en dispositivos móviles
  let touchStartX = 0;
  let touchEndX = 0;
  container.addEventListener('touchstart', (e) => {
    touchStartX = e.changedTouches[0].screenX;
  }, { passive: true });

  container.addEventListener('touchend', (e) => {
    touchEndX = e.changedTouches[0].screenX;
    const diff = touchStartX - touchEndX;
    const maxStartIndex = Math.max(0, totalSlides - getItemsPerView());
    if (Math.abs(diff) > 40) {
      if (diff > 0 && currentIndex < maxStartIndex) {
        renderSlide(currentIndex + 1);
      } else if (diff < 0 && currentIndex > 0) {
        renderSlide(currentIndex - 1);
      }
    }
  }, { passive: true });

  // Render inicial mostrando las primeras 3 comparsas en escritorio (de más reciente/actual a más antigua)
  renderSlide(0);

  // Modal Glassmorphism de Comparsa
  const modal = document.getElementById('modal-comparsa');
  if (!modal) return;

  const closeBtn = document.getElementById('modal-comparsa-close');
  const cerrarBtn = document.getElementById('modal-btn-cerrar');
  const titleEl = document.getElementById('modal-comp-title');
  const badgeEl = document.getElementById('modal-comp-badge');
  const ciudadEl = document.getElementById('modal-comp-ciudad');
  const rolEl = document.getElementById('modal-comp-rol');
  const descEl = document.getElementById('modal-comp-desc');
  const linkEl = document.getElementById('modal-comp-link');

  function abrirModal(card) {
    const nombre = card.dataset.nombre || 'Comparsa';
    const anios = card.dataset.anios ? ` • ${card.dataset.anios}` : '';
    const ciudad = (card.dataset.ciudad || '') + anios;
    const rol = card.dataset.rol || 'Dirección Técnica';
    const desc = card.dataset.desc || '';

    if (titleEl) titleEl.textContent = nombre;
    if (badgeEl) badgeEl.textContent = card.dataset.anios || 'Trayectoria';
    if (ciudadEl) ciudadEl.textContent = ciudad;
    if (rolEl) rolEl.textContent = rol;
    if (descEl) descEl.textContent = desc;

    if (linkEl) {
      linkEl.href = `/comparsa/${encodeURIComponent(nombre)}`;
    }

    modal.classList.add('active');
    modal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  }

  function cerrarModal() {
    modal.classList.remove('active');
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  }

  slides.forEach(card => {
    if (!card.dataset.modalBound) {
      card.dataset.modalBound = 'true';
      card.addEventListener('click', () => abrirModal(card));
      card.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          abrirModal(card);
        }
      });
    }
  });

  if (closeBtn && !closeBtn.dataset.listenerBound) {
    closeBtn.dataset.listenerBound = 'true';
    closeBtn.addEventListener('click', cerrarModal);
  }
  if (cerrarBtn && !cerrarBtn.dataset.listenerBound) {
    cerrarBtn.dataset.listenerBound = 'true';
    cerrarBtn.addEventListener('click', cerrarModal);
  }

  if (!modal.dataset.listenerBound) {
    modal.dataset.listenerBound = 'true';
    modal.addEventListener('click', (e) => {
      if (e.target === modal) cerrarModal();
    });
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.classList.contains('active')) {
      cerrarModal();
    }
    // Navegación con teclado si el modal está cerrado
    if (!modal.classList.contains('active')) {
      const maxStartIndex = Math.max(0, totalSlides - getItemsPerView());
      if (e.key === 'ArrowLeft' && currentIndex > 0) {
        renderSlide(currentIndex - 1);
      } else if (e.key === 'ArrowRight' && currentIndex < maxStartIndex) {
        renderSlide(currentIndex + 1);
      }
    }
  });
}

/**
 * Modal Glassmorphism para Perfil Técnico & Aptitudes Completas del CV
 */
function initModalPerfilTecnico() {
  const btnAbrir = document.getElementById('btn-perfil-tecnico') || document.getElementById('btn-abrir-perfil-tecnico');
  const modal = document.getElementById('modal-perfil-tecnico');
  if (!btnAbrir || !modal) return;

  const closeBtn = document.getElementById('modal-perfil-close');
  const cerrarBtn = document.getElementById('modal-perfil-btn-cerrar');

  function abrirModal() {
    modal.classList.add('active');
    modal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  }

  function cerrarModal() {
    modal.classList.remove('active');
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  }

  btnAbrir.addEventListener('click', (e) => {
    e.preventDefault();
    abrirModal();
  });

  if (closeBtn) closeBtn.addEventListener('click', cerrarModal);
  if (cerrarBtn) cerrarBtn.addEventListener('click', cerrarModal);

  modal.addEventListener('click', (e) => {
    if (e.target === modal) cerrarModal();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.classList.contains('active')) {
      cerrarModal();
    }
  });
}

/**
 * Modal Interactivo para Aptitudes del Taller & Técnicas de Confección
 * Abre con el botón "Explorar materiales y técnicas" y exhibe tarjetas oscuras con bordes dorados
 */
function initModalAptitudesTaller() {
  const btnAbrir = document.getElementById('btn-explorar-tecnicas');
  const modal = document.getElementById('modal-aptitudes-taller');
  if (!btnAbrir || !modal) return;

  const closeBtn = document.getElementById('modal-aptitudes-close');
  const cerrarBtn = document.getElementById('modal-aptitudes-btn-cerrar');

  function abrirModal() {
    modal.classList.add('active');
    modal.setAttribute('aria-hidden', 'false');
    btnAbrir.setAttribute('aria-expanded', 'true');
    document.body.style.overflow = 'hidden';
  }

  function cerrarModal() {
    modal.classList.remove('active');
    modal.setAttribute('aria-hidden', 'true');
    btnAbrir.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  }

  btnAbrir.addEventListener('click', (e) => {
    e.preventDefault();
    abrirModal();
  });

  if (closeBtn) closeBtn.addEventListener('click', cerrarModal);
  if (cerrarBtn) cerrarBtn.addEventListener('click', cerrarModal);

  modal.addEventListener('click', (e) => {
    if (e.target === modal) cerrarModal();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.classList.contains('active')) {
      cerrarModal();
    }
  });
}




