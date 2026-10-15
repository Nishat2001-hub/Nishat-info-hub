function initSite() {
  const button = document.querySelector<HTMLButtonElement>('#theme-toggle');
  const sync = () => { const dark = document.documentElement.classList.contains('dark'); button?.setAttribute('aria-pressed', String(dark)); button?.setAttribute('aria-label', dark ? 'লাইট মোড চালু করুন' : 'ডার্ক মোড চালু করুন'); };
  sync();
  button?.addEventListener('click', () => { document.documentElement.classList.toggle('dark'); try { localStorage.setItem('nishat-theme', document.documentElement.classList.contains('dark') ? 'dark' : 'light'); } catch {} sync(); });
  const menu = document.querySelector<HTMLDetailsElement>('header details');
  menu?.addEventListener('keydown', e => { if (e.key === 'Escape') { menu.open = false; menu.querySelector('summary')?.focus(); } });
  document.addEventListener('click', e => { if (menu?.open && e.target instanceof Node && !menu.contains(e.target)) menu.open = false; }, { signal: pageController.signal });
  document.querySelectorAll<HTMLAnchorElement>('header nav a').forEach(a => { if (a.pathname === location.pathname) a.setAttribute('aria-current', 'page'); });
  const ticker = document.querySelector<HTMLButtonElement>('#ticker-toggle');
  ticker?.addEventListener('click', () => { const paused = document.querySelector('.ticker-track')?.classList.toggle('paused'); ticker.setAttribute('aria-pressed', String(paused)); ticker.textContent = paused ? 'চালু করুন' : 'থামান'; });
  const intro = document.querySelector<HTMLElement>('#logo-intro');
  if (!intro || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  try { if (sessionStorage.getItem('nih-intro-seen')) return; sessionStorage.setItem('nih-intro-seen', '1'); } catch { return; }
  intro.classList.add('play');
  setTimeout(() => intro.classList.remove('play'), 1100);
}
let pageController = new AbortController();
document.addEventListener('astro:before-swap', event => { pageController.abort(); event.newDocument.documentElement.classList.toggle('dark', document.documentElement.classList.contains('dark')); });
document.addEventListener('astro:page-load', () => { pageController = new AbortController(); initSite(); });
