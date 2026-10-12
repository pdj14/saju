"""Check the configured provider; --generate uses a synthetic one-topic reading."""
import argparse
import asyncio
import json
from pathlib import Path

import httpx
from api.model_provider import CONFIG, ModelProviderError, OPENROUTER_URL, health_status, remote_error


async def main(generate=False):
    state = await health_status()
    print(json.dumps(state, ensure_ascii=False, indent=2))
    if not state['ready']: return 1
    if CONFIG.provider == 'openrouter':
        # Authentication check, no inference and no customer birth information.
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(OPENROUTER_URL + '/key', headers={'Authorization': 'Bearer ' + CONFIG.api_key})
                if response.is_error: raise ModelProviderError(remote_error(response.status_code))
                response.raise_for_status()
        except (httpx.HTTPError, ModelProviderError) as exc:
            print(str(exc) if isinstance(exc, ModelProviderError) else 'OpenRouter 인증 확인에 연결하지 못했어요.')
            return 1
        print('OpenRouter API 키 인증 확인 완료. 아직 해설 생성 요청은 보내지 않았어요.')
    if generate:
        from api.server import Profile, ReadRequest, facts_for, NOTES, LOCK, MODEL, OLLAMA
        from api.model_readings import write, raw_saju, SAJU
        req = ReadRequest(service='saju', profile=Profile(name='지민', birth_date='2004-05-15', birth_time='10:30', city='seoul'))
        facts = facts_for(req, fresh=True)
        try:
            result = await write('saju', raw_saju(facts['chart']['report']), NOTES, [('overview', SAJU['overview'])], MODEL, OLLAMA, LOCK)
        except (httpx.HTTPError, ModelProviderError, ValueError) as exc:
            print(str(exc) if isinstance(exc, (ModelProviderError, ValueError)) else '모델 연결 실패')
            return 1
        out = Path('.runtime/model-validation')
        out.mkdir(parents=True, exist_ok=True)
        (out / 'connection-sample.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
        print(result['title'] + '\n\n' + result['chapters'][0]['body'])
        print(json.dumps(result['metadata'], ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generate', action='store_true', help='Generate one synthetic topic (one call, at most one repair).')
    raise SystemExit(asyncio.run(main(parser.parse_args().generate)))
