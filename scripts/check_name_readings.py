"""Generate naming comparison with synthetic names only; no saved customer data."""
import asyncio
import json
from pathlib import Path

from api.server import Profile,ReadRequest,NameCandidate,read,SESSIONS,HTTPException
from api import name_readings


async def main():
    original=name_readings.complete
    async def observed(schema,messages,*args,**kwargs):
        value,metrics=await original(schema,messages,*args,**kwargs)
        out=Path('.runtime/model-validation/openrouter/name-batches.jsonl')
        out.parent.mkdir(parents=True,exist_ok=True)
        with out.open('a') as f:f.write(json.dumps({'output':value,'metrics':metrics},ensure_ascii=False)+'\n')
        print('Generated naming batch',flush=True)
        return value,metrics
    name_readings.complete=observed
    request=ReadRequest(service='name',profile=Profile(name='지민',surname='박',surname_hanja='朴',
        birth_date='2026-05-15',birth_time='10:30',naming_preference='wisdom'),
        name_candidates=[NameCandidate(name='서연'),NameCandidate(name='가람')])
    try:result=await read(request)
    except HTTPException as exc:
        print('REJECTED',str(exc.__cause__),flush=True)
        return 1
    SESSIONS.pop(result['reading_id'],None)
    result.update(reading_id=None,demo=True,example_request=request.model_dump(mode='json'))
    report=result['naming_report']
    assert len(report['candidate_reports'])==3
    assert report['generation']['previous_reading_used'] is False
    path=Path('.runtime/model-validation/openrouter/names.json')
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2))
    for p in report['candidate_reports']:
        print(p['name'],p['status'],'rank=',p['recommended_rank'],'combinations=',len(p['recommendations']),flush=True)
    print('VERIFIED',report['generation']['model'],report['generation']['seconds'],'seconds',flush=True)
    return 0


if __name__=='__main__':raise SystemExit(asyncio.run(main()))
