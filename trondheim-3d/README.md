# Trondheim 3D – gatelys v2.55 TEST

Denne pakken endrer **kun gatelysmodulen** i eksisterende Trondheim 3D HTML. Den inkluderer en rask, lokal GeoJSON-kilde for **faktisk kartlagte** lyspunkter, samt en forbedret, tydelig merket **beregningsmotor** for kartutsnitt uten kartlagte lyspunkt.

## Gjennomføring uten å miste tog og buss

1. Legg `scripts/apply_v255.py` og `scripts/lamp_patch_v255.js` på samme relative plass som i denne pakken.
2. Kjør med Python 3 på **din fullstendige v2.54 TEST-fil**:

   `python scripts/apply_v255.py Trondheim_3D_v2_54_SAMLET_TOGANIMASJON_TEST.html index.html`

   Hvis HTML-strukturen er ulik den forventede, stopper programmet i stedet for å risikere sletting av togmodul, rutetavler eller andre funksjoner.
3. Legg `data/trondheim-gatelys.geojson`, begge Python- og JS-filene i `scripts/` samt `.github/workflows/update-gatelys.yml` inn i **roten av samme GitHub-repository** som serverer https://langfjurru.github.io/trondheim-3d/. Behold repoets eksisterende `index.html` (v2.54) urørt; GitHub Actions kan oppdatere denne automatisk. Alternativt kan du selv legge inn din nye lokalt genererte `index.html` fra punkt 2.
4. Dersom `index.html` allerede er v2.54, vil arbeidsflyten automatisk oppgradere den eksisterende HTML-filen på GitHub uten å erstatte øvrig kode. På GitHub: `Actions` → `Oppdater kartlagte gatelys (OSM til GeoJSON)` → `Run workflow`. Første kjøring fyller GeoJSON med reelle OSM-noder. Kjøringen gjentas deretter ukentlig uten at kartet spør Overpass ved hver sidevisning. Ved begrensede Actions-rettigheter må `Settings` → `Actions` → `General` → `Workflow permissions` tillate `Read and write permissions`.
5. Bruk v2.55 som TEST inntil mobil, kartflytting, tog/buss og dag/natt-lys er kontrollert.

Hvis `index.html` ligger i en undermappe, må `data/` ligge i samme undermappe fordi `./data/trondheim-gatelys.geojson?v=255` er relativ til HTML-filens adresse.

## Lysplassering

- Kartlagte `highway=street_lamp` / `man_made=street_lamp` OSM-punkter lastes som statiske WGS84 GeoJSON-punkter (én GET ved oppstart).
- Bare punkter nær relevante bussgater/landemerker vises, i tråd med det eksisterende gatelyslaget. Ingen kartlagte master flyttes på for å passe gategeometrien.
- Når det mangler reelle punktdata, suppleres gateløpet med beregnede master, konsekvent side og omtrent 37–43 m avstand i stedet for en ny tilfeldig start i hvert veisegment.
- Beregnede master kommer ikke innenfor ca. 29 m av en kartlagt mast; løpende deduplisering hindrer dobbeltrader.
- Solposisjon, fargetone, eksisterende spotlights og buss/trikk/tog/hurtigbåt beholdes i den oppdaterte **v2.54-filens** øvrige kode.
- Appens lagtekst viser antall kartlagte kontra beregnede master. Når GeoJSON er tom eller utilgjengelig virker den beregnede plasseringen fortsatt.

## Datagrunnlag og lisens

© OpenStreetMap-bidragsytere. OSM-data er tilgjengelige under [Open Database License (ODbL 1.0)](https://www.openstreetmap.org/copyright). Legg denne kildehenvisningen synlig på kartet; oppdateringspatchen legger til henvisning under gatelysinnstillingen. Dataene i GeoJSON er et avledet OSM-uttak og kan brukes videre i henhold til ODbL-vilkårene.

Trondheim kommunes fullstendige gatelysregister er **ikke** med i denne pakken. Kommunens nettsted har eget skjema for utlevering, og bruksrett må avklares separat. NVDB-data kan etterprøves og innarbeides i senere iterasjon, men objekter med utledet veggeometri må ikke utgis for å ha faktisk mastposisjon.

## Ytelse og drift

Ingen Overpass-forespørsler ved kartvisning. Ett cachebart GeoJSON-hent per sidevisning. Kartets pågående tegning bruker eksisterende 2D Canvas-overlegg (ikke ekstra WebGL-rendering). Ved stort OSM-dekningsområde bør punktene deles i fliser; denne Trondheim-avgrensningen er bevisst liten.

## Begrensning i leveransen

v2.54-HTML-en fra den forrige samtalen er ikke tilgjengelig som kildefil i denne kjørekonteksten. For å unngå regresjon til v2.51 leveres derfor en **patcher for v2.54**, pluss en separat testkompilering mot tilgjengelig v2.51 for syntaks-/integrasjonskontroll. Ingen endringer er publisert i brukerens GitHub-repository fra denne leveransen.
