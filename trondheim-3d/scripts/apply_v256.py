#!/usr/bin/env python3
"""Safe and idempotent v2.55 -> v2.56 streetlight-only upgrade.

Changes only lamp selection, projected visibility, and version tags.
Keeps all other Trondheim 3D systems and the v2.55 OSM GeoJSON setup unchanged.
"""
from __future__ import annotations
import pathlib
import re
import sys

STAMP = 'V256_BUILDING_MASK_V1'

HELPERS = r''' // V256_BUILDING_MASK_V1: exclude all lamps from building polygons; conservative 3D screen occlusion.
 // Uses the already-loaded OpenFreeMap building source. No new fetches, external libraries, or worker.
 function v256Footprints(sx,sy){
  const grid=new Map(),cell=32,buildings=[];
  let rows=[];
  try{if(map.getSource('buildings-source'))rows=map.querySourceFeatures('buildings-source',{sourceLayer:'building'})||[];}catch(e){console.warn('Gatelys bygningsgeometri',e);}
  function add(poly){
   if(!poly?.length||!Array.isArray(poly[0])||poly[0].length<4)return;
   const rings=poly.map(r=>r.map(p=>[(p[0]-10.4)*sx,(p[1]-63.43)*sy]));
   if(!rings[0]?.length)return;
   const a=rings[0];let loX=Infinity,loY=Infinity,hiX=-Infinity,hiY=-Infinity;
   for(const p of a){if(!Number.isFinite(p[0])||!Number.isFinite(p[1]))return;
    loX=Math.min(loX,p[0]);loY=Math.min(loY,p[1]);hiX=Math.max(hiX,p[0]);hiY=Math.max(hiY,p[1]);}
   if(hiX-loX>1500||hiY-loY>1500)return;
   const rec={rings,loX,loY,hiX,hiY};buildings.push(rec);
   const x0=Math.floor((loX-4)/cell),x1=Math.floor((hiX+4)/cell),y0=Math.floor((loY-4)/cell),y1=Math.floor((hiY+4)/cell);
   if((x1-x0+1)*(y1-y0+1)>1500)return;
   for(let x=x0;x<=x1;x++)for(let y=y0;y<=y1;y++){
    const key=x+':'+y;if(!grid.has(key))grid.set(key,[]);grid.get(key).push(rec);
   }
  }
  for(const f of rows){const g=f.geometry;
   if(g?.type==='Polygon')add(g.coordinates);
   else if(g?.type==='MultiPolygon')for(const poly of g.coordinates)add(poly);
  }
  const ready=rows.length>0||(map.getSource('buildings-source')&&map.isSourceLoaded('buildings-source'));
  return {grid,cell,sx,sy,ready:Boolean(ready),count:buildings.length};
 }
 function v256InRing(x,y,ring){
  let inside=false;
  for(let i=0,j=ring.length-1;i<ring.length;j=i++){
   const a=ring[i],b=ring[j];
   if((a[1]>y)!==(b[1]>y)&&x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0])inside=!inside;
  }
  return inside;
 }
 function v256NearRing(x,y,ring,buffer){
  const r2=buffer*buffer;
  for(let i=0,j=ring.length-1;i<ring.length;j=i++){
   const a=ring[i],b=ring[j],dx=b[0]-a[0],dy=b[1]-a[1],d=dx*dx+dy*dy;
   if(d<0.001)continue;
   const t=clamp(((x-a[0])*dx+(y-a[1])*dy)/d,0,1);
   if((x-a[0]-t*dx)**2+(y-a[1]-t*dy)**2<r2)return true;
  }
  return false;
 }
 function v256ClearBuilding(p,buffer,idx){
  // A no-data result must not be confused with an explicitly clear footprint.
  if(!idx.ready)return false;
  const x=(p[0]-10.4)*idx.sx,y=(p[1]-63.43)*idx.sy;
  const cx=Math.floor(x/idx.cell),cy=Math.floor(y/idx.cell);
  const inspected=new Set();
  for(let ox=-1;ox<=1;ox++)for(let oy=-1;oy<=1;oy++)for(const building of idx.grid.get((cx+ox)+':'+(cy+oy))||[]){
   if(inspected.has(building))continue;inspected.add(building);
   if(x<building.loX-buffer||x>building.hiX+buffer||y<building.loY-buffer||y>building.hiY+buffer)continue;
   const rings=building.rings;
   if(v256InRing(x,y,rings[0])&&!rings.slice(1).some(hole=>v256InRing(x,y,hole)))return false;
   if(v256NearRing(x,y,rings[0],buffer))return false;
  }
  return true;
 }
 function v256HiddenBy3D(p){
  // On a pitched map, canvas poles cannot be depth-tested against GL buildings.
  // Suppress a pole when its ground anchor is visually hidden by a 3D extrusion.
  if(map.getPitch()<22)return false;
  const layers=['building-extrude','building-facade-detail','building-roof-cap'].filter(id=>{
   try{return map.getLayer(id)&&map.getLayoutProperty(id,'visibility')!=='none';}catch(_){return false;}
  });
  if(!layers.length)return false;
  try{const pixel=map.project(p);return map.queryRenderedFeatures([pixel.x,pixel.y],{layers}).length>0;}
  catch(_){return false;}
 }
'''


