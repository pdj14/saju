"""Snapshot public Court name-character lookup for readings with dictionary meanings.

Stores characters and permitted readings only, not the lookup service's dictionary prose.
Unqueried readings are unknown; absence is meaningful only within a successful query.
"""
import asyncio,hashlib,json
from datetime import date
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1]
URL='https://efamily.scourt.go.kr/webhanja/whjsearch'
async def main():
 data=json.loads((ROOT/'knowledge/hanja-unihan.json').read_text())
 readings=sorted({r for d in data.values() if d.get('meaning_ko') or d.get('definition') for r in d['readings']})
 by={};digests={}
 async with httpx.AsyncClient(timeout=25,follow_redirects=True) as client:
  for reading in readings:
   if reading in by:continue
   response=await client.get(URL,params={'mode':'listUnicodeByKsnd','ksnd':format(ord(reading),'x'),'ext':0,'pgmode':1,'pgno':1,'pgsize':10000})
   response.raise_for_status();payload=response.json()
   if payload.get('errno')!=0 or len(payload.get('resultlist',[]))!=payload['resultcount']:raise ValueError('Incomplete court lookup')
   rows=[]
   for row in payload['resultlist']:
    if row.get('isin')!=1:continue
    try:char=chr(int(row['cd'],16))
    except (ValueError,TypeError):continue
    rows.append(char)
   by[reading]=list(dict.fromkeys(rows));digests[reading]=hashlib.sha256(response.content).hexdigest()
   await asyncio.sleep(.06)
 result={'source':'https://efamily.scourt.go.kr/cs/CsBltnWrtList.do?bltnbordId=0000010','endpoint':URL,'checked_at':date.today().isoformat(),
  'scope':'공식 조회가 성공한 독음에 대한 인명용 글자 목록의 조회일 스냅샷. 미조회 독음은 미확인. 최신 신고 판정은 공식 조회에서 확인.',
  'readings':by,'response_sha256':digests,'reading_checked_at':{r:date.today().isoformat() for r in by}}
 (ROOT/'knowledge/name-registry.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print({'queried_readings':len(by),'character_reading_pairs':sum(map(len,by.values()))})
asyncio.run(main())
