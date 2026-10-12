"""Run fresh readings with the configured model using synthetic fixtures.

No old personal reading is fed into a model. Saved artifacts contain only the
synthetic fixtures below; do not substitute customer inputs into this script.
"""
import asyncio
import argparse
import json
from pathlib import Path
import time

from api import model_readings
from api.model_provider import CONFIG
from api.server import Profile,ReadRequest,read,MODEL,SESSIONS,HTTPException

OUT=Path('.runtime/model-validation')/CONFIG.provider
OUT.mkdir(parents=True,exist_ok=True)
original=model_readings.call_model


async def observed(schema,system,user,*args,**kwargs):
    topics=[x['topic'] for x in user.get('SECTION_REQUESTS',[])]
    print('GENERATING',user.get('SERVICE'),topics,'repair=',bool(user.get('VALIDATION_ERRORS')),flush=True)
    result,metrics=await original(schema,system,user,*args,**kwargs)
    with (OUT/'batches.jsonl').open('a') as f:
        f.write(json.dumps({'service':user.get('SERVICE'),'topics':topics,'output':result.model_dump(),'metrics':metrics},ensure_ascii=False)+'\n')
    print('GENERATED',metrics,flush=True)
    return result,metrics


async def main(services):
    model_readings.call_model=observed
    first=Profile(name='지민',birth_date='2004-05-15',birth_time='10:30',city='seoul')
    second=Profile(name='서연',birth_date='2004-05-21',birth_time='10:30',city='busan')
    failed=False
    for service in services:
        started=time.monotonic()
        req=ReadRequest(service=service,profile=first,partner=second if service=='compatibility' else None)
        try:
            result=await read(req)
        except HTTPException as exc:
            failed=True
            failure={'service':service,'status':'rejected','reason':str(exc.__cause__),'seconds':round(time.monotonic()-started,2)}
            (OUT/(service+'-rejected.json')).write_text(json.dumps(failure,ensure_ascii=False,indent=2))
            print('REJECTED',failure,flush=True)
            continue
        assert result['editorial_mode']=='fresh_model'
        if service=='compatibility':
            chapters=result['compatibility_report']['chapters']
            assert len(chapters)==6
            assert all(p['report']['generation']['previous_reading_used'] is False for p in result['compatibility_report']['people'])
        else:
            chapters=result['report']['astrology']['interpretation'] if service=='stars' else result['report']['chapters']
        assert result['generation']['previous_reading_used'] is False
        paragraphs=[p for c in chapters for p in c['paragraphs']]
        assert len(paragraphs)==len(set(paragraphs))
        SESSIONS.pop(result['reading_id'],None)
        result['reading_id']=None;result['demo']=True;result['example_request']=req.model_dump(mode='json')
        (OUT/(service+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2))
        (OUT/(service+'.txt')).write_text(result['title']+'\n\n'+result['summary']+'\n\n'+'\n\n'.join(c['title']+'\n'+'\n\n'.join(c['paragraphs']) for c in chapters))
        print('VERIFIED',service,'model=',MODEL,'chapters=',len(chapters),'characters=',sum(map(len,paragraphs)),
              'seconds=',round(time.monotonic()-started,2),flush=True)
    return 1 if failed else 0


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--services',nargs='+',choices=['saju','stars','compatibility'],default=['saju','stars','compatibility'])
    raise SystemExit(asyncio.run(main(parser.parse_args().services)))
