const VERSION = "v4";
const STATIC_CACHE = `static-${VERSION}`;
const DYNAMIC_CACHE = `dynamic-${VERSION}`;
const IMG_CACHE = `images-${VERSION}`;

const STATIC_ASSETS = [
    "/",
    "/static/pwa/offline.html",
    "/static/css/site.css",
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css",
    "/static/js/main.js",
    "/static/pwa/icon-192.png",
    "/static/pwa/icon-512.png"
];

// INSTALACIÓN
self.addEventListener("install", event => {
    event.waitUntil(
        caches.open(STATIC_CACHE).then(cache => {
            console.log("📦 Cache estática lista");
            return cache.addAll(STATIC_ASSETS);
        })
    );
    self.skipWaiting();
});

// ACTIVACIÓN → elimina versiones antiguas
self.addEventListener("activate", event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(
                keys.map(key => {
                    if (![STATIC_CACHE, DYNAMIC_CACHE, IMG_CACHE].includes(key)) {
                        console.log("🗑 Eliminando cache vieja:", key);
                        return caches.delete(key);
                    }
                })
            )
        )
    );
    self.clients.claim();
});

// FETCH → Manejo especial Cloudinary + offline
self.addEventListener("fetch", event => {
    const req = event.request;
    const url = new URL(req.url);

    // 1️⃣ IMÁGENES DE CLOUDINARY — cache dinámico inteligente
    if (req.destination === "image" || url.hostname.includes("cloudinary")) {
        event.respondWith(
            caches.open(IMG_CACHE).then(cache =>
                fetch(req)
                    .then(res => {
                        cache.put(req, res.clone()); // Guardamos para offline
                        return res;
                    })
                    .catch(() => cache.match(req)) // Si no hay internet → imagen cacheada
            )
        );
        return;
    }

    // 2️⃣ HTML — network first → fallback offline
    if (req.headers.get("accept")?.includes("text/html")) {
        event.respondWith(
            fetch(req)
                .then(res => {
                    return caches.open(DYNAMIC_CACHE).then(cache => {
                        cache.put(req, res.clone());
                        return res;
                    });
                })
                .catch(() => caches.match(req) || caches.match("/static/pwa/offline.html"))
        );
        return;
    }

    // 3️⃣ Static (CSS, JS, fuentes)
    event.respondWith(
        caches.match(req).then(cached => {
            return (
                cached ||
                fetch(req)
                    .then(res => {
                        return caches.open(DYNAMIC_CACHE).then(cache => {
                            cache.put(req, res.clone());
                            return res;
                        });
                    })
                    .catch(() => cached)
            );
        })
    );
});
