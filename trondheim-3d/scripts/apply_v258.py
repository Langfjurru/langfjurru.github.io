#!/usr/bin/env python3
"""Trondheim 3D v2.58: additive favorites overlay on existing v2.57 GitHub source.

Safe rules: refuse non-v2.57 sources, preserve existing scripts and realtime engines,
write atomically, and be idempotent. All UI resources are embedded in this script.
"""
from __future__ import annotations
import pathlib
import re
import sys
import tempfile

STAMP = 'V258_FAVORITES_BEGIN'
STYLE = r'''/* V258_FAVORITES_BEGIN: additive styling; original map styles stay unchanged. */
.v258-fav-star{display:inline-flex;align-items:center;justify-content:center;flex:none;width:34px;height:34px;min-width:34px;border:1px solid #dce6e8;border-radius:10px;background:#edf3f5;color:#667b84;font:800 20px/1 system-ui;cursor:pointer;touch-action:manipulation}
.v258-fav-star.is-saved{color:#bb7a08;background:#fff2cd;border-color:#efd296}
.v258-fav-star:focus-visible,.v258-fav-launch:focus-visible,.v258-fav-close:focus-visible,.v258-fav-item:focus-visible,.v258-fav-remove:focus-visible{outline:3px solid #e9a72c;outline-offset:2px}
.v258-fav-launch{position:fixed;right:13px;bottom:calc(103px + env(safe-area-inset-bottom,0px));z-index:31;width:46px;height:46px;border:1px solid #e7dbb9;border-radius:15px;background:#fffef9;color:#8b690f;box-shadow:0 5px 20px #122e3642;font:800 24px system-ui;touch-action:manipulation}
.v258-fav-launch small{position:absolute;right:-3px;top:-5px;display:grid;place-items:center;min-width:17px;height:17px;padding:0 4px;border-radius:50px;background:#b17113;color:white;font:700 10px system-ui}
.v258-fav-launch small[hidden]{display:none}
.v258-fav-panel{position:fixed;z-index:32;right:12px;bottom:calc(156px + env(safe-area-inset-bottom,0px));width:min(335px,calc(100vw - 24px));max-height:min(55dvh,390px);overflow:auto;border:1px solid #dde8e9;border-radius:18px;background:#fffffffa;color:#25383d;box-shadow:0 12px 42px #142e3850;padding:13px 13px 10px;backdrop-filter:blur(14px);overscroll-behavior:contain}
.v258-fav-panel[hidden]{display:none!important}
.v258-fav-head{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:8px}.v258-fav-head strong{font-size:15px}.v258-fav-close{height:32px;width:32px;border:0;border-radius:9px;background:#edf2f3;color:#4c5e63;font-size:20px}
.v258-fav-hint{margin:0 0 10px;font-size:11px;line-height:1.45;color:#60737b}.v258-fav-empty{padding:15px 5px 18px;text-align:center;color:#61727b;font-size:12px}
.v258-fav-row{display:flex;align-items:center;gap:8px;border-top:1px solid #edf0f1;padding:7px 0}.v258-fav-item{flex:1;min-width:0;text-align:left;border:0;background:transparent;padding:5px 3px;color:#264956;cursor:pointer}.v258-fav-item strong{font-size:12px;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v258-fav-item small{font-size:10px;color:#617781;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:2px}.v258-fav-remove{width:33px;height:33px;flex:none;border:0;border-radius:9px;background:#fff3d8;color:#aa740e;font-size:20px;cursor:pointer}
.v258-fav-toast{position:fixed;z-index:70;right:12px;bottom:calc(167px + env(safe-area-inset-bottom,0px));max-width:min(320px,calc(100vw - 24px));padding:10px 13px;border-radius:11px;color:white;background:#294b57;box-shadow:0 5px 19px #0004;font:600 12px/1.4 system-ui;pointer-events:none}
.v258-fav-toast[hidden]{display:none!important}
body.route-focus .v258-fav-launch{bottom:calc(var(--route-sheet-height,178px) + 21px + env(safe-area-inset-bottom,0px))}
body.route-focus .v258-fav-panel{bottom:calc(var(--route-sheet-height,178px) + 70px + env(safe-area-inset-bottom,0px))}
@media(max-width:640px){.v258-fav-launch{right:10px;width:43px;height:43px;bottom:calc(70px + env(safe-area-inset-bottom,0px))}.v258-fav-panel{right:9px;bottom:calc(119px + env(safe-area-inset-bottom,0px));max-height:min(49dvh,350px)}.v258-fav-toast{bottom:calc(128px + env(safe-area-inset-bottom,0px))}}
/* V258_FAVORITES_END */'''
SCRIPT = r'''/* V258_FAVORITES_BEGIN: self-contained, does not alter realtime polling or map rendering. */
(function(){
 'use strict';
 if(window.TrondheimFavoritesV258)return;
 const STORAGE_KEY='trondheim3d.favorites.v1';
 const MAX_FAVORITES=60;
 const $f=id=>document.getElementById(id);
 let items=[];
 let storageAvailable=true;
 function load(){try{const raw=localStorage.getItem(STORAGE_KEY);if(!raw)return [];const a=JSON.parse(raw);return Array.isArray(a)?a.filter(f=>f&&typeof f.key==='string'&&['stop','tramstop','bus','ferry','fastboat','harbour','vanvikan','ferry244'].includes(f.kind)&&f.key.length<150).slice(0,MAX_FAVORITES):[];}catch(e){storageAvailable=false;console.warn('Favoritter: lokal lagring ikke tilgjengelig',e);return [];}}
 items=load();
 function save(){try{localStorage.setItem(STORAGE_KEY,JSON.stringify(items));storageAvailable=true;}catch(e){storageAvailable=false;toast('Favoritten fungerer nå, men nettleseren tillater ikke varig lagring.');console.warn('Favoritter: kunne ikke lagre lokalt',e);}}
 function el(tag,classes,text){const node=document.createElement(tag);if(classes)node.className=classes;if(text!==undefined)node.textContent=text;return node;}
 function cleanText(value,max=120){return String(value||'').trim().slice(0,max);}
 function goodCoords(pos){return Array.isArray(pos)&&pos.length>=2&&Number.isFinite(+pos[0])&&Number.isFinite(+pos[1])&&+pos[0]>=3&&+pos[0]<=34&&+pos[1]>=55&&+pos[1]<=73;}
 const exist=key=>items.some(f=>f.key===key);
 let toastTimer=0;
 const t=el('div','v258-fav-toast');t.hidden=true;t.setAttribute('role','status');document.body.appendChild(t);
 function toast(message){t.textContent=message;t.hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>t.hidden=true,2800);}
 const launch=el('button','v258-fav-launch','☆');launch.type='button';launch.setAttribute('aria-label','Vis favoritter');launch.title='Mine favoritter';
 const counter=el('small','');counter.hidden=true;launch.append(counter);
 const panel=el('section','v258-fav-panel');panel.hidden=true;panel.setAttribute('aria-label','Mine favoritter');
 const head=el('div','v258-fav-head');const label=el('strong','', '★ Mine favoritter');const close=el('button','v258-fav-close','×');close.type='button';close.setAttribute('aria-label','Lukk favoritter');head.append(label,close);panel.append(head);
 panel.append(el('p','v258-fav-hint','Trykk på en favoritt for å åpne den. Trykk på ★ igjen for å fjerne den. Lagres bare på denne enheten.'));
 const list=el('div','v258-fav-list');panel.append(list);
 document.body.append(launch,panel);
 function updateCounter(){counter.textContent=String(items.length);counter.hidden=items.length===0;launch.setAttribute('aria-label','Vis favoritter, '+items.length+' lagret');}
 function closePanel(){panel.hidden=true;launch.setAttribute('aria-expanded','false');}
 function togglePanel(){panel.hidden=!panel.hidden;launch.setAttribute('aria-expanded',String(!panel.hidden));if(!panel.hidden)renderList();}
 launch.setAttribute('aria-expanded','false');launch.setAttribute('aria-controls','v258-favorites-panel');panel.id='v258-favorites-panel';launch.addEventListener('click',ev=>{ev.stopPropagation();togglePanel();});close.addEventListener('click',closePanel);
 document.addEventListener('keydown',ev=>{if(ev.key==='Escape')closePanel();});
 document.addEventListener('pointerdown',ev=>{if(!panel.hidden&&!panel.contains(ev.target)&&!launch.contains(ev.target))closePanel();},{passive:true});
 function currentStop(){
  const s=(typeof boardState!=='undefined'&&boardState&&boardState.stop)||null;
  if(!s||!/^NSR:(StopPlace|Quay):/.test(s.id||''))return null;
  const o={kind:'stop',key:'stop:'+s.id,id:String(s.id),name:'🚌 '+cleanText(s.name||'Holdeplass'),detail:'Bussavganger',parentId:s.parentId||null,platform:s.platform||''};if(goodCoords(s.coords))o.coords=[+s.coords[0],+s.coords[1]];return o;
 }
 function currentTramStop(){
  const s=window.__TrondheimFavoritesTramV258?.current?.();
  if(!s||!/^NSR:(StopPlace|Quay):/.test(s.id||''))return null;
  const o={kind:'tramstop',key:'tramstop:'+s.id,id:String(s.id),name:'🚊 '+cleanText(s.name||'Trikkeholdeplass'),detail:'Linje 9 · trikkeavganger',parentId:s.parentId||null,platform:s.platform||''};if(goodCoords(s.coords))o.coords=[+s.coords[0],+s.coords[1]];return o;
 }
 function currentBus(){
  const title=$f('route-title')?.textContent||'';
  const m=title.match(/^Buss\s+(.+?)\s+·/i);
  if(!m)return null;
  const line=cleanText(m[1],35);
  if(!line||line==='–'||/hentar|rute/i.test(line))return null;
  let destination='';try{destination=cleanText((typeof selectedBusRoute!=='undefined'&&selectedBusRoute?.route?.end)||$f('route-to')?.textContent||'');}catch(e){destination=cleanText($f('route-to')?.textContent||'');}
  if(/^(sjekkar|hentar|ukjend|ukjent)/i.test(destination))destination='';
  return {kind:'bus',key:'bus:'+line.toLowerCase(),id:line,name:'🚌 Buss '+line,detail:destination?'Mot '+destination:'Busslinje '+line,destination};
 }
 function currentFerry(){return {kind:'ferry',key:'ferry:880',id:'880',name:'⛴️ Ferge 880',detail:'Flakk–Rørvik'};}
 function currentFastboat(){
  const selection=window.__TrondheimFavoritesFastboatV258?.current?.();if(!selection)return null;
  const code=cleanText(selection.code,20),quay=cleanText(selection.quay,90);
  if(quay)return {kind:'fastboat',key:'fastboat:quay:'+quay,id:quay,quay,name:'⛴️ '+cleanText($f('fastboat-title')?.textContent||'Hurtigbåtkai'),detail:'Avganger fra valgt kai'};
  if(code)return {kind:'fastboat',key:'fastboat:line:'+code,id:code,code,name:'⛴️ Hurtigbåt '+code,detail:'Rute '+code};
  return {kind:'fastboat',key:'fastboat:terminal',id:'terminal',name:'⛴️ Trondheim hurtigbåtterminal',detail:'Hurtigbåtavganger'};
 }
 function currentHarbour(){
  const s=window.__TrondheimFavoritesHarbourV258?.current?.();if(!s||!String(s.id||'').startsWith('NSR:'))return null;
  const out={kind:'harbour',key:'harbour:'+s.id,id:String(s.id),name:'⛴️ '+cleanText(s.name||$f('harbour-title')?.textContent||'Hurtigbåtkai'),detail:'Hurtigbåtavganger',publicCode:s.publicCode||'',stopPlaceId:s.stopPlace?.id||'',stopPlaceName:s.stopPlace?.name||s.name||''};
  const lng=Number(s.longitude),lat=Number(s.latitude);if(goodCoords([lng,lat]))out.coords=[lng,lat];return out;
 }
 function currentVanvikan(){return {kind:'vanvikan',key:'vanvikan:water',id:'vanvikan',name:'⛴️ Vanvikan–Trondheim',detail:'Hurtigbåtavganger og reisetid'};}
 function currentFerry244(){
  const s=window.__TrondheimFavoritesFerry244V258?.current?.();const code=cleanText(s?.code,25);
  if(!code)return null;
  return {kind:'ferry244',key:'ferry244:'+code,id:code,name:'⛴️ Ferge '+code,detail:'Fergeavganger og reiseretning'};
 }

 function cardConfig(id){
  const c=$f(id);if(!c||c.hidden)return null;
  if(id==='departure-card')return currentStop();
  if(id==='tram-board')return currentTramStop();
  if(id==='selected-route-card')return currentBus();
  if(id==='ferry-card')return currentFerry();
  if(id==='fastboat-board')return currentFastboat();
  if(id==='harbour-board')return currentHarbour();
  if(id==='vanvikan-board')return currentVanvikan();
  if(id==='ferry244-card')return currentFerry244();
  return null;
 }
 function toggleFavorite(item){
  if(!item?.key)return;
  const i=items.findIndex(f=>f.key===item.key);
  if(i>=0){items.splice(i,1);toast('Fjernet fra favoritter');}
  else{if(items.length>=MAX_FAVORITES){toast('Maks '+MAX_FAVORITES+' favoritter. Fjern en før du legger til flere.');return;}items.push(item);toast('Lagt til i favoritter');}
  save();updateCounter();renderList();syncStars();
 }
 const cardIds=['departure-card','tram-board','selected-route-card','ferry-card','fastboat-board','harbour-board','vanvikan-board','ferry244-card'];
 function syncStars(){
  for(const id of cardIds){const c=$f(id);if(!c)continue;const btn=c.querySelector('.v258-fav-star');if(!btn)continue;
   const cur=cardConfig(id);const saved=cur&&exist(cur.key);
   const display=!!cur;
   if(btn.hidden===display)btn.hidden=!display;
   if(btn.classList.contains('is-saved')!==!!saved)btn.classList.toggle('is-saved',!!saved);
   const aria=saved?'Fjern fra favoritter':'Legg til i favoritter';if(btn.getAttribute('aria-label')!==aria)btn.setAttribute('aria-label',aria);
   const next=saved?'★':'☆';if(btn.textContent!==next)btn.textContent=next;
  }
 }
 function setupStars(){
  const config=[['selected-route-card','.route-top','#route-close'],['departure-card','.departure-actions','#departure-refresh'],['tram-board','.departure-actions','#tram-board-refresh'],['ferry-card','.ferry-actions','#ferry-close'],['fastboat-board','.departure-actions','#fastboat-refresh'],['harbour-board','.departure-actions','#harbour-refresh'],['vanvikan-board','.departure-actions','#vanvikan-refresh'],['ferry244-card','.ferry-actions','#ferry244-refresh']];
  for(const [id,holderSelector,beforeSelector] of config){const card=$f(id),holder=card?.querySelector(holderSelector);if(!holder||card.querySelector('.v258-fav-star'))continue;
   const b=el('button','v258-fav-star','☆');b.type='button';b.hidden=true;b.title='Legg til eller fjern favoritt';
   b.addEventListener('click',ev=>{ev.preventDefault();ev.stopPropagation();const s=cardConfig(id);if(s)toggleFavorite(s);});
   holder.insertBefore(b,card.querySelector(beforeSelector)||null);
   const ob=new MutationObserver(()=>{if(!card.hidden)syncStars();else if(!b.hidden)b.hidden=true;});
   ob.observe(card,{attributes:true,attributeFilter:['hidden']});
   const title=card.querySelector('h3');if(title)ob.observe(title,{subtree:true,childList:true,characterData:true});
   if(id==='selected-route-card'){
    const target=$f('route-to');if(target)ob.observe(target,{subtree:true,childList:true,characterData:true});
   }
  }
  syncStars();
 }
 function findBusToOpen(fav){
  const arr=(typeof state!=='undefined'&&Array.isArray(state.bus))?state.bus:[];
  const candidates=arr.filter(f=>String(f.properties?.line||'').trim().toLowerCase()===fav.id.toLowerCase()&&f.properties?.vehicleId);
  if(!candidates.length)return null;
  const dest=cleanText(fav.destination).toLowerCase();
  const primary=candidates.find(f=>dest&&[f.properties?.destinationName,f.properties?.route].some(s=>cleanText(s).toLowerCase().includes(dest)))||candidates[0];
  return primary.properties.vehicleId;
 }
 function panToCoords(fav){if(goodCoords(fav.coords)&&typeof map!=='undefined'&&map?.flyTo){try{map.flyTo({center:fav.coords,zoom:Math.max(map.getZoom(),14.5),duration:800,essential:true});}catch(e){console.warn('Favorittkart',e);}}}
 function openFavorite(fav){
  closePanel();
  try{
   if(fav.kind==='stop'){
    if(typeof selectStopPlace!=='function')throw Error('Holdeplassvisningen er ikke tilgjengelig');
    selectStopPlace({id:fav.id,name:fav.name.replace(/^🚌\s*/,''),coords:fav.coords||null,parentId:fav.parentId||null,platform:fav.platform||''});panToCoords(fav);return;
   }
   if(fav.kind==='tramstop'){
    const open=window.__TrondheimFavoritesTramV258?.open;if(typeof open!=='function')throw Error('Trikkemodulen er ikke klar');
    open({id:fav.id,name:fav.name.replace(/^🚊\s*/,''),coords:fav.coords||null,parentId:fav.parentId||null,platform:fav.platform||''});panToCoords(fav);return;
   }
   if(fav.kind==='bus'){
    if(typeof selectBusRoute!=='function')throw Error('Bussvisningen er ikke tilgjengelig');
    const vehicleId=findBusToOpen(fav);if(!vehicleId){toast('Ingen aktiv buss '+fav.id+' i innlastet kartområde akkurat nå.');return;}
    selectBusRoute(String(vehicleId));return;
   }
   if(fav.kind==='ferry'){
    if(typeof openFerryCard!=='function')throw Error('Fergevisningen er ikke tilgjengelig');
    openFerryCard({});return;
   }
   if(fav.kind==='fastboat'){
    const open=window.__TrondheimFavoritesFastboatV258?.open;
    if(typeof open!=='function')throw Error('Hurtigbåtmodulen er ikke klar');
    open({quay:fav.quay||null,code:fav.code||null,vessel:null});return;
   }
   if(fav.kind==='harbour'){
    const open=window.__TrondheimFavoritesHarbourV258?.open;
    if(typeof open!=='function')throw Error('Hurtigbåtkaiene er ikke tilgjengelige');
    const pos=goodCoords(fav.coords)?fav.coords:[];
    open({id:fav.id,name:fav.name.replace(/^⛴️\s*/,''),publicCode:fav.publicCode||'',longitude:pos[0],latitude:pos[1],stopPlace:{id:fav.stopPlaceId||'',name:fav.stopPlaceName||''}});panToCoords(fav);return;
   }
   if(fav.kind==='vanvikan'){
    const btn=$f('vanvikan-open');if(!btn)throw Error('Vanvikan-tavlen finnes ikke');
    btn.click();return;
   }
   if(fav.kind==='ferry244'){
    const open=window.__TrondheimFavoritesFerry244V258?.open;
    if(typeof open!=='function')throw Error('Fergemodulen er ikke klar');
    open({line:fav.id},false);return;
   }
  }catch(e){console.warn('Favoritt kunne ikke åpnes',e);toast('Kunne ikke åpne favoritten: '+e.message);}
 }
 function renderList(){list.replaceChildren();if(!items.length){list.append(el('div','v258-fav-empty','Ingen favoritter ennå. Velg en holdeplass eller kollektivrute i kartet og trykk ☆.'));return;}
  for(const fav of items){const row=el('div','v258-fav-row'),b=el('button','v258-fav-item'),name=el('strong','',fav.name||fav.id),details=el('small','',fav.detail||'');b.type='button';b.append(name,details);b.title='Åpne '+(fav.name||fav.id);b.addEventListener('click',()=>openFavorite(fav));
   const remove=el('button','v258-fav-remove','★');remove.type='button';remove.setAttribute('aria-label','Fjern '+(fav.name||fav.id)+' fra favoritter');remove.title='Fjern favoritt';remove.addEventListener('click',ev=>{ev.stopPropagation();toggleFavorite(fav);});row.append(b,remove);list.append(row);}
 }
 document.addEventListener('DOMContentLoaded',()=>{setupStars();updateCounter();renderList();},{once:true});
 if(document.readyState!=='loading'){setupStars();updateCounter();renderList();}
 window.TrondheimFavoritesV258={get:()=>items.map(x=>({...x})),has:exist};
})();
/* V258_FAVORITES_END */'''
TRAM_ANCHOR = "tramSwitch.addEventListener('change',onTramToggle);"
TRAM_BRIDGE = "window.__TrondheimFavoritesTramV258={open:(item)=>openTramBoard(item),current:()=>tramBoardStop};\n "


