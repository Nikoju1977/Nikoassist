'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
for(const name of ['app.js','sw.js','tasks-backup.js','api/assistant.js','api/health.js']){
 const content=fs.readFileSync(path.join(__dirname,name),'utf8');
 new Function('module','require','process',content);
}
const page=fs.readFileSync(path.join(__dirname,'index.html'),'utf8');
const js=fs.readFileSync(path.join(__dirname,'app.js'),'utf8');
for(const m of js.matchAll(/\$\('([^']+)'\)/g))assert(page.includes('id="'+m[1]+'"'),'Missing DOM id '+m[1]);
assert(fs.existsSync(path.join(__dirname,'manifest.webmanifest')));
assert(fs.existsSync(path.join(__dirname,'install.js')),'PWA install script');
assert(page.includes('id="pwa-install"'),'PWA install button');
const manifest=JSON.parse(fs.readFileSync(path.join(__dirname,'manifest.webmanifest'),'utf8'));
for(const size of ['192x192','512x512'])assert(manifest.icons.some(x=>x.sizes===size&&x.type==='image/png'),'PWA PNG icon '+size);
const backup=require('./tasks-backup.js');
assert(page.includes('id="import-tasks"'),'Backup import button missing');
assert(page.includes('id="import-tasks-file"'),'Backup import file picker missing');
assert(page.includes('id="import-status"'),'Accessible import feedback missing');
assert(page.indexOf('src="./tasks-backup.js"')<page.indexOf('src="./app.js"'),'Backup parser must load before app');
assert(fs.readFileSync(path.join(__dirname,'sw.js'),'utf8').includes("'./tasks-backup.js'"),'Offline PWA must cache the backup parser');
const good={format:'nikoassist-tasks-v1',tasks:[
 {id:'external-id-should-not-be-trusted',text:'  Préparer le tournage  ',done:false},
 {id:'again',text:'Réviser le montage',done:true}
]};
const parsed=backup.parse(JSON.stringify(good));
assert.deepEqual(parsed,[{text:'Préparer le tournage',done:false},{text:'Réviser le montage',done:true}],'Only title and state should be imported');
const current=[{id:'local',text:'préparer le tournage',done:true}];
const before=JSON.stringify(current);
const plan=backup.previewMerge(current,parsed);
assert.equal(plan.duplicates,1);
assert.deepEqual(plan.toAdd,[{text:'Réviser le montage',done:true}]);
assert.equal(JSON.stringify(current),before,'Import must preserve existing task data');
assert.throws(()=>backup.parse(JSON.stringify({format:'untrusted',tasks:[]})),/export de tâches/);
assert.throws(()=>backup.parse(JSON.stringify({format:'nikoassist-tasks-v1',tasks:[{text:'A',done:'yes'}]})),/Tâche invalide/);
assert.throws(()=>backup.parse(JSON.stringify({format:'nikoassist-tasks-v1',tasks:[{text:'x'.repeat(161),done:false}]})),/Tâche invalide/);
assert.throws(()=>backup.parse(JSON.stringify({format:'nikoassist-tasks-v1',tasks:new Array(201).fill({text:'A',done:false})})),/export de tâches/);
assert.throws(()=>backup.parse('{invalid'),/JSON valide/);
const filled=Array.from({length:200},(_,i)=>({text:'Tâche '+i,done:false}));
assert.equal(backup.previewMerge(filled,parsed).toAdd.length,0,'Import must respect 200 task limit');
console.log('PASS NikoAssist Web static + API syntax, portable backup, dedupe and controls');
