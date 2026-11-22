'use strict';
/* Regression du service worker sans connexion réseau : double cache, 404, offline, privacy. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const scope='https://nikoassist.example/';
const routes=new Map();
const stores=new Map();
const listeners={};
const urlOf=value=>new URL(typeof value==='string'?value:value.url,scope).href;
function ensureStore(name){
 if(!stores.has(name))stores.set(name,new Map());
 const store=stores.get(name);
 return {
  async addAll(paths){for(const p of paths){const url=urlOf(p);const res=await networkFetch({url});if(!res.ok)throw Error('Precache failed: '+p);store.set(url,res.clone());}},
  async put(req,res){store.set(urlOf(req),res.clone());},
  async match(req){return store.get(urlOf(req))?.clone()}
 };
}
const caches={
 async open(name){return ensureStore(name)},
 async keys(){return [...stores.keys()]},
 async delete(name){return stores.delete(name)},
 async match(req){for(const name of stores.keys()){const hit=await ensureStore(name).match(req);if(hit)return hit}return undefined}
};
let online=true;
async function networkFetch(req){
 if(!online)throw Error('Offline');
 const url=urlOf(req);
 const route=routes.get(url);
 if(!route)return new Response('Unknown',{status:404});
 return new Response(route.body,{status:route.status||200,headers:{'Content-Type':route.contentType||'text/plain'}});
}
const source=fs.readFileSync(path.join(__dirname,'sw.js'),'utf8');
const assets=['','index.html','styles.css','app.js','tasks-backup.js','studio-niko-core.js','manifest.webmanifest','icon.svg','icon-192.png','icon-512.png','install.js'];
for(const asset of assets)routes.set(urlOf(asset),{body:'asset-'+(asset||'root')});
let activated=false;
vm.runInNewContext(source,{URL,Response,Set,Promise,caches,fetch:networkFetch,self:{
 location:{origin:new URL(scope).origin},registration:{scope},
 clients:{claim:async()=>{activated=true}},skipWaiting:async()=>{},
 addEventListener:(name,handler)=>{listeners[name]=handler}
}});
async function lifecycle(name){const waits=[];listeners[name]({waitUntil:p=>waits.push(Promise.resolve(p))});await Promise.all(waits);}
async function request(uri,{method='GET',mode='same-origin'}={}){
 const waits=[];let handled;
 const input={url:urlOf(uri),method,mode};
 listeners.fetch({request:input,respondWith:p=>{handled=Promise.resolve(p)},waitUntil:p=>waits.push(Promise.resolve(p))});
 if(!handled)return null;
 const res=await handled;
 await Promise.all(waits);
 return res;
}
(async()=>{
 stores.set('nikoassist-web-v6-task-restoration',new Map());
 stores.set('another-app-cache-v2',new Map());
 await lifecycle('install');
 await lifecycle('activate');
 assert(activated);
 assert.equal(stores.has('nikoassist-web-v6-task-restoration'),false,'Obsolete NikoAssist cache removed');
 assert.equal(stores.has('another-app-cache-v2'),true,'Other applications caches preserved');
 assert.equal(await (await request('app.js')).text(),'asset-app.js');
 routes.set(urlOf('app.js'),{body:'app-new-code'});
 assert.equal(await (await request('app.js')).text(),'app-new-code','Shell code loads new bytes online');
 online=false;
 assert.equal(await (await request('app.js')).text(),'app-new-code','Updated shell remains available offline');
 online=true;
 routes.set(urlOf(''),{body:'HOME-CURRENT'});
 assert.equal(await (await request('',{mode:'navigate'})).text(),'HOME-CURRENT');
 routes.set(urlOf('other'),{body:'UNRELATED-PAGE'});
 assert.equal(await (await request('other',{mode:'navigate'})).text(),'UNRELATED-PAGE');
 online=false;
 assert.equal(await (await request('',{mode:'navigate'})).text(),'HOME-CURRENT','Unrelated page cannot overwrite offline homepage');
 assert.equal(await request('api/assistant'),null,'API requests bypass cache and service worker');
 assert.equal(await request('app.js',{method:'POST'}),null,'Non-GET bypass');
 assert.equal(await request('https://another-domain.example/app.js'),null,'Cross-origin bypass');
 await assert.rejects(()=>request('file-not-cached.js'),/Offline/,'Offline missing asset must fail, not return HTML');
 console.log('PASS NikoAssist SW regression — updates, offline home, cache isolation, APIs');
})().catch(error=>{console.error(error);process.exitCode=1});
