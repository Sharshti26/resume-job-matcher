// ResumeMatch AI - simple service worker
// Sirf static files (CSS, icons) cache hoti hain. Login wale pages cache NAHI hote,
// taaki kisi aur user ka data kabhi dikhai na de.
const CACHE = "resumematch-v1";
const STATIC_ASSETS = ["/static/style.css", "/static/icon-192.png", "/static/icon-512.png"];

const OFFLINE_HTML =
  '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">' +
  "<title>Offline</title></head>" +
  '<body style="font-family:Arial,sans-serif;text-align:center;padding:60px 20px;color:#16213E;">' +
  "<h2>You are offline</h2><p>Please check your internet connection and try again.</p></body></html>";

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(STATIC_ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // Page kholna: hamesha internet se; na ho to offline message
  if (req.mode === "navigate") {
    event.respondWith(
      fetch(req).catch(() => new Response(OFFLINE_HTML, { headers: { "Content-Type": "text/html" } }))
    );
    return;
  }

  // Static files: cache se turant, aur background me update
  if (url.pathname.startsWith("/static/")) {
    event.respondWith(
      caches.match(req).then((cached) => {
        const network = fetch(req)
          .then((res) => {
            const copy = res.clone();
            caches.open(CACHE).then((c) => c.put(req, copy));
            return res;
          })
          .catch(() => cached);
        return cached || network;
      })
    );
  }
});