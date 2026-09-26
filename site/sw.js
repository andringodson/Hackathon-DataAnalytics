// Cache-first for immutable assets (versioned files, pinned CDN libraries, font files);
// network-first for the page and data so updates show up immediately, with the cache as an offline fallback.
const VERSION = "__V__";
const STATIC = `vr-static-${VERSION}`;
const RUNTIME = "vr-runtime";
const IMMUTABLE_HOSTS = new Set(["cdn.jsdelivr.net", "fonts.gstatic.com"]);

self.addEventListener("install", () => self.skipWaiting());

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    for (const key of await caches.keys()) if (key.startsWith("vr-static-") && key !== STATIC) await caches.delete(key);
    await self.clients.claim();
  })());
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  const immutable = IMMUTABLE_HOSTS.has(url.hostname) || (url.origin === self.location.origin && url.searchParams.has("v"));
  if (immutable) {
    event.respondWith((async () => {
      const cache = await caches.open(STATIC);
      const hit = await cache.match(req);
      if (hit) return hit;
      const res = await fetch(req);
      if (res.ok || res.type === "opaque") cache.put(req, res.clone());
      return res;
    })());
    return;
  }
  if (url.origin === self.location.origin) {
    event.respondWith((async () => {
      try {
        const res = await fetch(req);
        if (res.ok) {
          const copy = res.clone();
          caches.open(RUNTIME).then((c) => c.put(req, copy));
        }
        return res;
      } catch (err) {
        const hit = await caches.match(req);
        if (hit) return hit;
        throw err;
      }
    })());
  }
});
