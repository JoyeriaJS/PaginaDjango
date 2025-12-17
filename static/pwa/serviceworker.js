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
    const req = event.request;
    const url = new URL(req.url);

    // -------------------------------
    // 1️⃣ Cloudinary + imágenes locales
    // -------------------------------
    if (req.destination === "image" || url.hostname.includes("cloudinary")) {
        event.respondWith(
            caches.open(IMG_CACHE).then(cache =>
                fetch(req)
                    .then(res => {
                        cache.put(req, res.clone());
                        return res;
                    })
                    .catch(() => cache.match(req))
            )
        );
        return;
    }

    // -------------------------------
    // 2️⃣ Páginas HTML completas
    // -------------------------------
    if (req.headers.get("accept")?.includes("text/html")) {
        event.respondWith(
            fetch(req)
                .then(res => {
                    caches.open(DYNAMIC_CACHE).then(cache => {
                        cache.put(req, res.clone());
                    });
                    return res;
                })
                .catch(() => caches.match(req) || caches.match("/static/pwa/offline.html"))
        );
        return;
    }

    // -------------------------------
    // 3️⃣ Sincronización de carrito Offline
    // -------------------------------
    if (url.pathname.includes("/carrito/agregar/")) {
        event.respondWith(
            fetch(req).catch(async () => {
                // Guardar operación para sincronizar después
                let pending = await readCartPending();
                pending.push({
                    url: url.pathname,
                    method: req.method,
                    timestamp: Date.now()
                });
                await writeCartPending(pending);

                return new Response(
                    JSON.stringify({ ok: true, offline: true }),
                    { headers: { "Content-Type": "application/json" } }
                );
            })
        );
        return;
    }

    // -------------------------------
    // 4️⃣ Normal: Static + fallback dinámico
    // -------------------------------
    event.respondWith(
        caches.match(req).then(cached => {
            return (
                cached ||
                fetch(req)
                    .then(res => {
                        caches.open(DYNAMIC_CACHE).then(cache => {
                            cache.put(req, res.clone());
                        });
                        return res;
                    })
                    .catch(() => cached)
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
