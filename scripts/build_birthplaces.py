"""Rebuild the offline KMA catalog from its published XLSX, using stdlib only."""
import hashlib
import io
import json
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'https://www.data.go.kr/data/15084084/openapi.do'
DOWNLOAD = 'https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000007696658&fileSn=1'
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def build(blob):
    package = zipfile.ZipFile(io.BytesIO(blob))
    filename = next(n for n in package.namelist() if n.endswith('.xlsx'))
    workbook = package.read(filename)
    z = zipfile.ZipFile(io.BytesIO(workbook))
    strings = [''.join(e.itertext()) for e in ET.fromstring(z.read('xl/sharedStrings.xml'))]
    rows = []
    for row in ET.fromstring(z.read('xl/worksheets/sheet1.xml')).findall('.//s:row', NS):
        values = {}
        for cell in row.findall('s:c', NS):
            v = cell.find('s:v', NS)
            if v is not None:
                values[cell.attrib['r'].rstrip('0123456789')] = strings[int(v.text)] if cell.attrib.get('t') == 's' else v.text
        rows.append(values)
    assert rows[0]['B'] == '행정구역코드' and rows[0]['N'] == '경도(초/100)'
    regions = {}
    places = []
    for row in rows[1:]:
        if row.get('A') != 'kor' or not row.get('C') or row.get('C') == '이어도':
            continue
        longitude, latitude = float(row['N']), float(row['O'])
        if not 122 < longitude < 134 or not 30 < latitude < 40:
            continue
        region = row['B'][:2]
        regions[region] = {'id': region, 'label': row['C']}
        district, locality = row.get('D', ''), row.get('E', '')
        if not district and not locality and region != '36':
            continue  # A province capital is not everybody's birthplace.
        # Searchable former names help people born before the 2026 merger.
        familiar = ('광주' if district in ['동구', '서구', '남구', '북구', '광산구'] else '전남') if region == '12' else ''
        places.append({'id': 'kr-' + row['B'], 'region': region, 'district': district,
                       'locality': locality, 'label': ' '.join(filter(None, [familiar, district, locality])) or row['C'],
                       'longitude': round(longitude, 8), 'latitude': round(latitude, 8),
                       'aliases': ' '.join(filter(None, [row['C'], familiar, {'51':'강원도', '52':'전라북도'}.get(region)])),
                       'basis': '기상청 행정구역 대표지점'})
    # Backward compatibility preserves the three previously used coordinates.
    for city, region, label, lon, lat in [('seoul','11','서울 · 대표지점',126.9784,37.5665),
                                        ('busan','26','부산 · 대표지점',129.0756,35.1796),
                                        ('jeju','50','제주 · 대표지점',126.5312,33.4996)]:
        places.append({'id':city,'region':region,'district':'','locality':'','label':label,
                       'longitude':lon,'latitude':lat,'aliases':'','basis':'기존 도시 대표지점'})
    assert len({p['id'] for p in places}) == len(places)
    catalog = {'source': SOURCE, 'regions': list(regions.values()), 'places': places}
    (ROOT / 'dist/assets/birthplaces.json').write_text(json.dumps(catalog, ensure_ascii=False, separators=(',', ':')) + '\n')
    provenance = {'source': SOURCE, 'download': DOWNLOAD, 'worksheet': filename,
                  'archive_sha256': hashlib.sha256(blob).hexdigest(), 'xlsx_sha256': hashlib.sha256(workbook).hexdigest(),
                  'retrieved_at': datetime.now(timezone.utc).isoformat(), 'attribution':'기상청 · 공공데이터포털',
                  'license':'공공누리 제1유형 · 출처표시', 'license_url':'https://www.kogl.or.kr/info/licenseType1.do',
                  'places':len(places),'regions':len(regions),
                  'scope':'읍면동·시군구 대표지점의 경도 사용. 정확한 출생 건물 좌표나 과거 행정구역 경계는 아님. 광주·전남의 옛 이름은 검색·표시 별칭. 기존 3개 도시 좌표 유지. 좌표 0인 이어도 제외.'}
    (ROOT / 'knowledge/birthplaces-provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'places':len(places),'regions':len(regions)}))


if __name__ == '__main__':
    build(urllib.request.urlopen(DOWNLOAD).read())
