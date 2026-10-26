/* NikoAssist PWA: secure offline shell + Web Push.
 * Never cache API/WS responses, HTML documents, model output or credentials.
 * Only anonymous, hash-versioned build assets can be cached.
 */
const STATIC_CACHE = "nikoassist-static-v1";
const CORE = ["/offline.html", "/icon.svg", "/icon-192.png", "/icon-512.png", "/manifest.webmanifest"];
const ASSET_PATTERN = /^\/assets\/[^/]+-[\w-]{8,}\.(?:js|css|woff2?|svg|png)$/;

self.addEventListener("install", (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(STATIC_CACHE);
    // The offline page must exist; noncritical artwork is best effort.
    await cache.add("/offline.html");
    await Promise.allSettled(CORE.filter((p) => p !== "/offline.html").map((path) => cache.add(path)));
    await self.skipWaiting();
  })());
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    for (const key of await caches.keys()) {
      if (key.startsWith("nikoassist-static-") && key !== STATIC_CACHE) await caches.delete(key);
    }
    await self.clients.claim();
  })());
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  // Credentials and private content NEVER pass through CacheStorage.
  if (url.pathname.startsWith("/api/") || url.pathname === "/api" || url.pathname.startsWith("/ws") || url.pathname.startsWith("/auth")) return;
  if (req.mode === "navigate") {
    event.respondWith(fetch(req).catch(async () => {
      const fallback = await caches.match("/offline.html");
      return fallback || new Response("NikoAssist hors ligne", { status: 503, headers: { "Content-Type": "text/plain; charset=utf-8" } });
    }));
    return;
  }
  if (url.search || !ASSET_PATTERN.test(url.pathname)) return;
  event.respondWith((async () => {
    const cache = await caches.open(STATIC_CACHE);
    const cached = await cache.match(req);
    if (cached) return cached;
    const response = await fetch(req);
    if (response.ok && response.type === "basic") await cache.put(req, response.clone());
    return response;
  })());
});

async function setBadge(n) {
  if (typeof n !== "number" || !("setAppBadge" in self.navigator)) return;
  try {
    if (n > 0) await self.navigator.setAppBadge(n);
    else await self.navigator.clearAppBadge();
  } catch { /* Badging API optional */ }
}

function sameOriginPath(candidate) {
  try {
    const url = new URL(candidate || "/", self.location.origin);
    return url.origin === self.location.origin ? url.pathname + url.search + url.hash : "/";
  } catch {
    return "/";
  }
}

self.addEventListener("push", (event) => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch {
    data = { title: "NikoAssist", body: event.data ? event.data.text() : "" };
  }
  event.waitUntil((async () => {
    await setBadge(data.badge);
    const windows = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
    if (windows.some((c) => c.visibilityState === "visible") && data.kind !== "test") return;
    await self.registration.showNotification(data.title || "NikoAssist", {
      body: data.body || "",
      tag: data.tag || undefined,
      renotify: !!data.tag,
      icon: "/icon-192.png",
      badge: "/icon-192.png",
      timestamp: data.ts ? Date.parse(data.ts) : Date.now(),
      data: { url: sameOriginPath(data.url), kind: data.kind || "" },
    });
  })());
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const path = sameOriginPath(event.notification.data && event.notification.data.url);
  event.waitUntil((async () => {
    const windows = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
    for (const client of windows) {
      if ("focus" in client) {
        await client.focus();
        client.postMessage({ type: "open", url: path });
        return;
      }
    }
    await self.clients.openWindow(path);
  })());
});
