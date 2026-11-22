/* NikoAssist Web — mises à jour des ressources avec secours hors connexion. */
const CACHE='nikoassist-web-v7-network-first';
const PREFIX='nikoassist-web-';
const ASSETS=['./','./index.html','./styles.css','./app.js','./tasks-backup.js','./studio-niko-core.js','./manifest.webmanifest','./icon.svg','./icon-192.png','./icon-512.png','./install.js'];
const ROOT=new URL('./',self.registration.scope);
const INDEX=new URL('./index.html',self.registration.scope);
const SHELL=new Set(['./styles.css','./app.js','./tasks-backup.js','./studio-niko-core.js','./install.js'].map(path=>new URL(path,self.registration.scope).pathname));
self.addEventListener('install',event=>event.waitUntil(
 caches.open(CACHE).then(cache=>cache.addAll(ASSETS)).then(()=>self.skipWaiting())
));
self.addEventListener('activate',event=>event.waitUntil(
 caches.keys().then(keys=>Promise.all(keys.filter(key=>key.startsWith(PREFIX)&&key!==CACHE).map(key=>caches.delete(key))))
  .then(()=>self.clients.claim())
));
self.addEventListener('fetch',event=>{
 const request=event.request;
 const url=new URL(request.url);
 if(request.method!=='GET'||url.origin!==self.location.origin||url.pathname.startsWith('/api/'))return;
 if(request.mode==='navigate'){
  event.respondWith(fetch(request).then(response=>{
   // Ne jamais remplacer l'accueil hors ligne avec la réponse d'une autre route.
   if(response.ok&&(url.pathname===ROOT.pathname||url.pathname===INDEX.pathname)){
    const copy=response.clone();
    event.waitUntil(caches.open(CACHE).then(cache=>cache.put(INDEX.href,copy)));
   }
   return response;
  }).catch(async()=>await caches.match(INDEX.href)||await caches.match(request)||Response.error()));
  return;
 }
 if(SHELL.has(url.pathname)){
  // CSS/JS : réseau prioritaire. Une mise à jour de code ne reste plus bloquée dans l'ancien cache.
  event.respondWith(fetch(request).then(response=>{
   if(response.ok){
    const copy=response.clone();
    event.waitUntil(caches.open(CACHE).then(cache=>cache.put(request,copy)));
   }
   return response;
  }).catch(async()=>await caches.match(request)||Response.error()));
  return;
 }
 event.respondWith(caches.match(request).then(hit=>hit||fetch(request)));
});
