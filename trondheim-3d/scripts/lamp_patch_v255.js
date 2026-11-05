 // v2.55: Mapped OSM street-lamp points are loaded ONCE from a GitHub Pages GeoJSON snapshot.
 // Fallback lamps are generated from map road geometry with a stable per-street cadence.
 // The registry never claims that generated points are surveyed locations.
 const LAMP_REGISTRY_URL='./data/trondheim-gatelys.geojson?v=255';
 lampState.registryLamps=[];
 lampState.registryState='laster';
 lampState.registryUpdated='';
 // Required source credit for the static ODbL-derived GeoJSON file.
 if(lampStatus?.parentElement&&!document.getElementById('trondheim-osm-lamps-credit')){
  const credit=document.createElement('a');
  credit.id='trondheim-osm-lamps-credit';
  credit.href='https://www.openstreetmap.org/copyright';
  credit.target='_blank';credit.rel='noopener noreferrer';
  credit.textContent='© OpenStreetMap-bidragsytere · ODbL';
  credit.style.cssText='display:inline-block;margin-top:3px;color:#337383;font-size:10px;text-decoration:underline;';
  lampStatus.parentElement.appendChild(credit);
 }
 async function loadLampRegistry(){
  try{
   const response=await fetch(new URL(LAMP_REGISTRY_URL,document.baseURI).href,{cache:'default'});
   if(!response.ok)throw Error('HTTP '+response.status);
   const fc=await response.json();
   if(fc?.type!=='FeatureCollection'||!Array.isArray(fc.features))throw Error('Ugyldig GeoJSON');
   lampState.registryLamps=fc.features.filter(f=>f?.geometry?.type==='Point'&&
    Array.isArray(f.geometry.coordinates)&&Number.isFinite(f.geometry.coordinates[0])&&
    Number.isFinite(f.geometry.coordinates[1])&&
    f.geometry.coordinates[1]>=63.35&&f.geometry.coordinates[1]<=63.53&&
    f.geometry.coordinates[0]>=10.20&&f.geometry.coordinates[0]<=10.70&&
    (f.properties?.source==='OpenStreetMap'||(f.properties?.source==='NVDB'&&f.properties?.egengeometri===true)))
    .map(f=>({pole:f.geometry.coordinates,source:f.properties?.source,osmId:f.properties?.osm_id||null}));
   lampState.registryState=lampState.registryLamps.length?'klar':'tom';
   lampState.registryUpdated=String(fc.metadata?.updated_at||'');
  }catch(e){lampState.registryState='feil';console.warn('Gatelys: lokale GeoJSON-data kunne ikke lastes, bruker trygg beregning.',e);}
  planScan(60);
 }
 function lampRegistryStatus(){
  // Show exact provenance instead of labelling estimated points as mapped fixtures.
  const actual=lampState.features.filter(f=>f.registered).length;
  const estimate=lampState.features.length-actual;
  lampCount.textContent=switchEl.checked?String(lampState.features.length):'–';
  if(!switchEl.checked){lampStatus.textContent='Av · stolpene er skjult';return;}
  if(state.mapMode==='raster'){lampStatus.textContent='Gatelys vises i vektorkart';return;}
  if(map.getZoom()<15){lampStatus.textContent='Zoom inn for gatelys · OSM / beregnede';return;}
  if(!lampState.features.length){lampStatus.textContent='Ingen gatelys i kartutsnittet';return;}
  const src=actual?`${actual} OSM/NVDB · `:'';
  const fallback=estimate?`${estimate} beregnet`:'';
  const phase=lampState.strength>.14?' · tent':' · slukket';
  lampStatus.textContent=src+fallback+phase;
 }
 // Metric-space nearest-geometry calculation; street determines the direction of the lamp arm.
 function v255ClosestRoad(p,grid,sx,sy){
  const x=(p[0]-10.4)*sx,y=(p[1]-63.43)*sy,cellSize=28;
  const gx=Math.floor(x/cellSize),gy=Math.floor(y/cellSize);
  let nearest=null,dist2=22*22;
  for(let ox=-1;ox<=1;ox++)for(let oy=-1;oy<=1;oy++){
   for(const s of grid.get((gx+ox)+':'+(gy+oy))||[]){
    const dx=s.bx-s.ax,dy=s.by-s.ay,ll=dx*dx+dy*dy;
    if(ll<.1)continue;
    const t=clamp(((x-s.ax)*dx+(y-s.ay)*dy)/ll,0,1);
    const qx=s.ax+t*dx,qy=s.ay+t*dy,d=(x-qx)**2+(y-qy)**2;
    if(d<dist2){dist2=d;nearest={street:[10.4+qx/sx,63.43+qy/sy],dist:Math.sqrt(d),name:s.name};}
   }
  }
  return nearest;
 }
 function v255GenerateLamps(){
  const zoom=map.getZoom(),bounds=map.getBounds(),center=map.getCenter();
  const sx=111320*Math.cos(center.lat*RAD),sy=111320;
  const w=map.getCanvas().clientWidth||innerWidth,h=map.getCanvas().clientHeight||innerHeight;
  const cap=w<680?105:165,routeIndex=routeGrid(bounds);
  const eligible=[],segmentSeen=new Set(),grid=new Map(),gridSize=28;
  function addIndex(s){
   const length=Math.hypot(s.bx-s.ax,s.by-s.ay);
   for(let k=0,n=Math.min(600,Math.ceil(length/12));k<=n;k++){
    const t=k/Math.max(1,n),x=s.ax+(s.bx-s.ax)*t,y=s.ay+(s.by-s.ay)*t;
    const key=Math.floor(x/gridSize)+':'+Math.floor(y/gridSize);
    if(!grid.has(key))grid.set(key,new Set());grid.get(key).add(s);
   }
  }
  for(const feat of segmentsFromMap()){
   const cls=roadType(feat.properties||{});if(!cls)continue;
   const p=feat.properties||{},name=normalizedRoadName(p);
   const known=BUS_ROAD_NAMES.has(name)||BUS_ROAD_NAMES.has(String(p.ref||'').toLowerCase());
   for(const line of roadCoords(feat)){
    if(!Array.isArray(line))continue;
    for(let j=1;j<line.length;j++){
     const a=line[j-1],b=line[j];
     if(!Array.isArray(a)||!Array.isArray(b)||![a[0],a[1],b[0],b[1]].every(Number.isFinite))continue;
     const ax=(a[0]-10.4)*sx,ay=(a[1]-63.43)*sy,bx=(b[0]-10.4)*sx,by=(b[1]-63.43)*sy;
     const len=Math.hypot(bx-ax,by-ay);if(len<7||len>1800)continue;
     if(Math.max(a[0],b[0])<bounds.getWest()-.002||Math.min(a[0],b[0])>bounds.getEast()+.002||
        Math.max(a[1],b[1])<bounds.getSouth()-.002||Math.min(a[1],b[1])>bounds.getNorth()+.002)continue;
     const k1=`${Math.round(a[0]*1e5)}:${Math.round(a[1]*1e5)}`;
     const k2=`${Math.round(b[0]*1e5)}:${Math.round(b[1]*1e5)}`;
     const key=k1<k2?k1+'|'+k2:k2+'|'+k1;
     if(segmentSeen.has(key))continue;segmentSeen.add(key);
     const mid=[(a[0]+b[0])*.5,(a[1]+b[1])*.5];
     const near=nearestLandmark(mid);
     const allowed=cls==='walkway'?Boolean(near):known||onEnturCorridor(mid,routeIndex)||Boolean(near);
     if(!allowed)continue;
     // Nidarosdomen is deliberately lit by the separate architectural module.
     if(meters2(mid,[10.39697,63.426954])<95)continue;
     const s={ax,ay,bx,by,len,name,cls,landmark:Boolean(near)};
     eligible.push(s);addIndex(s);
    }
   }
  }
  const mapped=[],pad=.0010;
  for(const entry of lampState.registryLamps){
   const p=entry.pole;
   if(p[0]<bounds.getWest()-pad||p[0]>bounds.getEast()+pad||p[1]<bounds.getSouth()-pad||p[1]>bounds.getNorth()+pad)continue;
   if(meters2(p,[10.39697,63.426954])<95)continue;
   const nearest=v255ClosestRoad(p,grid,sx,sy);if(!nearest)continue;
   if(mapped.some(f=>meters2(f.pole,p)<2.5))continue;
   const projected=map.project(p);
   if(projected.x<-55||projected.y<-80||projected.x>w+55||projected.y>h+60)continue;
   mapped.push({pole:p,street:nearest.street,registered:true,priority:Math.hypot(projected.x-w/2,projected.y-h/2)});
  }
  const predicted=[];
  for(const s of eligible){
   // Direction independent of vector-tile segmentation or the order of a road's vertices.
   const canonical=(s.ax<s.bx)||(s.ax===s.bx&&s.ay<s.by);
   const tx=(s.bx-s.ax)/s.len*(canonical?1:-1),ty=(s.by-s.ay)/s.len*(canonical?1:-1);
   const name=s.name||`gate:${Math.round((s.ax+s.bx)/400)}:${Math.round((s.ay+s.by)/400)}`;
   const side=(hash(name)&1)?1:-1;
   const offset=s.cls==='walkway'?2.7:/^(primary|secondary|trunk)$/.test(s.cls)?7.4:6.1;
   const spacing=s.landmark?43:/^(primary|secondary)$/.test(s.cls)?37:43;
   const phase=hash(name+'|streetlight')%spacing;
   const v0=s.ax*tx+s.ay*ty,v1=s.bx*tx+s.by*ty;
   const min=Math.min(v0,v1),max=Math.max(v0,v1);
   for(let t=Math.ceil((min-phase)/spacing)*spacing+phase;t<=max;t+=spacing){
    const frac=(t-v0)/(v1-v0);
    if(frac<.055||frac>.945)continue;
    const x=s.ax+(s.bx-s.ax)*frac,y=s.ay+(s.by-s.ay)*frac;
    const street=[10.4+x/sx,63.43+y/sy];
    const pole=[10.4+(x-side*ty*offset)/sx,63.43+(y+side*tx*offset)/sy];
    if(meters2(street,[10.39697,63.426954])<95)continue;
    if(mapped.some(f=>meters2(pole,f.pole)<29))continue;
    const pt=map.project(pole);
    if(pt.x<-55||pt.y<-65||pt.x>w+55||pt.y>h+60)continue;
    predicted.push({pole,street,registered:false,priority:Math.hypot(pt.x-w/2,pt.y-h/2)+(s.landmark?-50:0)});
   }
  }
  // Mapped poles always beat synthetic positions. Local spacing prevents duplicates at junctions.
  mapped.sort((a,b)=>a.priority-b.priority);
  predicted.sort((a,b)=>a.priority-b.priority);
  const out=[];
  for(const f of mapped){if(out.length>=cap)break;if(!out.some(p=>meters2(p.pole,f.pole)<2.5))out.push(f);}
  for(const f of predicted){if(out.length>=cap)break;if(!out.some(p=>meters2(p.pole,f.pole)<23))out.push(f);}
  return out;
 }
 function scanLamps(){
  lampState.scanTimer=0;
  if(!switchEl.checked||document.hidden||!ctx)return;
  if(map.getZoom()<15||state.mapMode!=='vector'){
   lampState.features=[];lampRegistryStatus();scheduleGlows();return;
  }
  // Keep Entur route information as a non-blocking supplement for unnamed bus corridors.
  void refreshBusCorridors();
  lampState.features=v255GenerateLamps();
  lampState.ready=true;
  lampRegistryStatus();scheduleGlows();
 }
