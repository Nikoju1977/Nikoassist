'use strict';
// Web tools deliberately run without an LLM and without any personal API key.
const WIKI='https://fr.wikipedia.org/w/api.php';
function output(res,status,obj){res.setHeader('Cache-Control','no-store');res.setHeader('X-Content-Type-Options','nosniff');return res.status(status).json(obj);}
function clean(s,max){return typeof s==='string'?s.trim().replace(/\s+/g,' ').slice(0,max):'';}
async function apiFetch(url){
 const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),6500);
 try{const res=await fetch(url,{signal:controller.signal,headers:{'Accept':'application/json','User-Agent':'NikoAssistWeb/1.0 (public reference lookups)'}});if(!res.ok)throw Error('Upstream '+res.status);return await res.json();}
 finally{clearTimeout(timer);}
}
const codes=new Map([
 [0,'ciel dégagé'],[1,'principalement ensoleillé'],[2,'partiellement nuageux'],[3,'couvert'],
 [45,'brouillard'],[48,'brouillard givrant'],[51,'bruine légère'],[53,'bruine'],[55,'bruine forte'],
 [61,'pluie faible'],[63,'pluie'],[65,'forte pluie'],[71,'neige légère'],[73,'neige'],[75,'fortes chutes de neige'],
 [80,'averses faibles'],[81,'averses'],[82,'fortes averses'],[95,'orage'],[96,'orage et grêle'],[99,'orage et forte grêle']
]);
async function wiki(query){
 const u=new URL(WIKI);u.searchParams.set('action','query');u.searchParams.set('list','search');u.searchParams.set('srsearch',query);
 u.searchParams.set('srlimit','1');u.searchParams.set('format','json');
 const raw=await apiFetch(u.href);const title=raw.query?.search?.[0]?.title;
 if(!title)return{answer:'Aucun article Wikipédia trouvé pour « '+query+' ». Essaie un terme plus précis.'};
 const z=new URL(WIKI);z.searchParams.set('action','query');z.searchParams.set('prop','extracts');z.searchParams.set('exintro','1');z.searchParams.set('explaintext','1');z.searchParams.set('format','json');z.searchParams.set('titles',title);
 const info=await apiFetch(z.href);
 const pages=Object.values(info.query?.pages||{});
 const extract=clean(pages[0]?.extract||'',1500);
 return {answer:title+'.\n\n'+(extract||'Un article existe, mais aucun résumé textuel n’est disponible.'),source:'https://fr.wikipedia.org/wiki/'+encodeURIComponent(title.replace(/\s/g,'_'))};
}
async function weather(city){
 const u=new URL('https://geocoding-api.open-meteo.com/v1/search');
 u.searchParams.set('name',city);u.searchParams.set('count','1');u.searchParams.set('language','fr');
 const places=await apiFetch(u.href);const p=places.results?.[0];
 if(!p)return{answer:'Je ne trouve pas la ville « '+city+' ». Essaie une commune proche ou une ville plus connue.'};
 const v=new URL('https://api.open-meteo.com/v1/forecast');
 v.searchParams.set('latitude',String(p.latitude));v.searchParams.set('longitude',String(p.longitude));
 v.searchParams.set('current','temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m');
 v.searchParams.set('timezone',p.timezone||'Europe/Paris');v.searchParams.set('forecast_days','1');
 const data=await apiFetch(v.href);const w=data.current;
 if(!w)return{answer:'Les observations météo sont actuellement indisponibles pour '+p.name+'.'};
 const fmt=x=>typeof x==='number'?String(Math.round(x*10)/10):'—';
 const location=[p.name,p.admin1,p.country].filter(Boolean).join(', ');
 return {answer:'Météo actuelle pour '+location+' : '+(codes.get(w.weather_code)||'conditions variables')+
  '.\nTempérature : '+fmt(w.temperature_2m)+' °C (ressenti '+fmt(w.apparent_temperature)+' °C).'+
  '\nHumidité : '+fmt(w.relative_humidity_2m)+' % ; vent : '+fmt(w.wind_speed_10m)+' km/h ; précipitations : '+fmt(w.precipitation)+' mm.'+
  '\nMesures/modèle fournis par Open-Meteo. Heure du relevé : '+(w.time||'non précisée')+'.',
  source:'https://open-meteo.com/'};
}
module.exports=async function handler(req,res){
 if(req.method!=='POST')return output(res,405,{error:'Méthode non autorisée'});
 const body=req.body&&typeof req.body==='object'?req.body:{};
 const type=clean(body.type,20);const query=clean(body.query,120);
 if(!query||!['wiki','weather'].includes(type))return output(res,400,{error:'Requête invalide'});
 try{
  const result=await(type==='wiki'?wiki(query):weather(query));
  return output(res,200,result);
 }catch(e){return output(res,503,{error:'Source publique momentanément inaccessible. Réessayez ultérieurement.'});}
};