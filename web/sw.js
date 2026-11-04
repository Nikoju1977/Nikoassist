const CACHE='nikoassist-web-v1';
const ASSETS=['./','./index.html','./styles.css','./app.js','./manifest.webmanifest','./icon.svg'];
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{
 const r=event.request;if(r.method!=='GET'||new URL(r.url).origin!==self.location.origin||new URL(r.url).pathname.startsWith('/api/'))return;
 if(r.mode==='navigate'){event.respondWith(fetch(r).then(x=>{if(x.ok){const c=x.clone();caches.open(CACHE).then(cache=>cache.put('./index.html',c));}return x;}).catch(()=>caches.match('./index.html')));return;}
 event.respondWith(caches.match(r).then(c=>c||fetch(r)));
});