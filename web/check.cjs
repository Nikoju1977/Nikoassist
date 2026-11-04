'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
for(const name of ['app.js','sw.js','api/assistant.js','api/health.js']){
 const content=fs.readFileSync(path.join(__dirname,name),'utf8');
 new Function('module','require','process',content);
}
const page=fs.readFileSync(path.join(__dirname,'index.html'),'utf8');
const js=fs.readFileSync(path.join(__dirname,'app.js'),'utf8');
for(const m of js.matchAll(/\$\('([^']+)'\)/g))assert(page.includes('id="'+m[1]+'"'),'Missing DOM id '+m[1]);
assert(fs.existsSync(path.join(__dirname,'manifest.webmanifest')));
console.log('PASS NikoAssist Web static + API syntax and controls');
