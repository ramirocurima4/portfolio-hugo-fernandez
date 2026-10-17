/**
 * Hugo Fernández Arte Creativo - Ficha de Detalle Dinámica, Comentarios & Social Sharing (FASE 8)
 * Conexión de pages/traje-detalle.html y templates/traje-detalle.html con Flask y SQLite.
 */

document.addEventListener('DOMContentLoaded', () => {
  initFichaDetalleAutonoma();
  initComentariosTraje();
});

/**
 * Detecta de forma inteligente el ID del traje actual:
 * 1. Desde la ruta amigable SSR (/traje/<id>)
 * 2. Desde el atributo data-traje-id del contenedor HTML
 * 3. Desde el parámetro de consulta ?id=<id>
 * 4. Por defecto: '1'
 */
function obtenerTrajeIdActual() {
  const match = window.location.pathname.match(/\/traje\/(\d+)/);
  if (match && match[1]) {
    return match[1];
  }
  const showcase = document.querySelector('[data-traje-id]');
  if (showcase && showcase.getAttribute('data-traje-id')) {
    const dataId = showcase.getAttribute('data-traje-id').trim();
    if (dataId && dataId !== '{{ traje.id }}') {
      return dataId;
    }
  }
  const urlParams = new URLSearchParams(window.location.search);
  const paramId = urlParams.get('id');
  if (paramId) {
    return paramId;
  }
  return '1';
}

/**
 * Resuelve rutas relativas o absolutas de imágenes según el contexto de la página
 */
