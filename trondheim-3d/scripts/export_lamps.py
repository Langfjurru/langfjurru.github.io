#!/usr/bin/env python3
"""Build a static GeoJSON snapshot of surveyed/mapped OSM street lamps in Trondheim.

Source: OpenStreetMap (ODbL 1.0). Run in GitHub Actions, not in app clients.
Never fabricate measured positions. Unknown coverage is filled by explicitly
estimated positions from the map's own fallback algorithm.
"""
from __future__ import annotations
import datetime as dt
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEST = ROOT / 'data' / 'trondheim-gatelys.geojson'
BBOX = (63.38, 10.25, 63.50, 10.56)  # south, west, north, east
QUERY = '''[out:json][timeout:90];
(
 node["highway"="street_lamp"](63.38,10.25,63.50,10.56);
 node["man_made"="street_lamp"](63.38,10.25,63.50,10.56);
);
out body;'''
ENDPOINTS = (
    'https://overpass.kumi.systems/api/interpreter',
    'https://overpass-api.de/api/interpreter',
)


def download_osm():
    errors = []
    body = urllib.parse.urlencode({'data': QUERY}).encode('ascii')
    for endpoint in ENDPOINTS:
        for trial in range(2):
            try:
                req = urllib.request.Request(endpoint, data=body, method='POST', headers={
                    'User-Agent': 'Trondheim3D-Gatelys-Geodata/1.0 (noncommercial; weekly; ODbL)',
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'Accept': 'application/json',
                })
                with urllib.request.urlopen(req, timeout=125) as response:
                    result = json.load(response)
                if not isinstance(result.get('elements'), list):
                    raise ValueError('Invalid/empty Overpass response')
                return result, endpoint
            except Exception as exc:
                errors.append(f'{endpoint} forsøk {trial+1}: {exc}')
                if trial == 0: time.sleep(4)
    raise RuntimeError('Kan ikke hente lyspunktdata: ' + '; '.join(errors))


def convert(raw):
    features = []
    used = set()
    for el in raw['elements']:
        if el.get('type') != 'node' or not isinstance(el.get('id'), int):
            continue
        if el['id'] in used:
            continue
        used.add(el['id'])
        lat, lon = el.get('lat'), el.get('lon')
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            continue
        if not (BBOX[0] <= lat <= BBOX[2] and BBOX[1] <= lon <= BBOX[3]):
            continue
        tags = el.get('tags', {})
        if (tags.get('disused') == 'yes' or tags.get('removed') == 'yes' or
                tags.get('abandoned') == 'yes' or tags.get('construction') == 'yes'):
            continue
        props = {'source': 'OpenStreetMap', 'osm_id': el['id'], 'mapped': True}
        for key in ('lamp_mount', 'lamp_type', 'light:colour', 'lit', 'height'):
            if key in tags:
                props[key.replace(':', '_')] = tags[key][:72]
        features.append({
            'type': 'Feature',
            'id': 'osm-node-' + str(el['id']),
            'geometry': {'type': 'Point', 'coordinates': [round(lon, 7), round(lat, 7)]},
            'properties': props,
        })
    features.sort(key=lambda f: f['properties']['osm_id'])
    return features


def main():
    raw, endpoint = download_osm()
    features = convert(raw)
    if not features:
        raise RuntimeError('Overpass returned zero qualifying street lamps: retain previous GeoJSON')
    old = json.loads(DEST.read_text(encoding='utf-8')) if DEST.exists() else {}
    if old.get('features') == features:
        print(f'No changes: {len(features)} OSM poles. Previous file preserved.')
        return
    snapshot = {
        'type': 'FeatureCollection',
        'metadata': {
            'description': 'Kartlagte lysmaster, ikke beregnede mastesteder.',
            'status': 'importert_fra_osm',
            'updated_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
            'source': 'OpenStreetMap',
            'source_endpoint': endpoint,
            'license': 'ODbL-1.0',
            'attribution': '© OpenStreetMap contributors',
            'source_url': 'https://www.openstreetmap.org/copyright',
            'bbox_wgs84': [BBOX[1], BBOX[0], BBOX[3], BBOX[2]],
            'feature_count': len(features),
        },
        'features': features,
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(snapshot, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    print(f'Updated {DEST}: {len(features)} OSM nodes from {endpoint}')


if __name__ == '__main__':
    try:
        main()
    except Exception as ex:
        print(f'ERROR: {ex}', file=sys.stderr)
        sys.exit(1)
