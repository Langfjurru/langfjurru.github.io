#!/usr/bin/env python3
"""Trondheim 3D v2.57: remove expensive roadside streetlight engine.

Strictly targeted HTML-only patch. Preserves solar day/night shading, vehicle
headlight lighting and the separate architectural floodlight module. Does not
modify any bus, train, tram, boat, map style, or realtime sources.
"""
from __future__ import annotations
import pathlib
import re
import sys

STAMP = 'V257_STREETLIGHTS_OFF_PERF'
START = '// v2.37: Bus-corridor-only lamps'
END = '// v2.39: Architectural floodlight design'

SOLAR_ONLY = r'''// V257_STREETLIGHTS_OFF_PERF: all roadside streetlamp work removed.
// No OSM/GeoJSON lamp fetch, no building scans, no road scans,
 // no streetlamp animation frame listener or transparent 2D canvas redraw.
 // Keep the original solar day/night algorithm and vehicle-light timing.
{
 const RAD=Math.PI/180;
 const clamp=(x,a,b)=>Math.min(b,Math.max(a,x));
 const smooth=(a,b,x)=>{let t=clamp((x-a)/(b-a),0,1);return t*t*(3-2*t);};
 const shade=document.getElementById('trondheim-light-shade');
 const skyStatus=document.getElementById('solar-light-status');
 const obsoleteCanvas=document.getElementById('trondheim-lamp-glows');
 // Do not allocate or repaint a full-screen, high-DPI canvas on every map movement.
 if(obsoleteCanvas){obsoleteCanvas.style.display='none';obsoleteCanvas.width=1;obsoleteCanvas.height=1;}
 const formatter=new Intl.DateTimeFormat('nb-NO',{timeZone:'Europe/Oslo',hour:'2-digit',minute:'2-digit',hourCycle:'h23'});
 function solarAltitude(date,lat,lon){
  const start=Date.UTC(date.getUTCFullYear(),0,1);
  const day=Math.floor((Date.UTC(date.getUTCFullYear(),date.getUTCMonth(),date.getUTCDate())-start)/86400000)+1;
  const mins=date.getUTCHours()*60+date.getUTCMinutes()+date.getUTCSeconds()/60;
  const days=Date.UTC(date.getUTCFullYear()+1,0,1)-start>365*86400000?366:365;
  const g=2*Math.PI/days*(day-1+(mins/60-12)/24);
  const eq=229.18*(.000075+.001868*Math.cos(g)-.032077*Math.sin(g)-.014615*Math.cos(2*g)-.040849*Math.sin(2*g));
  const decl=.006918-.399912*Math.cos(g)+.070257*Math.sin(g)-.006758*Math.cos(2*g)+.000907*Math.sin(2*g)-.002697*Math.cos(3*g)+.00148*Math.sin(3*g);
  const hour=((mins+eq+4*lon)/4-180)*RAD;
  const sinAlt=Math.sin(lat*RAD)*Math.sin(decl)+Math.cos(lat*RAD)*Math.cos(decl)*Math.cos(hour);
  return {alt:Math.asin(clamp(sinAlt,-1,1))/RAD,afternoon:Math.sin(hour)>0,hourAngleDeg:hour/RAD};
 }
 function tickSky(){
  const center=map.getCenter(),sun=solarAltitude(new Date(),center.lat,center.lng),alt=sun.alt;
  const twilight=1-smooth(-12,9,alt);
  const evening=sun.afternoon?.075*smooth(15,70,sun.hourAngleDeg):0;
  const darkening=clamp(twilight*.78+evening,0,.82);
  const strength=1-smooth(-8,-2,alt);
  shade.style.opacity=darkening.toFixed(3);
  shade.style.background=alt>0?'linear-gradient(160deg,rgba(45,41,50,.48),rgba(18,28,49,.68))':
   'linear-gradient(155deg,rgba(13,26,51,.74),rgba(4,13,32,.89))';
  try{
   if(map.getStyle()&&typeof map.setLight==='function'){
    map.setLight({anchor:'map',color:alt<0?'#9baed2':alt<9?'#f3d9ba':'#fff7e8',
      intensity:Number((.55-darkening*.42).toFixed(3)),position:[1.2,210,38]});
   }
  }catch(e){/* Raster / incompatible map style: DOM shading still works. */}
  // Retain original vehicle headlights and light-cones behaviour.
  syncVehicleLighting(alt,darkening,strength);
  const phase=alt>=9?(sun.afternoon?'Ettermiddag':'Dagslys'):alt>=-6?'Skumring':'Natt';
  if(skyStatus)skyStatus.textContent=`${phase} · sol ${alt.toFixed(1)}° · ${formatter.format(new Date())}`;
 }
 // Solar brightness changes slowly: no per-frame work required.
 map.on('style.load',tickSky);
 map.on('moveend',tickSky);
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)tickSky();});
 setInterval(()=>{if(!document.hidden)tickSky();},60000);
 tickSky();
}

'''


