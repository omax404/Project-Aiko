// ═══ Project Aiko — Landing Page Script ═══

document.addEventListener('DOMContentLoaded', () => {
  initScrollReveal();
  initParallax();
  initHeaderScroll();
  initMobileMenu();
});

// ── Scroll Reveal ──
function initScrollReveal() {
  const els = document.querySelectorAll('.reveal');
  if (!('IntersectionObserver' in window)) {
    els.forEach(el => el.classList.add('visible'));
    return;
  }
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const parent = entry.target.parentElement;
        const siblings = parent ? Array.from(parent.querySelectorAll('.reveal')) : [];
        const idx = siblings.indexOf(entry.target);
        setTimeout(() => entry.target.classList.add('visible'), idx * 70);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -30px 0px' });
  els.forEach(el => observer.observe(el));
}

// ── Parallax on hero card ──
function initParallax() {
  const card = document.getElementById('hero-card');
  const floatTarget = document.querySelector('[data-float]');
  if (!card && !floatTarget) return;

  let ticking = false;
  window.addEventListener('pointermove', (e) => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => {
      const cx = window.innerWidth / 2;
      const cy = window.innerHeight / 2;
      const x = (e.clientX - cx) / cx;
      const y = (e.clientY - cy) / cy;
      if (card) card.style.transform = `perspective(1000px) rotateY(${x * 3}deg) rotateX(${-y * 3}deg)`;
      if (floatTarget) floatTarget.style.transform = `translate3d(${x * 8}px, ${y * 8}px, 0)`;
      ticking = false;
    });
  });
  window.addEventListener('pointerleave', () => {
    if (card) card.style.transform = '';
    if (floatTarget) floatTarget.style.transform = '';
  });
}

// ── Header solidify on scroll ──
function initHeaderScroll() {
  const header = document.getElementById('header');
  if (!header) return;
  window.addEventListener('scroll', () => {
    header.classList.toggle('scrolled', window.scrollY > 40);
  }, { passive: true });
}

// ── Mobile menu ──
function initMobileMenu() {
  const toggle = document.getElementById('mobile-toggle');
  const nav = document.getElementById('nav');
  if (!toggle || !nav) return;

  toggle.addEventListener('click', () => {
    const isOpen = nav.style.display === 'flex';
    nav.style.display = isOpen ? '' : 'flex';
    nav.style.position = isOpen ? '' : 'absolute';
    nav.style.top = isOpen ? '' : '60px';
    nav.style.left = isOpen ? '' : '0';
    nav.style.right = isOpen ? '' : '0';
    nav.style.flexDirection = isOpen ? '' : 'column';
    nav.style.background = isOpen ? '' : 'rgba(6,6,12,0.95)';
    nav.style.backdropFilter = isOpen ? '' : 'blur(20px)';
    nav.style.padding = isOpen ? '' : '8px 16px 16px';
    nav.style.borderBottom = isOpen ? '' : '1px solid rgba(255,255,255,0.06)';
  });

  // Close on link click
  nav.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => {
      nav.style.display = '';
      nav.style.position = '';
    });
  });
}