function resolverRuta(url) {
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
 * Función auxiliar para sanitizar cadenas HTML
 */
function escapeTxt(str) {
  if (typeof str !== 'string') return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * Consume los datos del traje individual e hidrata los elementos del DOM si se navega de forma estática
 */
async function initFichaDetalleAutonoma() {
  const isDetalle = window.location.pathname.includes('traje-detalle.html') || 
                    window.location.pathname.startsWith('/traje/') ||
                    Boolean(document.getElementById('detalle-titulo') || document.getElementById('traje-title-txt'));
  if (!isDetalle) return;

  const urlParams = new URLSearchParams(window.location.search);
  const idParam = urlParams.get('id');

  // Si estamos en la ruta SSR /traje/<id> y no hay query param ?id=, los datos ya vienen del servidor
  if (!idParam && window.location.pathname.startsWith('/traje/')) {
    return;
  }

  const trajeId = idParam || obtenerTrajeIdActual();
  if (!trajeId) return;

  let traje = null;

  // 1. Intentar leer desde sessionStorage (precargado desde la grilla)
  try {
    const cached = sessionStorage.getItem('selectedTraje');
    if (cached) {
      const parsed = JSON.parse(cached);
      if (String(parsed.id) === String(trajeId)) {
        traje = parsed;
      }
    }
  } catch (e) {
    console.warn('Error leyendo sessionStorage:', e);
  }

  // 2. Si no estaba en caché, consultar al endpoint específico /api/trajes/<id>
  if (!traje) {
    try {
      const res = await fetch(`/api/trajes/${trajeId}`);
      if (res.ok) {
        traje = await res.json();
      } else {
        const resList = await fetch('/api/trajes');
        if (resList.ok) {
          const list = await resList.json();
          traje = list.find(t => String(t.id) === String(trajeId));
        }
      }
    } catch (e) {
      console.error('Error al obtener datos del traje:', e);
    }
  }

  if (!traje) return;

  // Inyección en el DOM para entornos estáticos o hidratación en cliente
  const tituloEl = document.getElementById('detalle-titulo') || document.getElementById('traje-title-txt');
  const imagenEl = document.getElementById('detalle-imagen') || document.getElementById('main-preview-img');
  const materialesEl = document.getElementById('detalle-materiales') || document.getElementById('materiales-container');
  const badgeRol = document.getElementById('traje-badge-rol');
  const metaComparsa = document.getElementById('meta-comparsa');
  const metaRol = document.getElementById('meta-rol');
  const rImg = document.getElementById('comparison-real-img');

  if (tituloEl) {
    tituloEl.textContent = `${traje.comparsero} - ${traje.comparsa}`;
  }

  if (imagenEl && traje.foto_url) {
    imagenEl.src = resolverRuta(traje.foto_url);
    imagenEl.alt = `${traje.comparsero} (${traje.comparsa})`;
  }

  if (materialesEl && traje.materiales) {
    materialesEl.innerHTML = '';
    const clean = traje.materiales.replace(/\.$/, '');
    const lista = clean.split(',').map(m => m.trim()).filter(Boolean);

    materialesEl.innerHTML = lista.map((m, idx) => `
      <div class="material-tag reveal visible delay-${(idx % 3) + 1}">
        <span class="tag-label">✦ Material</span>
        <span class="tag-quantity">${escapeTxt(m)}</span>
      </div>
    `).join('');
  }

  if (badgeRol) badgeRol.textContent = `${traje.genero} • ${traje.comparsa}`;
  if (metaComparsa) metaComparsa.textContent = traje.comparsa;
  if (metaRol) metaRol.textContent = `${traje.genero} (${traje.comparsa})`;
  if (rImg && traje.foto_url) rImg.src = resolverRuta(traje.foto_url);
}

/**
 * FASE 7: Sistema de Comentarios - Carga dinámica y envío asíncrono
 */
async function initComentariosTraje() {
  const listaContainer = document.getElementById('comentarios-lista');
  const form = document.getElementById('form-comentario');
  if (!listaContainer || !form) return;

  const trajeId = obtenerTrajeIdActual();

  // Carga inicial de comentarios
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
      statusEl.textContent = '';

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

        const data = await response.json();
        
        // Limpiar campos y dar feedback
        textoInput.value = '';
        statusEl.style.color = '#2ecc71';
        statusEl.textContent = '✓ Comentario publicado con éxito';

        // Actualizar la lista en el DOM sin recargar la página
        await cargarComentariosDeTraje(trajeId);

        setTimeout(() => {
          statusEl.textContent = '';
        }, 3500);

      } catch (err) {
        console.error('Error al enviar comentario:', err);
        statusEl.style.color = '#e74c3c';
        statusEl.textContent = '⚠️ No se pudo publicar el comentario. Intenta nuevamente.';
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
            <span>🎭</span> ${escapeTxt(com.usuario)}
          </span>
          <span class="comentario-item-fecha">${escapeTxt(com.fecha || '')}</span>
        </div>
        <p class="comentario-item-texto">${escapeTxt(com.texto)}</p>
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
 * ==============================================================================
 * FASE 8: BOTÓN "COMPARTIR TRAJE" (WEB SHARE API CON FALLBACK AL PORTAPAPELES)
 * ==============================================================================
 */
async function compartirTraje() {
  const shareData = {
    title: document.title,
    text: '¡Mira este increíble traje de carnaval coordinado por Hugo Fernández!',
    url: window.location.href
  };

  const feedbackEl = document.getElementById('share-feedback');

  const mostrarFeedback = (mensaje = '✓ ¡Enlace copiado al portapapeles!') => {
    if (feedbackEl) {
      feedbackEl.textContent = mensaje;
      feedbackEl.style.display = 'inline-block';
      feedbackEl.classList.add('visible');
      setTimeout(() => {
        feedbackEl.style.display = 'none';
        feedbackEl.classList.remove('visible');
      }, 3500);
    }
  };

  // 1. Probar Web Share API (Navegadores móviles y compatibles)
  if (navigator.share) {
    try {
      await navigator.share(shareData);
      return;
    } catch (err) {
      // Si el usuario canceló el diálogo nativo (AbortError), no hacemos nada
      if (err.name === 'AbortError') {
        return;
      }
      console.warn('navigator.share falló, activando fallback:', err);
    }
  }

  // 2. Fallback a portapapeles (Desktop y navegadores sin Share API)
  copiarEnlaceAlPortapapeles(mostrarFeedback);
}

/**
 * Copia la URL actual al portapapeles del sistema y activa el feedback visual
 */
function copiarEnlaceAlPortapapeles(callbackFeedback) {
  const url = window.location.href;

  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(url)
      .then(() => {
        if (callbackFeedback) callbackFeedback('✓ ¡Enlace copiado al portapapeles!');
      })
      .catch((err) => {
        console.warn('Fallo navigator.clipboard.writeText, probando input auxiliar:', err);
        fallbackCopiarInput(url, callbackFeedback);
      });
  } else {
    fallbackCopiarInput(url, callbackFeedback);
  }
}

/**
 * Fallback compatible para navegadores antiguos o entornos sin navigator.clipboard
 */
function fallbackCopiarInput(texto, callbackFeedback) {
  try {
    const tempInput = document.createElement('input');
    tempInput.value = texto;
    tempInput.style.position = 'fixed';
    tempInput.style.top = '-9999px';
    tempInput.style.left = '-9999px';
    document.body.appendChild(tempInput);
    tempInput.focus();
    tempInput.select();
    const successful = document.execCommand('copy');
    document.body.removeChild(tempInput);

    if (successful && callbackFeedback) {
      callbackFeedback('✓ ¡Enlace copiado al portapapeles!');
    } else if (callbackFeedback) {
      callbackFeedback('⚠️ Enlace: ' + texto);
    }
  } catch (err) {
    console.error('Error al copiar enlace en fallback:', err);
    if (callbackFeedback) {
      callbackFeedback('⚠️ Enlace: ' + texto);
    }
  }
}

// Exponer en window para que esté disponible en el atributo inline onclick="compartirTraje()"
window.compartirTraje = compartirTraje;
window.copiarEnlaceAlPortapapeles = copiarEnlaceAlPortapapeles;
window.obtenerTrajeIdActual = obtenerTrajeIdActual;
