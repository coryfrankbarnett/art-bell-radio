// Art Bell Radio — offline app shell. Audio is not cached here (saved shows live in IndexedDB).
const VERSION = 'abr-v35';
const SHELL = ['./', './index.html', './manifest.webmanifest', './icon-192.png', './icon-512.png', './apple-touch-icon.png', './artwork-1024.png', './icon-maskable-512.png', './fonts/instrument-serif.woff2', './fonts/instrument-serif-italic.woff2', './fonts/space-grotesk.woff2', './fonts/inter.woff2', './fonts/geist-mono-400.woff2', './fonts/geist-mono-500.woff2'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== VERSION).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET') return;
  // Never intercept archive.org (audio, ranges, metadata) — let the browser handle it directly
  if (url.hostname.endsWith('archive.org')) return;
  // Show list: network first, cached copy when offline
  if (url.origin === location.origin && (url.pathname.endsWith('/library.json') || url.pathname.endsWith('/topics.json'))) {
    e.respondWith(fetch(e.request).then(r => { const c = r.clone(); caches.open(VERSION).then(x => x.put(e.request, c)); return r; }).catch(() => caches.match(e.request)));
    return;
  }
  // App page: network first so updates arrive, cached copy when offline
  if (e.request.mode === 'navigate') {
    e.respondWith(fetch(e.request).then(r => { const c = r.clone(); caches.open(VERSION).then(x => x.put('./index.html', c)); return r; })
      .catch(() => caches.match('./index.html')));
    return;
  }
  // Fonts and app files: serve from cache, refresh in the background
  if (url.origin === location.origin || url.hostname.endsWith('fonts.googleapis.com') || url.hostname.endsWith('fonts.gstatic.com')) {
    e.respondWith(caches.open(VERSION).then(async c => {
      const hit = await c.match(e.request);
      const net = fetch(e.request).then(r => { if (r.ok || r.type === 'opaque') c.put(e.request, r.clone()); return r; }).catch(() => hit);
      return hit || net;
    }));
  }
});
