(()=>{
'use strict';
const $=id=>document.getElementById(id);
const taskKey='nikoassist-web-tasks-v1';
let tasks=[];
try{const value=JSON.parse(localStorage.getItem(taskKey)||'[]');if(Array.isArray(value))tasks=value.filter(x=>x&&typeof x.text==='string').slice(0,200);}catch{}
const messages=$('messages');const composer=$('message');
function save(){try{localStorage.setItem(taskKey,JSON.stringify(tasks));}catch{addMessage('assistant','Le stockage local est indisponible ; les modifications restent temporaires.');}}
function addMessage(role,text,source=null){
 const row=document.createElement('div');row.className='message-row '+role;
 const avatar=document.createElement('span');avatar.className='avatar';avatar.textContent=role==='user'?'U':'N';
 const bubble=document.createElement('div');bubble.className='bubble';
 const p=document.createElement('p');p.textContent=text;bubble.appendChild(p);
 if(source&&/^https:\/\/(?:fr\.wikipedia\.org|github\.com|studio-niko-hub\.vercel\.app)\//.test(source)){
  const link=document.createElement('a');link.className='source';link.href=source;link.target='_blank';link.rel='noopener noreferrer';link.textContent='Consulter la source ↗';bubble.appendChild(link);
 }
 row.append(avatar,bubble);messages.appendChild(row);messages.scrollTop=messages.scrollHeight;
 if(role==='assistant'&&$('read-aloud').checked&&'speechSynthesis' in window){speechSynthesis.cancel();const utterance=new SpeechSynthesisUtterance(text);utterance.lang='fr-FR';utterance.rate=1;speechSynthesis.speak(utterance);}
}
function renderTasks(){
 $('tasks').replaceChildren();const completed=tasks.filter(x=>x.done).length;
 $('task-count').textContent=tasks.length+' tâche'+(tasks.length>1?'s':'')+(completed?' · '+completed+' terminée'+(completed>1?'s':''):'');
 $('empty-tasks').hidden=tasks.length>0;
 for(const task of tasks){
  const item=document.createElement('li');item.className=task.done?'done':'';
  const label=document.createElement('label');const box=document.createElement('input');box.type='checkbox';box.checked=!!task.done;box.dataset.task=task.id;
  const span=document.createElement('span');span.textContent=task.text;label.append(box,span);
  const del=document.createElement('button');del.className='delete-task';del.type='button';del.textContent='×';del.title='Supprimer la tâche';del.setAttribute('aria-label','Supprimer '+task.text);del.dataset.delete=task.id;
  item.append(label,del);$('tasks').appendChild(item);
 }
}
function addTask(text){
 const name=String(text||'').trim().slice(0,160);
 if(!name)return false;
 if(tasks.length>=200)return false;
 tasks.unshift({id:String(Date.now())+'-'+Math.random().toString(36).slice(2,9),text:name,done:false,created:new Date().toISOString()});
 save();renderTasks();return true;
}
function calculate(raw){
 const input=raw.replaceAll(',','.').replace(/[×x]/g,'*').replace(/[÷:]/g,'/').replace(/\s+/g,'');
 if(input.length>90||!/^[0-9.+\-*/()%]+$/.test(input))return null;
 let pos=0;
 function parseExpr(){
  let left=parseTerm();
  while(input[pos]==='+'||input[pos]==='-'){const operator=input[pos++];const r=parseTerm();left=operator==='+'?left+r:left-r;}return left;
 }
 function parseTerm(){let left=parseFactor();while(input[pos]==='*'||input[pos]==='/'){const op=input[pos++];const r=parseFactor();left=op==='*'?left*r:left/r;}return left;}
 function parseFactor(){if(input[pos]==='+'){pos++;return parseFactor();}if(input[pos]==='-'){pos++;return -parseFactor();}
  if(input[pos]==='('){pos++;const value=parseExpr();if(input[pos++]!==')')throw Error('parenthèse');return value;}
  const match=/^(?:\d+\.?\d*|\.\d+)/.exec(input.slice(pos));if(!match)throw Error('nombre');
  pos+=match[0].length;return Number(match[0]);}
 try{const answer=parseExpr();if(pos!==input.length||!Number.isFinite(answer))return null;return Number(answer.toPrecision(12));}catch{return null;}
}
async function assistantCommand(text){
 const q=text.trim();
 if(/^(salut|bonjour|bonsoir|aide|help|commandes|que peux[- ]tu faire)[ !?]*$/i.test(q))
  return {answer:'Je peux rechercher une information sur Wikipédia (« Qui est Alice Guy ? »), consulter la météo (« météo à Nantes »), calculer (« calcule (24 * 16) / 3 »), ajouter une tâche (« ajoute tâche : préparer le tournage ») ou afficher « mes tâches ». La dictée et la lecture dépendent du navigateur. Le moteur multi-agents Python n’est pas connecté.'};
 const add=/^(?:ajoute(?:r)?(?: une)? t[aâ]che|note une t[aâ]che|rappelle[- ]moi de)\s*[:\-]?\s+(.+)$/i.exec(q);
 if(add){const ok=addTask(add[1]);return {answer:ok?'Tâche ajoutée à cet appareil : '+add[1]:'Impossible d’ajouter la tâche (limite atteinte ou titre vide).'};}
 if(/^(?:mes t[aâ]ches|liste des t[aâ]ches|affiche les t[aâ]ches)$/i.test(q))return{answer:tasks.length?tasks.map((x,i)=>(i+1)+'. '+(x.done?'[terminée] ':'')+x.text).join('\n'):'Vous n’avez encore aucune tâche enregistrée sur cet appareil.'};
 const calc=/^(?:calcul(?:e|er)?|combien font)\s*[:\-]?\s*(.+?)[ ?]*$/i.exec(q);
 if(calc){const result=calculate(calc[1]);return{answer:result===null?'Expression invalide. Exemple : calcule (24 * 16) / 3':'Résultat : '+result};}
 const weather=/\b(?:m[eé]t[eé]o|temps qu.il fait|temp[eé]rature)\b(?:\s*(?:a|à|sur|pour|de|du|dans|en)\s+)?\s*(.+)?$/i.exec(q);
 if(weather){
   let city=(weather[1]||'').trim().replace(/[?!]+$/,'');
   if(!city||/^(?:aujourd'hui|maintenant|actuelle?)$/i.test(city))return{answer:'Précise une ville, par exemple : « météo à Nantes ». Je ne collecte pas ta position automatiquement.'};
   return await askApi({type:'weather',query:city.slice(0,100)});
 }
 if(/^(?:quelle heure|il est quelle heure|nous sommes quel jour|quelle date)/i.test(q))
   return{answer:'Nous sommes le '+new Intl.DateTimeFormat('fr-FR',{dateStyle:'full',timeStyle:'short',timeZone:'Europe/Paris'}).format(new Date())+' (heure de Paris).'};
 const wiki=/^(?:qui est|qui [eé]tait|qu.est[- ]ce que|c.est quoi|d[eé]finis|recherche|cherche|wikip[eé]dia|parle[- ]moi de)\s+(.+?)[?!.\s]*$/i.exec(q);
 if(wiki)return await askApi({type:'wiki',query:wiki[1].trim().slice(0,120)});
 return{answer:'Je n’ai pas de moteur conversationnel général connecté pour répondre avec fiabilité. Essaie « Recherche Alice Guy », « Météo Rennes », « Calcule 24*8 » ou « Ajoute tâche : ... ». Pour le véritable multi-agents, le runtime Python de NikoAssist doit encore être relié à un service sécurisé.'};
}
async function askApi(payload){
 const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),10000);
 try{
  const response=await fetch('./api/assistant',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(payload),signal:controller.signal});
  const data=await response.json();if(!response.ok)throw Error(data.error||'Erreur HTTP '+response.status);
  return{answer:data.answer||'Aucun résultat trouvé.',source:data.source||null};
 }catch(e){return{answer:'Service momentanément indisponible. Vérifie ta connexion et réessaie. '+(e.name==='AbortError'?'Délai de réponse dépassé.':'')};}
 finally{clearTimeout(timer);}
}
let busy=false;
async function sendMessage(text){
 const value=String(text||'').trim();
 if(!value||busy)return;
 addMessage('user',value);composer.value='';busy=true;$('send').disabled=true;
 try{const reply=await assistantCommand(value);addMessage('assistant',reply.answer,reply.source);}
 finally{busy=false;$('send').disabled=false;composer.focus();}
}
$('prompt-form').addEventListener('submit',event=>{event.preventDefault();sendMessage(composer.value);});
composer.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendMessage(composer.value);}});
document.querySelectorAll('[data-example]').forEach(b=>b.addEventListener('click',()=>sendMessage(b.dataset.example)));
$('clear-chat').addEventListener('click',()=>{messages.replaceChildren();addMessage('assistant','Conversation effacée. Tes tâches locales sont conservées.');});
$('task-form').addEventListener('submit',e=>{e.preventDefault();if(addTask($('task-input').value))$('task-input').value='';});
$('tasks').addEventListener('change',e=>{if(e.target.matches('[data-task]')){const task=tasks.find(x=>x.id===e.target.dataset.task);if(task){task.done=e.target.checked;save();renderTasks();}}});
$('tasks').addEventListener('click',e=>{const b=e.target.closest('[data-delete]');if(b){tasks=tasks.filter(x=>x.id!==b.dataset.delete);save();renderTasks();}});
$('clear-completed').addEventListener('click',()=>{tasks=tasks.filter(x=>!x.done);save();renderTasks();});
$('export-tasks').addEventListener('click',()=>{
 const payload=JSON.stringify({format:'nikoassist-tasks-v1',exported:new Date().toISOString(),tasks},null,2);
 const url=URL.createObjectURL(new Blob([payload],{type:'application/json'}));
 const a=document.createElement('a');a.href=url;a.download='nikoassist-taches.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
const SpeechRecognition=window.SpeechRecognition||window.webkitSpeechRecognition;
if(!SpeechRecognition){$('microphone').hidden=true;}
else{
 let recognition=null;
 $('microphone').addEventListener('click',()=>{
  if(recognition){recognition.stop();return;}
  recognition=new SpeechRecognition();recognition.lang='fr-FR';recognition.interimResults=false;recognition.maxAlternatives=1;
  recognition.onresult=e=>{composer.value=e.results[0][0].transcript;composer.focus();};
  recognition.onend=()=>{recognition=null;$('microphone').classList.remove('listening');};
  recognition.onerror=()=>{addMessage('assistant','La dictée vocale n’est pas disponible ou sa permission est refusée.');};
  $('microphone').classList.add('listening');recognition.start();
 });
}
async function health(){
 try{const res=await fetch('./api/health',{cache:'no-store'});if(!res.ok)throw Error('Not ready');const data=await res.json();if(data.ok)$('service-status').textContent='Outils web prêts';else throw Error('Not ready');}
 catch{$('service-status').textContent='Services web indisponibles';}
}
$('year').textContent=new Date().getFullYear();
renderTasks();health();
if('serviceWorker'in navigator)window.addEventListener('load',()=>navigator.serviceWorker.register('./sw.js').catch(()=>{}),{once:true});
})();