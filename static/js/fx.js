/**
 * FX.JS — Capa de efectos de vanguardia (vanilla, sin dependencias)
 * ----------------------------------------------------------------------------
 * Ganchos declarativos (se activan por atributo; no hay que tocar JS al sumar páginas):
 *   [data-split]            titulares con entrada palabra por palabra
 *   [data-reveal]           revelado al hacer scroll (valores: left | right | zoom)
 *   [data-parallax="0.1"]   desplazamiento parallax (usa la propiedad CSS `translate`)
 *   [data-parallax-img]     parallax interno de una imagen dentro de su marco
 *   [data-tilt]             inclinación 3D siguiendo el cursor
 *   [data-spot]             foco de luz que sigue al cursor (variables --mx / --my)
 *   [data-magnetic]         botones magnéticos
 *   [data-rail]             riel horizontal arrastrable
 *   [data-count="123"]      contador animado
 * API pública: window.HFX.{ refresh, observe, splitText, toast }
 * Todo respeta prefers-reduced-motion y se degrada sin romper el contenido.
 */
(() => {
  'use strict';
  if (window.HFX) return;

  const root = document.documentElement;
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  const lerp = (a, b, t) => a + (b - a) * t;
  const clamp = (v, min, max) => Math.min(max, Math.max(min, v));
  const safe = (fn, name) => { try { fn(); } catch (err) { console.warn(`[HFX:${name}]`, err); } };
  const curtainActive = root.classList.contains('has-curtain');

  /* ── Telón: recordar que ya se mostró en esta sesión ─────────────────── */
  function initCurtain() {
    if (!curtainActive) return;
    try { sessionStorage.setItem('hf_telon', '1'); } catch (e) { /* modo privado */ }
  }

  /* ── Hilo de progreso de lectura ─────────────────────────────────────── */
  function initProgress() {
    const bar = document.querySelector('.fx-progress i');
    if (!bar) return;
    let ticking = false;
    const update = () => {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      bar.style.setProperty('--p', max > 0 ? clamp(window.scrollY / max, 0, 1).toFixed(4) : 0);
      ticking = false;
    };
    window.addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
    window.addEventListener('resize', update, { passive: true });
    update();
  }

  /* ── Texto partido por palabras (conserva <em>, <strong>, etc.) ──────── */
  function splitText(el) {
    if (!el || el.classList.contains('is-split')) return;
    let idx = 0;
    const label = el.textContent.replace(/\s+/g, ' ').trim();
    const walk = (node) => {
      Array.from(node.childNodes).forEach((child) => {
        if (child.nodeType === Node.TEXT_NODE) {
          const frag = document.createDocumentFragment();
          child.textContent.split(/(\s+)/).forEach((part) => {
            if (!part) return;
            if (/^\s+$/.test(part)) { frag.appendChild(document.createTextNode(' ')); return; }
            const w = document.createElement('span');
            w.className = 'w';
            w.setAttribute('aria-hidden', 'true');
            const wi = document.createElement('span');
            wi.className = 'wi';
            wi.style.setProperty('--i', idx++);
            wi.textContent = part;
            w.appendChild(wi);
            frag.appendChild(w);
          });
          child.replaceWith(frag);
        } else if (child.nodeType === Node.ELEMENT_NODE) {
          walk(child);
        }
      });
    };
    el.setAttribute('aria-label', label);
    walk(el);
    el.classList.add('is-split');
  }

  /* ── Observador de revelado (split + data-reveal) ────────────────────── */
  let revealObserver = null;
  function observe(el) {
    if (!el) return;
    if (reduce || !('IntersectionObserver' in window)) {
      el.classList.add('visible', 'in-view');
      return;
    }
    const inHero = !!el.closest('.hero');
    const start = () => revealObserver.observe(el);
    if (curtainActive && inHero) setTimeout(start, 1700); else start();
  }

  function initReveal() {
    if (!reduce && 'IntersectionObserver' in window) {
      revealObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add('visible', 'in-view');
          revealObserver.unobserve(entry.target);
        });
      }, { threshold: 0.18, rootMargin: '0px 0px -8% 0px' });
    }
    document.querySelectorAll('[data-split]').forEach(splitText);
    document.querySelectorAll('[data-split], [data-reveal]').forEach(observe);
  }

  /* ── Parallax con `translate` (no choca con transform de reveal/tilt) ── */
  const parallaxItems = [];
  function measureParallax() {
    parallaxItems.forEach((item) => {
      const prev = item.el.style.translate;
      item.el.style.translate = 'none';
      const rect = (item.frame || item.el).getBoundingClientRect();
      item.base = rect.top + window.scrollY + rect.height / 2;
      item.el.style.translate = prev;
    });
  }
  function applyParallax() {
    const vh = window.innerHeight;
    const sy = window.scrollY;
    parallaxItems.forEach((item) => {
      const delta = item.base - sy - vh / 2;
      if (Math.abs(delta) > vh * 1.6) return;
      item.el.style.translate = `0 ${(-delta * item.speed).toFixed(1)}px`;
    });
  }
  function initParallax() {
    if (reduce) return;
    document.querySelectorAll('[data-parallax]').forEach((el) => {
      parallaxItems.push({ el, speed: parseFloat(el.dataset.parallax) || 0.1, base: 0 });
    });
    document.querySelectorAll('[data-parallax-img]').forEach((el) => {
      parallaxItems.push({ el, frame: el.parentElement, speed: parseFloat(el.dataset.parallaxImg) || 0.1, base: 0 });
    });
    if (!parallaxItems.length) return;
    let ticking = false;
    const tick = () => { applyParallax(); ticking = false; };
    window.addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(tick); } }, { passive: true });
    window.addEventListener('resize', () => { measureParallax(); applyParallax(); }, { passive: true });
    window.addEventListener('load', () => { measureParallax(); applyParallax(); });
    measureParallax();
    applyParallax();
  }



  /* ── Spotlight + Tilt (delegados: funcionan con contenido dinámico) ──── */
  function initPointerFx() {
    if (!finePointer) return;
    let raf = 0, lastEvt = null;
    const process = () => {
      raf = 0;
      const e = lastEvt;
      if (!e) return;
      const spot = e.target.closest && e.target.closest('[data-spot]');
      if (spot) {
        const r = spot.getBoundingClientRect();
        spot.style.setProperty('--mx', `${e.clientX - r.left}px`);
        spot.style.setProperty('--my', `${e.clientY - r.top}px`);
      }
      if (reduce) return;
      const tilt = e.target.closest && e.target.closest('[data-tilt]');
      if (tilt) {
        const r = tilt.getBoundingClientRect();
        const px = (e.clientX - r.left) / r.width - 0.5;
        const py = (e.clientY - r.top) / r.height - 0.5;
        const max = parseFloat(tilt.dataset.tilt) || 6;
        tilt.classList.add('is-tilting');
        tilt.style.transform = `perspective(1000px) rotateX(${(-py * max).toFixed(2)}deg) rotateY(${(px * max).toFixed(2)}deg)`;
      }
    };
    document.addEventListener('pointermove', (e) => { lastEvt = e; if (!raf) raf = requestAnimationFrame(process); }, { passive: true });
    document.addEventListener('pointerout', (e) => {
      const tilt = e.target.closest && e.target.closest('[data-tilt]');
      if (tilt && !tilt.contains(e.relatedTarget)) {
        tilt.classList.remove('is-tilting');
        tilt.style.transform = '';
      }
    }, { passive: true });
  }

  /* ── Botones magnéticos ──────────────────────────────────────────────── */
  function initMagnetic() {
    if (!finePointer || reduce) return;
    const state = new Map();
    let running = false;
    const step = () => {
      let moving = false;
      state.forEach((s, el) => {
        s.cx = lerp(s.cx, s.tx, 0.16); s.cy = lerp(s.cy, s.ty, 0.16);
        if (Math.abs(s.cx - s.tx) > 0.1 || Math.abs(s.cy - s.ty) > 0.1) moving = true;
        el.style.translate = (Math.abs(s.cx) < 0.05 && Math.abs(s.cy) < 0.05 && !s.active) ? '' : `${s.cx.toFixed(1)}px ${s.cy.toFixed(1)}px`;
      });
      if (moving) requestAnimationFrame(step); else running = false;
    };
    const kick = () => { if (!running) { running = true; requestAnimationFrame(step); } };

    document.addEventListener('pointermove', (e) => {
      document.querySelectorAll('[data-magnetic]').forEach((el) => {
        const r = el.getBoundingClientRect();
        const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
        const dx = e.clientX - cx, dy = e.clientY - cy;
        const reach = Math.max(r.width, r.height) * 0.75;
        const s = state.get(el) || { cx: 0, cy: 0, tx: 0, ty: 0, active: false };
        if (Math.hypot(dx, dy) < reach) { s.tx = dx * 0.28; s.ty = dy * 0.38; s.active = true; }
        else if (s.active) { s.tx = 0; s.ty = 0; s.active = false; }
        else return;
        state.set(el, s);
        kick();
      });
    }, { passive: true });
  }

  /* ── Riel horizontal arrastrable ─────────────────────────────────────── */
  function initRails() {
    document.querySelectorAll('[data-rail]').forEach((rail) => {
      let down = false, startX = 0, startLeft = 0, moved = 0;
      rail.addEventListener('pointerdown', (e) => {
        if (e.pointerType === 'touch') return;
        down = true; moved = 0; startX = e.clientX; startLeft = rail.scrollLeft;
      });
      window.addEventListener('pointermove', (e) => {
        if (!down) return;
        const dx = e.clientX - startX;
        moved = Math.max(moved, Math.abs(dx));
        if (moved > 5) rail.classList.add('is-dragging');
        rail.scrollLeft = startLeft - dx;
      });
      window.addEventListener('pointerup', () => { down = false; setTimeout(() => rail.classList.remove('is-dragging'), 0); });
      rail.addEventListener('click', (e) => { if (moved > 5) { e.preventDefault(); e.stopPropagation(); } }, true);
      rail.addEventListener('dragstart', (e) => e.preventDefault());
      rail.querySelectorAll('video').forEach((v) => {
        const card = v.closest('a');
        if (!card) return;
        card.addEventListener('pointerenter', () => v.play().catch(() => {}));
        card.addEventListener('pointerleave', () => v.pause());
      });
    });
  }

  /* ── Contadores animados ─────────────────────────────────────────────── */
  function animateCount(el) {
    const end = parseFloat(el.dataset.count);
    if (!isFinite(end)) return;
    if (reduce) { el.textContent = Math.round(end).toLocaleString('es-AR'); return; }
    const dur = 1400, t0 = performance.now();
    const tick = (t) => {
      const p = clamp((t - t0) / dur, 0, 1);
      const eased = 1 - Math.pow(1 - p, 4);
      el.textContent = Math.round(end * eased).toLocaleString('es-AR');
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }
  function initCounters() {
    const els = document.querySelectorAll('[data-count]');
    if (!els.length) return;
    if (!('IntersectionObserver' in window)) { els.forEach(animateCount); return; }
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => { if (en.isIntersecting) { animateCount(en.target); io.unobserve(en.target); } });
    }, { threshold: 0.4 });
    els.forEach((el) => io.observe(el));
  }

  /* ── Toast global reutilizable ───────────────────────────────────────── */
  function toast(message, type = 'error', ms = 5200) {
    let el = document.getElementById('fx-toast');
    if (!el) {
      el = document.createElement('div');
      el.id = 'fx-toast';
      el.className = 'fx-toast';
      el.setAttribute('role', 'alert');
      document.body.appendChild(el);
    }
    el.classList.toggle('is-info', type !== 'error');
    el.innerHTML = '<span aria-hidden="true">' + (type === 'error' ? '⚠️' : '✦') + '</span><div></div>';
    el.lastChild.textContent = message;
    requestAnimationFrame(() => el.classList.add('is-open'));
    clearTimeout(el._t);
    el._t = setTimeout(() => el.classList.remove('is-open'), ms);
  }

  /* ── Arranque ────────────────────────────────────────────────────────── */
  function boot() {
    safe(initCurtain, 'curtain');
    safe(initProgress, 'progress');
    safe(initReveal, 'reveal');
    safe(initParallax, 'parallax');
    safe(initPointerFx, 'pointer');
    safe(initMagnetic, 'magnetic');
    safe(initRails, 'rails');
    safe(initCounters, 'counters');
  }

  window.HFX = {
    splitText,
    observe,
    toast,
    refresh() {
      document.querySelectorAll('[data-split]:not(.is-split)').forEach(splitText);
      document.querySelectorAll('[data-split], [data-reveal]').forEach((el) => {
        if (!el.classList.contains('visible') && !el.classList.contains('in-view')) observe(el);
      });
      measureParallax();
    },
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
