/* Service worker: قارئ موسوعة اليهود واليهودية والصهيونية.
 * «الشبكة أولًا» للقشرة وملفّات البيانات؛ المتّصل يحصل دائمًا على أحدث نسخة،
 * ويعمل التطبيق دون اتصال من آخر نسخة محفوظة. */
const VERSION = 'v3-2026-06-07';
const CACHE = 'yahud-' + VERSION;
const CORE = ['./', './index.html', './meta.json', './manifest.webmanifest',
              './icon.svg', './icon-192.png', './icon-512.png',
              './apple-touch-icon.png', './favicon.png'];

self.addEventListener('install', (e) => {
  self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(CORE).catch(() => {})));
});

self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  const networkFirst =
    req.mode === 'navigate' ||
    url.pathname.endsWith('/') ||
    url.pathname.endsWith('index.html') ||
    url.pathname.endsWith('meta.json') ||
    /\/vol-\d+\.json$/.test(url.pathname) ||
    url.pathname.endsWith('intro.json');

  if (networkFirst) {
    e.respondWith(
      fetch(req).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(req, copy));
        return res;
      }).catch(() => caches.match(req).then((r) => r || caches.match('./index.html')))
    );
    return;
  }

  e.respondWith(
    caches.match(req).then((cached) => cached || fetch(req).then((res) => {
      const sameOrigin = url.origin === location.origin;
      const fontHost = url.host.indexOf('gstatic') !== -1 || url.host.indexOf('googleapis') !== -1;
      if (res && res.ok && (sameOrigin || fontHost)) {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(req, copy));
      }
      return res;
    }).catch(() => cached))
  );
});