def patch(text: str) -> str:
    if STAMP in text:
        return text
    if "LAMP_REGISTRY_URL" not in text or 'function v255GenerateLamps(){' not in text:
        raise ValueError('STOP: v2.55 streetlight engine not found; index.html was not modified.')
    if not re.search(r'v2\.55(?:\s+TEST|\b)', text[:20000], re.I):
        raise ValueError('STOP: the visible HTML header does not confirm v2.55.')
    start = text.find(' function v255GenerateLamps(){')
    end = text.find(' function scanLamps(){', start)
    if start < 0 or end < 0 or text.find(' function v255GenerateLamps(){', start+5)>=0:
        raise ValueError('STOP: unexpected v2.55 streetlight generator structure.')
    local = text[start:end]
    source = local
    # Get a single building polygon index for each scan, never requery inside candidate loops.
    local = local.replace('  const sx=111320*Math.cos(center.lat*RAD),sy=111320;',
        '  const sx=111320*Math.cos(center.lat*RAD),sy=111320;\n  const buildingMask=v256Footprints(sx,sy);', 1)
    # Honor OSM locations, but never show streetlamps inside actual building geometry.
    local = local.replace('   const p=entry.pole;\n',
        '   const p=entry.pole;\n   if(!v256ClearBuilding(p,0.9,buildingMask))continue;\n', 1)
    # Side of road selection: use canonical preferred side, then the opposite side when obstructed.
    old = '    const pole=[10.4+(x-side*ty*offset)/sx,63.43+(y+side*tx*offset)/sy];'
    new = '''    let pole=null;
    for(const sgn of [side,-side]){
     const candidate=[10.4+(x-sgn*ty*offset)/sx,63.43+(y+sgn*tx*offset)/sy];
     if(v256ClearBuilding(candidate,2.5,buildingMask)){pole=candidate;break;}
    }
    if(!pole)continue;'''
    local = local.replace(old,new,1)
    # Avoid canvas poles drawn over the visible roof surface. For speed, only query after
    # the final candidate set has been capped, not inside the generation loops.
    local = local.replace('  return out;\n',
        '  return out.filter(f=>!v256HiddenBy3D(f.pole));\n', 1)
    if local == source or 'const buildingMask=v256Footprints' not in local or 'for(const sgn of [side,-side])' not in local or 'out.filter(f=>!v256HiddenBy3D' not in local:
        raise ValueError('STOP: expected generator anchors not found. No changes written.')
    # Critical: prevent partial patches of unknown variants.
    if source.count(old)!=1 or source.count('   const p=entry.pole;\n')!=1 or source.count('  return out;\n')!=1:
        raise ValueError('STOP: ambiguous generator. No changes written.')
    updated=text[:start]+local+text[end:]
    if updated.count(' function v255GenerateLamps(){')!=1:
        raise ValueError('STOP: inconsistent generator count.')
    updated=updated.replace(' function v255GenerateLamps(){',HELPERS+' function v255GenerateLamps(){',1)
    updated=re.sub(r'(<meta name="app-version" content=")[^"]+("\s*/?>)',r'\g<1>2.56\2',updated,count=1)
    # Only change human-visible version references; leave old changelog and unrelated data.
    updated=updated.replace('v2.55 TEST','v2.56 TEST')
    updated=re.sub(r'(<title>[^<]*)v2\.55',r'\g<1>v2.56',updated,count=1)
    updated=updated.replace('3D Trondheim · v2.55','3D Trondheim · v2.56')
    return updated


def main():
    if len(sys.argv)<2 or len(sys.argv)>3:
        raise SystemExit('Usage: python scripts/apply_v256.py index.html [output.html]')
    p=pathlib.Path(sys.argv[1]); dst=pathlib.Path(sys.argv[2]) if len(sys.argv)>2 else p
    old=p.read_text(encoding='utf-8'); new=patch(old)
    if new==old:
        print('OK: v2.56 building filter already present; no changes.');return
    dst.write_text(new,encoding='utf-8')
    print('OK: v2.56 building footprints and pitched-view masking installed:',dst)


if __name__=='__main__':
    try:main()
    except Exception as e:print('ERROR:',e,file=sys.stderr);sys.exit(1)
