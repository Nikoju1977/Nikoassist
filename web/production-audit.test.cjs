'use strict';
const assert=require('node:assert/strict');
const {inspect,markdown,EXPECTED_CACHE,BASE}=require('./production-audit.cjs');

const sample={
 '/':'<title>NikoAssist — Studio Niko</title><textarea id="message"></textarea>',
 '/sw.js':"const CACHE='"+EXPECTED_CACHE+"';",
 '/app.js':'function syncHelpDuringEditing(){}',
 '/tasks-backup.js':"const FORMAT='nikoassist-tasks-v1';",
 '/styles.css':'.shell{display:grid}',
 '/api/health':JSON.stringify({ok:true,service:'nikoassist-web',pythonEngineConnected:false})
};
function mockFetch(overrides={}){
 return async(url,options)=>{
  assert(url.startsWith(BASE+'/'),'Audited URL must be the production origin');
  assert.equal(options.method,'GET');
  const pathname=new URL(url).pathname;
  const value=Object.hasOwn(overrides,pathname)?overrides[pathname]:sample[pathname];
  if(value instanceof Error)throw value;
  const response=typeof value==='object'?value:{body:value,status:200};
  return new Response(response.body||'',{
   status:response.status||200,
   headers:{'content-type':response.type||(pathname==='/api/health'?'application/json':pathname==='/'?'text/html':'application/javascript')}
  });
 };
}
(async()=>{
 const ok=await inspect(mockFetch());
 assert.equal(ok.status,'http_verified');
 assert.equal(ok.checks.length,6);
 assert.equal(ok.checks.every(x=>x.status==='verified'),true);
 assert.match(markdown(ok),/HTTP NikoAssist production/);
 const stale=await inspect(mockFetch({'/sw.js':"const CACHE='nikoassist-web-v6-task-restoration';"}));
 assert.equal(stale.status,'outdated_or_incomplete','Previous service worker cannot be called current');
 assert.equal(stale.checks.find(x=>x.id==='pwa').cache_version,'nikoassist-web-v6-task-restoration');
 const outdatedApp=await inspect(mockFetch({'/app.js':'const oldUI=true;'}));
 assert.equal(outdatedApp.checks.find(x=>x.id==='interface').status,'mismatch');
 const htmlInstead=await inspect(mockFetch({'/app.js':{body:'<!doctype html>',type:'text/html',status:200}}));
 assert.equal(htmlInstead.checks.find(x=>x.id==='interface').status,'mismatch');
 assert.match(htmlInstead.checks.find(x=>x.id==='interface').reason,/HTML/);
 const down=await inspect(mockFetch({'/api/health':new Error('offline')}));
 assert.equal(down.status,'partially_unreachable');
 assert.equal(down.checks.find(x=>x.id==='sante').http_status,null);
 const error=await inspect(mockFetch({'/app.js':{body:'Unavailable',status:503}}));
 assert.equal(error.status,'outdated_or_incomplete');
 assert.equal(error.checks.find(x=>x.id==='interface').http_status,503);
 console.log('PASS audit production — version, HTTP, HTML fallbacks, réseau, limites');
})().catch(error=>{console.error(error);process.exitCode=1});
