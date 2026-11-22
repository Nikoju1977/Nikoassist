'use strict';
/* Audit HTTP en lecture seule. Un GET réussi n'est PAS un test navigateur. */
const fs=require('node:fs/promises');
const BASE='https://nikoassist-pwa.vercel.app';
const EXPECTED_CACHE='nikoassist-web-v7-network-first';

async function inspect(fetchImpl=globalThis.fetch){
  const rules=[
    {id:'accueil',path:'/',matches:t=>/NikoAssist/.test(t)&&/id=["']message["']/.test(t)},
    {id:'pwa',path:'/sw.js',matches:t=>t.includes("const CACHE='"+EXPECTED_CACHE+"'")},
    {id:'interface',path:'/app.js',matches:t=>t.includes('syncHelpDuringEditing')},
    {id:'sauvegarde',path:'/tasks-backup.js',matches:t=>t.includes('nikoassist-tasks-v1')},
    {id:'style',path:'/styles.css',matches:t=>t.includes('.shell')},
    {id:'sante',path:'/api/health',matches:t=>{
      try{const json=JSON.parse(t);return json.ok===true&&json.service==='nikoassist-web'&&typeof json.pythonEngineConnected==='boolean';}
      catch{return false;}
    }}
  ];
  const checks=await Promise.all(rules.map(async({id,path,matches})=>{
    const url=new URL(path,BASE).href;
    try{
      const response=await fetchImpl(url,{
        method:'GET',redirect:'follow',signal:AbortSignal.timeout(12000),
        headers:{'Cache-Control':'no-cache','Accept':'*/*'}
      });
      const type=response.headers?.get('content-type')||'';
      const body=await response.text();
      // Un serveur peut renvoyer une page HTML au lieu du JS demandé : ne jamais valider ce cas.
      const wrongMime=(path.endsWith('.js')||path.endsWith('.css'))&&/text\/html/i.test(type);
      const ok=response.status===200&&!wrongMime&&matches(body);
      return {id,path,http_status:response.status,status:ok?'verified':'mismatch',
        reason:ok?'HTTP 200 et marqueurs attendus':wrongMime?'HTML servi à la place de la ressource':'Version ou contenu inattendu',
        ...(id==='pwa'?{cache_version:(body.match(/const CACHE=['"]([^'"]+)/)||[])[1]||null}:{})};
    }catch(error){
      return {id,path,http_status:null,status:'unreachable',reason:String(error?.message||error).slice(0,240)};
    }
  }));
  const verified=checks.every(c=>c.status==='verified');
  const unreachable=checks.some(c=>c.status==='unreachable');
  return {schema:1,checked_at:new Date().toISOString(),url:BASE,
    expected_cache:EXPECTED_CACHE,
    status:verified?'http_verified':unreachable?'partially_unreachable':'outdated_or_incomplete',
    scope:'HTTP public uniquement : aucun parcours navigateur, aucun test sur appareil physique, aucune IA distante vérifiée',
    checks};
}
function markdown(report){
  const icon=report.status==='http_verified'?'✅':'⚠️';
  return ['### Audit HTTP NikoAssist production',
    `${icon} Statut : **${report.status}** — ${report.checked_at}`,
    `URL : ${report.url} · cache attendu : \`${report.expected_cache}\``,
    '', '| Ressource | HTTP | Résultat | Motif |','|---|---:|---|---|',
    ...report.checks.map(c=>`| \`${c.path}\` | ${c.http_status??'—'} | ${c.status} | ${c.reason.replaceAll('|','/')} |`),
    '','**Limite :** vérification HTTP sans interaction avec une interface, sans test iPhone/Android, ni appel aux IA externes.',''].join('\n');
}
async function main(){
  const report=await inspect();
  console.log(JSON.stringify(report,null,2));
  const destination=process.env.NIKOASSIST_AUDIT_REPORT;
  if(destination)await fs.writeFile(destination,JSON.stringify(report,null,2)+'\n','utf8');
  if(process.env.GITHUB_STEP_SUMMARY)await fs.appendFile(process.env.GITHUB_STEP_SUMMARY,markdown(report)+'\n','utf8');
  if(report.status!=='http_verified'){
    console.log('::warning::NikoAssist production non synchronisée ou partiellement inaccessible : '+report.status);
    if(process.env.NIKOASSIST_AUDIT_STRICT==='1')process.exitCode=1;
  }
}
module.exports={inspect,markdown,BASE,EXPECTED_CACHE};
if(require.main===module)main().catch(error=>{console.error(error);process.exitCode=1});
