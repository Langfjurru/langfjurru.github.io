#!/usr/bin/env python3
"""Apply narrowly scoped streetlight improvements to an existing Trondheim 3D HTML.

Usage: python scripts/apply_v255.py path/to/v2.54.html [output.html]
The script refuses to modify ambiguous files and always preserves other code.
"""
import pathlib
import re
import sys

BASE = pathlib.Path(__file__).resolve().parent.parent
REGISTRY = (BASE / 'scripts' / 'lamp_patch_v255.js').read_text(encoding='utf-8')


def patch_html(source: str) -> str:
    if 'LAMP_REGISTRY_URL' in source:
        raise ValueError('Denne filen har allerede v2.55-lysmotoren')
    anchor = ' const switchEl=$(\'toggle-streetlights\'),skyStatus=$(\'solar-light-status\');'
    if source.count(anchor) != 1:
        raise ValueError('Fant ikke den forventede gatelysmodulen nøyaktig en gang.')
    # Replace only the road-point generation. NOAA timing, drawing and all other features stay unchanged.
    pattern = re.compile(r' function scanLamps\(\)\{[\s\S]*?\n \}\n function planScan\(', re.MULTILINE)
    if len(pattern.findall(source)) != 1:
        raise ValueError('Fant ikke en entydig scanLamps()-funksjon. Ingen fil ble endret.')
    source = pattern.sub(lambda m: REGISTRY.rstrip() + '\n function planScan(', source, count=1)
    # Run exactly one static GeoJSON request, after all module declarations.
    marker = " switchEl.addEventListener('change',()=>{"
    if source.count(marker) != 1:
        raise ValueError('Fant ikke entydig initialiseringspunkt for gatelysmodulen.')
    source = source.replace(marker, " void loadLampRegistry();\n" + marker, 1)
    # Patch the status only inside this same code module so later solar ticks keep accurate wording.
    start = source.index(anchor)
    end = source.find('// v2.39: Architectural floodlight', start)
    if end < 0:
        raise ValueError('Fant ikke avslutning på gatelysmodulen.')
    code = source[start:end]
    if code.count('setStatus();') < 2:
        raise ValueError('Uventet gatelysstatus: ingen fil endret.')
    # old function retained, but calls are changed to new status helper, without touching any other module
    code = code.replace('setStatus();', 'lampRegistryStatus();')
    source = source[:start] + code + source[end:]
    # Prevent duplicate source timestamps or version labels in unrelated API strings.
    source = re.sub(r'(<meta name="app-version" content=")[^"]+("\s*/?>)', r'\g<1>2.55\2', source, count=1)
    source = source.replace('v2.54 TEST', 'v2.55 TEST').replace('v2.54', 'v2.55')
    # Do not rename earlier changelog comments or old code constants by overwriting every occurrence.
    if '<title>' in source:
        source = re.sub(r'<title>(.*?)</title>', lambda m: '<title>' + re.sub(r'v2\.54', 'v2.55',m.group(1)) + '</title>',source,count=1,flags=re.I|re.S)
    return source


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        raise SystemExit('Bruk: python scripts/apply_v255.py v2.54.html [index.html]')
    src = pathlib.Path(sys.argv[1])
    dst = pathlib.Path(sys.argv[2]) if len(sys.argv) == 3 else src.with_name('Trondheim_3D_v2_55_Gatelys_GeoJSON_TEST.html')
    text = src.read_text(encoding='utf-8')
    updated = patch_html(text)
    dst.write_text(updated,encoding='utf-8')
    print(f'OK: {dst} | {len(updated):,} tegn | GeoJSON: data/trondheim-gatelys.geojson')

if __name__ == '__main__':
    main()
