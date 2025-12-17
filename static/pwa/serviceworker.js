const VERSION = "v10-fullapp";
const STATIC_CACHE = `static-${VERSION}`;
const DYNAMIC_CACHE = `dynamic-${VERSION}`;
const IMG_CACHE = `images-${VERSION}`;
const CART_CACHE_KEY = "offline-cart-sync";

// Páginas base cacheadas siempre
const HTML_PAGES = [
    "/",
    "/categorias/",
];

// Archivos estáticos importantes
const STATIC_ASSETS = [
    "/static/pwa/offline.html",
    "/static/css/site.css",
    "/static/js/main.js",
    "/static/pwa/icon-192.png",
    "/static/pwa/icon-512.png",
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css"
];

// -------------------------------
// INSTALACIÓN
// -------------------------------
self.addEventListener("install", event => {
    event.waitUntil(
        caches.open(STATIC_CACHE).then(cache => {
            cache.addAll(STATIC_ASSETS);
            cache.addAll(HTML_PAGES);
        })
    );
    self.skipWaiting();
});

// -------------------------------
// ACTIVACIÓN
// -------------------------------
self.addEventListener("activate", event => {
    event.waitUntil(
        caches.keys().then(keys => 
            Promise.all(
                keys.map(key => {
                    if (![STATIC_CACHE, DYNAMIC_CACHE, IMG_CACHE].includes(key)) {
                        return caches.delete(key);
                    }
                })
            )
        )
    );
    self.clients.claim();
});

// --------------------------------------
// FETCH — Offline catálogo + imágenes + páginas
// --------------------------------------
self.addEventListener("fetch", event => {
    const request = event.request;

    // -------------------------
    // 1) IMÁGENES → cache-first
    // -------------------------
    if (request.destination === "image") {
        event.respondWith(
            caches.open(IMG_CACHE).then(cache =>
                fetch(request)
                    .then(res => {
                        cache.put(request, res.clone());
                        return res;
                    })
                    .catch(() => caches.match(request))
            )
        );
        return;
    }

    // -------------------------
    // 2) HTML pages → network-first + fallback offline
    // -------------------------
    if (request.headers.get("accept").includes("text/html")) {
        event.respondWith(
            fetch(request)
                .then(res => {
                    const clone = res.clone();
                    caches.open(CACHE_NAME).then(c => c.put(request, clone));
                    return res;
                })
                .catch(() => caches.match(request).then(cached => {
                    return cached || caches.match("/static/pwa/offline.html");
                }))
        );
        return;
    }

    // -------------------------
    // 3) CSS / JS / fuentes → cache-first
    // -------------------------
    event.respondWith(
        caches.match(request).then(cached => {
            return (
                cached ||
                fetch(request).then(res => {
                    caches.open(CACHE_NAME).then(c =>
                        c.put(request, res.clone())
                    );
                    return res;
                })
            );
        })
    );
});


/* ---------------------------------------------------
   📦 Manejo de sincronización del carrito offline
--------------------------------------------------- */
async function readCartPending() {
    const cache = await caches.open("cart-sync");
    const res = await cache.match(CART_CACHE_KEY);
    return res ? await res.json() : [];
}

async function writeCartPending(data) {
    const cache = await caches.open("cart-sync");
    await cache.put(CART_CACHE_KEY, new Response(JSON.stringify(data)));
}

// Cuando vuelve la red, intentar enviar los registros
self.addEventListener("sync", async event => {
    if (event.tag === "sync-cart") {
        event.waitUntil(syncCartRequests());
    }
});

async function syncCartRequests() {
    let pending = await readCartPending();

    for (const entry of pending) {
        try {
            await fetch(entry.url, { method: entry.method });
        } catch (e) {
            console.warn("❌ Error reenviando:", entry);
            return; // No borrar si falla
        }
    }

    console.log("🟢 Carrito sincronizado correctamente");
    await writeCartPending([]);
}