def replace_once(text: str, pattern: str, replacement: str, flags=0) -> str:
    out, count = re.subn(pattern, replacement, text, count=1, flags=flags)
    if count != 1:
        raise ValueError(f'STOP: expected anchor not found: {pattern}')
    return out


def patch(original: str) -> str:
    if original.count('/* V258_FAVORITES_BEGIN: additive styling') == 1 and original.count('/* V258_FAVORITES_BEGIN: self-contained') == 1:
        if re.search(r'<meta\s+name="app-version"\s+content="2\.58"', original):
            return original
        raise ValueError('STOP: partly installed v2.58, refusing second patch')
    if STAMP in original:
        raise ValueError('STOP: partially installed favorites module')
    version = re.search(r'<meta\s+name="app-version"\s+content="([^"]+)"', original)
    if version is None or version.group(1) != '2.57':
        raise ValueError('STOP: source must be published v2.57, not '+(version.group(1) if version else 'unversioned'))
    if original.count('</head>') != 1 or original.count('</body>') != 1:
        raise ValueError('STOP: invalid HTML document anchors')
    required = ('selected-route-card','route-title','departure-card','departure-title','ferry-card',
                'function selectBusRoute(', 'function selectStopPlace(', 'function openFerryCard(')
    for anchor in required:
        if anchor not in original:
            raise ValueError('STOP: expected unchanged v2.57 function or UI not found: '+anchor)
    new = replace_once(original, r'(<meta\s+name="app-version"\s+content=")2\.57(")', r'\g<1>2.58\2')
    new = replace_once(new, r'(<title>[^<]*?)v2\.57(?:\s*(?:YTELSE\s*TEST|TEST))?([^<]*</title>)', r'\g<1>v2.58\2', re.I)
    # Clean the version displayed to the visitor, without renaming stable internal v255/v257 anchors.
    new = re.sub(r'(aria-label="Versjon )2\.57', r'\g<1>2.58', new, count=1)
    new = re.sub(r'(<span\s+class="release-tag"[^>]*>)v2\.57(?:\s*(?:YTELSE\s*TEST|TEST))?(</span>)',r'\g<1>v2.58\2',new,count=1,flags=re.I)
    new = new.replace('Kartprototype v2.57','Kartprototype v2.58')
    new = new.replace('3D Trondheim · v2.57','3D Trondheim · v2.58')
    new = new.replace('v2.57 YTELSE TEST','v2.58')
    # Bridge is added only when current tram implementation matches v2.51+.
    # If unavailable, bus/stop/ferry favorites still work, and existing tram code is untouched.
    if TRAM_ANCHOR in new and 'function openTramBoard(stop)' in new:
        new = new.replace(TRAM_ANCHOR, TRAM_BRIDGE + TRAM_ANCHOR, 1)
    # Optional additive accessors for existing isolated transport modules.
    # Their original data fetching, animations, and renderers remain untouched.
    boats_anchor = " const headers={'Content-Type':'application/json','ET-Client-Name':'langfjurru-trondheim3d-fastboat'};"
    if boats_anchor in new and "const card=$('fastboat-board')" in new:
        new = new.replace(boats_anchor, " window.__TrondheimFavoritesFastboatV258={open:(q)=>open(q),current:()=>selection};\n"+boats_anchor,1)
    quay_anchor = ' function open(q){selected=q;card.hidden=false;clearRoute();'
    if quay_anchor in new and "const card=$('harbour-board')" in new:
        new = new.replace(quay_anchor, " window.__TrondheimFavoritesHarbourV258={open:(q)=>open(q),current:()=>selected};\n"+quay_anchor,1)
    ferry_anchor = ' async function open(props={},fit=true){'
    if ferry_anchor in new and "card=$('ferry244-card')" in new:
        new = new.replace(ferry_anchor, " window.__TrondheimFavoritesFerry244V258={open:(p,fit)=>open(p,fit),current:()=>selected};\n"+ferry_anchor,1)
    new = new.replace('</head>', '<style id="v258-favorites-style">\n'+STYLE+'\n</style>\n</head>', 1)
    new = new.replace('</body>', '<script id="v258-favorites-script">\n'+SCRIPT+'\n</script>\n</body>', 1)
    if not re.search(r'<meta\s+name="app-version"\s+content="2\.58"',new):
        raise ValueError('STOP: version update failed')
    if new.count('id="v258-favorites-script"') != 1 or new.count('id="v258-favorites-style"') != 1:
        raise ValueError('STOP: duplicate favorite module')
    return new


def main() -> None:
    if len(sys.argv) not in (2,3):
        raise SystemExit('Usage: python3 apply_v258.py path/to/index.html [output.html]')
    src=pathlib.Path(sys.argv[1]);dst=pathlib.Path(sys.argv[2]) if len(sys.argv)==3 else src
    old=src.read_text(encoding='utf-8');new=patch(old)
    if old==new:
        print('OK: v2.58 already installed; no changes')
        return
    if dst==src:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=src.parent,prefix='.v258-',suffix='.tmp',delete=False) as f:
            f.write(new);tmp=pathlib.Path(f.name)
        tmp.replace(src)
    else:dst.write_text(new,encoding='utf-8')
    print('OK: installed v2.58 favorites, version label and localStorage without replacing main app code')

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('ERROR:',exc,file=sys.stderr)
        raise SystemExit(1)
