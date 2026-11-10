/* Offline support. Pages and recipes: try the network first so updates show up, fall back to the saved copy.
   Fonts and icons: saved copy first. Bump VERSION to clear old copies. */
const VERSION = 'cookbot-v1';
const CORE = ['./', 'index.html', 'recipes.js', 'fonts.css', 'manifest.webmanifest', 'icon.svg', 'icon-192.png'];
self.addEventListener('install', e => { e.waitUntil(caches.open(VERSION).then(c => c.addAll(CORE)).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== VERSION).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', e => {
  const req = e.request; if (req.method !== 'GET' || new URL(req.url).origin !== location.origin) return;
  const fresh = req.mode === 'navigate' || /\/(index\.html|recipes\.js)?$|\.js$/.test(new URL(req.url).pathname);
  const save = res => { if (res.ok) { const copy = res.clone(); caches.open(VERSION).then(c => c.put(req, copy)); } return res; };
  e.respondWith(fresh
    ? fetch(req).then(save).catch(() => caches.match(req).then(r => r || caches.match('index.html')))
    : caches.match(req).then(r => r || fetch(req).then(save)));
});
