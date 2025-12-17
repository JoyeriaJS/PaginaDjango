const CACHE_NAME = "pwa-cache-v1";
const IMG_CACHE = "pwa-images-v1";
const URLS_TO_CACHE = [
    "/",
    "/static/pwa/offline.html",

    // CSS
    "/static/css/site.css",
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css",

    // JS
    "/static/js/main.js",

    // Íconos
    "/static/pwa/icon-192.png",
    "/static/pwa/icon-512.png"
];

// INSTALACIÓN (guarda archivos en caché)
self.addEventListener("install", event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            console.log("📦 Guardando archivos en caché");
            return cache.addAll(URLS_TO_CACHE);
        })
    );
});

// ACTIVACIÓN (borra cachés antiguas)
self.addEventListener("activate", event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(
                keys.map(key => {
                    if (key !== CACHE_NAME) {
                        console.log("🗑 Eliminando cache antigua:", key);
                        return caches.delete(key);
                    }
                })
            )
        )
    );
});

// INTERCEPTAR REQUESTS
self.addEventListener("fetch", event => {

    const request = event.request;

    // 🔵 1. CACHE DINÁMICO DE IMÁGENES
    if (request.destination === "image") {
        event.respondWith(
            caches.open(IMG_CACHE).then(cache => {
                return fetch(request)
                    .then(networkResponse => {
                        cache.put(request, networkResponse.clone()); // Guarda imagen
                        return networkResponse;
                    })
                    .catch(() => caches.match(request)); // Si no hay red → muestra la cacheada
            })
        );
        return; // Salimos para no afectar el resto
    }

    // 🔵 2. CACHE NORMAL (páginas + CSS + JS + etc.)
    event.respondWith(
        caches.match(request).then(cachedResponse => {
            if (cachedResponse) return cachedResponse;

            return fetch(request)
                .catch(() => {
                    if (request.headers.get("accept").includes("text/html")) {
                        return caches.match("/static/pwa/offline.html");
                    }
                });
        })
    );
});

