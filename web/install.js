(()=>{
'use strict';
const button=document.getElementById('pwa-install');
const dialog=document.getElementById('pwa-install-dialog');
const info=document.getElementById('pwa-install-guide');
const close=document.getElementById('pwa-install-close');
const status=document.getElementById('pwa-install-status');
if(!button||!dialog||!info||!close)return;
let promptEvent=null;
const standalone=()=>window.matchMedia('(display-mode: standalone)').matches||navigator.standalone===true;
function currentInstructions(){
 const ua=navigator.userAgent||'';
 if(/iPhone|iPad|iPod/i.test(ua))
  return 'Sur iPhone ou iPad, ouvrez ce site dans Safari, appuyez sur Partager, puis choisissez « Sur l’écran d’accueil » et « Ajouter ». Les autres navigateurs iOS peuvent proposer une option différente.';
 if(/Android/i.test(ua))
  return 'Sur Android, ouvrez ce site dans Chrome puis appuyez sur ⋮ → « Installer l’application » ou « Ajouter à l’écran d’accueil » (libellé selon la version). Dans Samsung Internet, utilisez le menu du navigateur et l’option d’ajout à l’écran d’accueil.';
 return 'Sur Chrome ou Edge, utilisez l’icône Installer dans la barre d’adresse ou le menu ⋮ → « Installer l’application ». Sur Safari macOS, utilisez Fichier → Ajouter au Dock. Certains navigateurs n’installent qu’un raccourci.';
}
function showGuide(message){
 info.textContent=message||currentInstructions();
 if(typeof dialog.showModal==='function')dialog.showModal();
 else dialog.setAttribute('open','');
}
function markInstalled(){
 button.textContent='Application installée ✓';
 button.disabled=true;
 if(status)status.textContent='Application installée sur cet appareil.';
}
if(standalone())markInstalled();
window.addEventListener('beforeinstallprompt',event=>{
 event.preventDefault();
 promptEvent=event;
 if(!standalone()){
  button.textContent='Installer la PWA ↓';
  if(status)status.textContent='Installation disponible dans ce navigateur.';
 }
});
window.addEventListener('appinstalled',()=>{promptEvent=null;markInstalled();});
button.addEventListener('click',()=>{
 if(standalone()){markInstalled();return;}
 if(!promptEvent){showGuide();return;}
 const event=promptEvent;promptEvent=null;
 try{
  event.prompt();
  event.userChoice.then(choice=>{
   if(choice?.outcome==='accepted'){if(status)status.textContent='Installation acceptée, finalisation par le navigateur.';}
   else {if(status)status.textContent='Installation annulée. Réessayez via le menu de votre navigateur.';}
  }).catch(()=>showGuide());
 }catch{showGuide();}
});
close.addEventListener('click',()=>{if(typeof dialog.close==='function')dialog.close();else dialog.removeAttribute('open');});
dialog.addEventListener('click',e=>{if(e.target===dialog&&typeof dialog.close==='function')dialog.close();});
})();
