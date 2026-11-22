'use strict';
/* NikoAssist browser integration checks: local tasks only, no external AI or accounts. */
const assert=require('node:assert/strict');
const {spawn,execFileSync}=require('node:child_process');
const fs=require('node:fs/promises');
const os=require('node:os');
const path=require('node:path');

const root=path.resolve(__dirname,'..');
const port=19486,base='http://127.0.0.1:'+port;
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function poll(fn,label,timeout=20000){
 const start=Date.now();let error;
 while(Date.now()-start<timeout){
  try{const result=await fn();if(result)return result;}catch(e){error=e;}
  await sleep(120);
 }
 throw new Error('Timeout '+label+(error?': '+error.message:''));
}
function chromeBinary(){
 if(process.env.CHROME_BIN)return process.env.CHROME_BIN;
 for(const candidate of ['google-chrome','google-chrome-stable','chromium','chromium-browser']){
  try{return execFileSync('which',[candidate],{encoding:'utf8'}).trim();}catch{}
 }
 throw Error('Chromium non disponible sur ce runner.');
}
function taskFileInput(json,name='nikoassist-taches.json'){
 return '(()=>{const picker=document.querySelector("#import-tasks-file");'+
  'const data=new DataTransfer();data.items.add(new File(['+JSON.stringify(json)+'],'+
   JSON.stringify(name)+',{type:"application/json"}));picker.files=data.files;'+
   'picker.dispatchEvent(new Event("change",{bubbles:true}));return true;})()';
}
async function main(){
 let server,chrome,ws;const pending=new Map(),browserErrors=[],httpPosts=[];
 const tmp=await fs.mkdtemp(path.join(os.tmpdir(),'nikoassist-browser-'));
 let seq=0,diagnostics='';
 try{
  server=spawn('python3',['-m','http.server',String(port),'--bind','127.0.0.1','--directory','web'],{
   cwd:root,stdio:['ignore','ignore','pipe']
  });
  server.stderr.on('data',chunk=>diagnostics+=String(chunk).slice(-1000));
  await poll(async()=>{const r=await fetch(base+'/');return r.status===200},'local web server');
  chrome=spawn(chromeBinary(),['--headless=new','--no-sandbox','--disable-gpu','--disable-dev-shm-usage',
   '--no-first-run','--no-default-browser-check','--disable-background-networking',
   '--remote-debugging-port=0','--remote-allow-origins=*',
   '--user-data-dir='+path.join(tmp,'chrome'),'about:blank'],{stdio:['ignore','ignore','pipe']});
  chrome.stderr.on('data',chunk=>diagnostics+=String(chunk).slice(-1000));
  const debuggerPort=await poll(async()=>{
   const raw=await fs.readFile(path.join(tmp,'chrome','DevToolsActivePort'),'utf8');
   return Number(raw.split('\n')[0]);
  },'Chrome DevTools');
  const tabs=await(await fetch('http://127.0.0.1:'+debuggerPort+'/json/list')).json();
  const tab=tabs.find(x=>x.type==='page');
  assert.ok(tab?.webSocketDebuggerUrl,'Chrome debugger page missing');
  ws=new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{
   ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',reject,{once:true});
  });
  ws.addEventListener('message',event=>{
   const msg=JSON.parse(event.data);
   if(msg.method==='Runtime.exceptionThrown')browserErrors.push(msg.params?.exceptionDetails?.exception?.description||'Browser exception');
   if(msg.method==='Network.requestWillBeSent'&&msg.params?.request?.method==='POST')httpPosts.push(msg.params.request.url);
   if(!msg.id||!pending.has(msg.id))return;
   const p=pending.get(msg.id);pending.delete(msg.id);
   msg.error?p.reject(Error(JSON.stringify(msg.error))):p.resolve(msg.result);
  });
  function call(method,params={}){
   const id=++seq;
   return new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>{pending.delete(id);reject(Error('DevTools timeout '+method));},12000);
    pending.set(id,{resolve:v=>{clearTimeout(timer);resolve(v);},reject:e=>{clearTimeout(timer);reject(e);}});
    ws.send(JSON.stringify({id,method,params}));
   });
  }
  async function evaluate(expression){
   const out=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
   if(out.exceptionDetails)throw Error('Browser JS: '+(out.exceptionDetails.exception?.description||out.exceptionDetails.text));
   return out.result?.value;
  }
  const wait=(expression,label)=>poll(()=>evaluate(expression),label,15000);
  await call('Page.enable');await call('Runtime.enable');await call('Network.enable');
  await call('Page.navigate',{url:base+'/'});
  await wait('document.readyState==="complete"&&!!document.querySelector("#import-tasks")&&!!window.NikoAssistTaskBackup','PWA initialized');
  await evaluate('window.confirm=()=>true;true');
  await evaluate('(()=>{document.querySelector("#task-input").value="Projet local";document.querySelector("#task-form").requestSubmit();return true})()');
  await wait('document.querySelector("#task-count").textContent.includes("1 tâche")','local task created');
  const backup=JSON.stringify({format:'nikoassist-tasks-v1',tasks:[
   {id:'untrusted-1',text:'Projet local',done:true},
   {id:'untrusted-2',text:'Monter la vidéo',done:true}
  ]});
  await evaluate(taskFileInput(backup));
  await wait('document.querySelector("#import-status").textContent.includes("1 tâche(s) importée(s)")','backup restored');
  const stored=await evaluate('JSON.parse(localStorage.getItem("nikoassist-web-tasks-v1"))');
  assert.equal(stored.length,2,'Merge preserves original and adds one task');
  assert.equal(stored.find(x=>x.text==='Projet local').done,false,'Existing completion state must stay unchanged');
  assert.equal(stored.find(x=>x.text==='Monter la vidéo').done,true,'Restored completion state must be preserved');
  assert.equal(stored.some(x=>x.id==='untrusted-2'),false,'Untrusted backup IDs must not be reused');
  const oldJSON=JSON.stringify(stored);
  await evaluate(taskFileInput('{not-json','invalid.json'));
  await wait('document.querySelector("#import-status").textContent.includes("Import refusé")','malformed backup refused');
  assert.equal(await evaluate('JSON.stringify(JSON.parse(localStorage.getItem("nikoassist-web-tasks-v1")))'),oldJSON,'Bad backup must not modify tasks');
  await evaluate('(()=>{const original=URL.createObjectURL.bind(URL);URL.createObjectURL=blob=>{window.__nikoExportBlob=blob;return original(blob)};document.querySelector("#export-tasks").click();return true})()');
  const exported=await evaluate('window.__nikoExportBlob.text().then(JSON.parse)');
  assert.equal(exported.format,'nikoassist-tasks-v1','Export format is stable');
  assert.equal(exported.tasks.length,2,'Export contains merged tasks');
  await call('Page.navigate',{url:base+'/?reloaded=1'});
  await wait('document.readyState==="complete"&&document.querySelector("#task-count")?.textContent.includes("2 tâches")','local backup survives reload');
  await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:3,mobile:true});
  assert.equal(await evaluate('(()=>{const b=document.querySelector("#import-tasks").getBoundingClientRect();return b.height>=44&&b.width>=44&&b.left>=0&&b.right<=innerWidth})()'),true,'Mobile import button must meet 44px target and stay onscreen');
  assert.equal(await evaluate('(()=>{const b=document.querySelector("#studio-niko-embedded-guide>summary").getBoundingClientRect();return b.height>=44&&b.width>=44&&b.left>=0&&b.right<=innerWidth})()'),true,'Mobile help target must meet 44px');
  await evaluate('document.querySelector("#message").focus();true');
  await wait('document.activeElement?.id==="message"','mobile composer focus');
  const guideState=await evaluate('(()=>{const g=document.querySelector("#studio-niko-embedded-guide");return {active:document.activeElement?.id,typing:g.dataset.typing||null,open:g.open,visible:getComputedStyle(g).visibility,cssHas:CSS.supports("selector(body:has(textarea:focus))"),helpRule:document.querySelector("#studio-niko-guide-style")?.textContent.includes("data-typing")};})()');
  assert.equal(guideState.visible,'hidden','Closed help should not cover focused mobile composer: '+JSON.stringify(guideState));
  assert.deepEqual(browserErrors,[],'Uncaught JS errors');
  assert.deepEqual(httpPosts,[],'Task backup must not submit data to a server');
  console.log('CHROMIUM NIKOASSIST PASS: add, merge, dedupe, confirm, invalid JSON, export, reload, 390px touch and privacy');
 }catch(error){
  throw Error(error.message+(diagnostics?'\nBrowser diagnostics: '+diagnostics.slice(-1000):''));
 }finally{
  try{ws?.close();}catch{}
  try{chrome?.kill('SIGKILL');}catch{}
  try{server?.kill('SIGTERM');}catch{}
  await sleep(300);
  await fs.rm(tmp,{recursive:true,force:true,maxRetries:6,retryDelay:200}).catch(()=>{});
 }
}
main().catch(e=>{console.error(e.stack||e);process.exitCode=1;});