def patch(html: str) -> str:
    if STAMP in html:
        return html
    if html.count(START) != 1 or html.count(END) != 1:
        raise ValueError('STOP: expected streetlight and architectural module anchors not found exactly once.')
    if 'function v255GenerateLamps(){' not in html or 'function scanLamps(){' not in html:
        raise ValueError('STOP: v2.55/2.56 road-lamp engine not found.')
    if 'trondheim-light-shade' not in html or 'syncVehicleLighting(' not in html:
        raise ValueError('STOP: existing solar / vehicle lighting anchors missing.')
    start = html.index(START)
    end = html.index(END, start)
    if start > end or end - start < 8000 or end-start > 70000:
        raise ValueError('STOP: unexpected road-lamp module size.')
    module = html[start:end]
    for required in ('function solarAltitude(', 'function tickSky(', 'void loadLampRegistry();', "map.on('move',scheduleGlows)"):
        if required not in module:
            raise ValueError('STOP: expected road-lamp code missing: ' + required)
    if 'V256_BUILDING_MASK_V1' not in module and 'LAMP_REGISTRY_URL' not in module:
        raise ValueError('STOP: neither v2.55 nor v2.56 lamp patch recognized.')
    # Only touch a bounded lamp section. The separate landmark-light module stays byte-identical.
    updated = html[:start] + SOLAR_ONLY + html[end:]
    # Keep architecture-light switch and rename it to avoid implying streetlamp placement.
    updated = updated.replace('Vis lyktestolper langs bussruter og ved landemerker',
                              'Vis arkitektonisk belysning av landemerker', 1)
    updated = updated.replace('</span>Gatelys</div>', '</span>Landemerkelys</div>', 1)
    updated = updated.replace('Bussgater + Gamle Bybro / Trondheim Torg · 4 bygg med lyskastere',
                              'Nidarosdomen, Gløshaugen, Kristiansten og Munkholmen', 1)
    updated = updated.replace('<span class="num" id="count-streetlights">–</span>',
                              '<span class="num" id="count-streetlights">4</span>', 1)
    updated = re.sub(r'(<meta name="app-version" content=")[^"]+("\s*/?>)',
                     r'\g<1>2.57\2', updated, count=1)
    updated = re.sub(r'(<title>[^<]*)v2\.\d+(?:\.\d+)?[^<]*(</title>)',
                     r'\g<1>v2.57 Ytelse TEST\2', updated, count=1)
    updated = updated.replace('v2.56 TEST', 'v2.57 YTELSE TEST')
    updated = updated.replace('v2.55 TEST', 'v2.57 YTELSE TEST')
    updated = updated.replace('3D Trondheim · v2.56', '3D Trondheim · v2.57')
    updated = updated.replace('3D Trondheim · v2.55', '3D Trondheim · v2.57')
    # Check the landmark floodlight implementation survived unchanged.
    if html[end:] != updated[updated.index(END):] and not re.search(r'v2\.5[56]',html[end:]):
        # Version text may be updated downstream; no check on those expected markers.
        raise ValueError('STOP: unexpected modification after landmark-light anchor.')
    for absent in ('function v255GenerateLamps(){', 'function v256Footprints(', 'map.on(\'move\',scheduleGlows)', 'void loadLampRegistry();'):
        if absent in updated:
            raise ValueError('STOP: expensive streetlamp logic unexpectedly remains: '+absent)
    return updated


def main() -> None:
    if len(sys.argv) not in (2, 3):
        raise SystemExit('Usage: python3 scripts/apply_v257.py index.html [output.html]')
    inp=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]) if len(sys.argv)==3 else inp
    original=inp.read_text(encoding='utf-8')
    new=patch(original)
    if new==original:
        print('OK: v2.57 is already installed; nothing to update.')
        return
    out.write_text(new,encoding='utf-8')
    print('OK: v2.57 performance patch installed. Roadside streetlamps disabled, solar/landmark lights retained.')

if __name__=='__main__':
    try: main()
    except Exception as exc:
        print('ERROR:',exc,file=sys.stderr)
        sys.exit(1)
