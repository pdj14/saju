"""Server-only model transport for local Ollama and free OpenRouter models."""
import copy
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env', override=False)
FREE_MODEL = 'nvidia/nemotron-3-super-120b-a12b:free'
OPENROUTER_URL = 'https://openrouter.ai/api/v1'


class ModelProviderError(RuntimeError):
    """A safe, actionable message; never includes credentials or response bodies."""


@dataclass(frozen=True)
class Settings:
    provider: str = 'ollama'
    model: str = 'qwen3.5:9b'
    ollama_url: str = 'http://127.0.0.1:11434'
    api_key: str = field(default='', repr=False)
    site_url: str = 'http://127.0.0.1:8787'
    app_name: str = 'Moa'
    json_mode: str = 'json_schema'

    @classmethod
    def from_env(cls, env=None):
        env = os.environ if env is None else env
        provider = env.get('MOA_LLM_PROVIDER', 'ollama').strip().lower()
        return cls(provider=provider,
            model=env.get('OPENROUTER_MODEL', FREE_MODEL).strip() if provider == 'openrouter' else env.get('MOA_MODEL', 'qwen3.5:9b').strip(),
            ollama_url=env.get('MOA_OLLAMA_URL', 'http://127.0.0.1:11434').rstrip('/'),
            api_key=env.get('OPENROUTER_API_KEY', '').strip(),
            site_url=env.get('OPENROUTER_SITE_URL', 'http://127.0.0.1:8787').strip(),
            app_name=env.get('OPENROUTER_APP_NAME', 'Moa').strip(),
            json_mode=env.get('OPENROUTER_JSON_MODE', 'json_schema').strip())

    def check(self, model=None):
        if self.provider not in {'ollama', 'openrouter'}:
            raise ModelProviderError('MOA_LLM_PROVIDER를 openrouter 또는 ollama로 설정해 주세요.')
        if self.provider == 'openrouter':
            if self.json_mode not in {'json_schema','json_object'}:
                raise ModelProviderError('OPENROUTER_JSON_MODE를 json_schema 또는 json_object로 설정해 주세요.')
            selected = self.model if model is None else model
            if selected != 'openrouter/free' and not selected.endswith(':free'):
                raise ModelProviderError('무료 모델만 사용할 수 있어요. OPENROUTER_MODEL에 :free 모델 또는 openrouter/free를 설정해 주세요.')
            if not self.api_key or self.api_key.startswith(('your-', 'sk-or-v1-여기', 'PASTE_')):
                raise ModelProviderError('sites/moa/.env에 OPENROUTER_API_KEY를 입력하고 서버를 다시 실행해 주세요.')

    @property
    def url(self):
        return OPENROUTER_URL if self.provider == 'openrouter' else self.ollama_url


CONFIG = Settings.from_env()


def strict_schema(schema):
    result = copy.deepcopy(schema)
    def walk(value):
        if isinstance(value, dict):
            if value.get('type') == 'object':
                value['additionalProperties'] = False
                value['required'] = list(value.get('properties', {}))
            for item in value.values(): walk(item)
        elif isinstance(value, list):
            for item in value: walk(item)
    walk(result)
    return result


def remote_error(status):
    return {
        400: 'OpenRouter가 요청 형식이나 모델 옵션을 지원하지 않아요. 모델의 JSON 구조 출력 지원을 확인해 주세요.',
        401: 'OpenRouter API 키가 유효하지 않아요. .env의 OPENROUTER_API_KEY를 확인해 주세요.',
        402: 'OpenRouter 계정의 이용 조건 또는 한도를 확인해 주세요. 유료 모델로 자동 전환하지 않았어요.',
        403: 'OpenRouter가 이 요청을 허용하지 않았어요. 계정과 모델의 이용 설정을 확인해 주세요.',
        404: '설정한 무료 모델을 찾을 수 없어요. OPENROUTER_MODEL을 확인해 주세요.',
        429: 'OpenRouter 무료 이용 한도에 도달했거나 요청이 몰렸어요. 잠시 후 다시 시도해 주세요.',
    }.get(status, 'OpenRouter 무료 모델에 연결하지 못했어요. 잠시 후 다시 시도해 주세요.')


async def complete(output_schema, messages, model, url, lock, *, output_limit=3000, context_size=12288, settings=None):
    """Return just the answer and non-sensitive timing/model metadata."""
    settings = CONFIG if settings is None else settings
    settings.check(model)
    started = time.monotonic()
    if settings.provider == 'openrouter':
        headers = {'Authorization': 'Bearer ' + settings.api_key, 'Content-Type': 'application/json',
                   'HTTP-Referer': settings.site_url, 'X-OpenRouter-Title': settings.app_name}
        body = {'model': model, 'messages': messages, 'stream': False, 'temperature': 0.2, 'seed': 42,
                'max_tokens': output_limit, 'reasoning': {'enabled': False},
                'response_format': {'type': 'json_schema', 'json_schema': {
                    'name': 'moa_reading', 'strict': True, 'schema': strict_schema(output_schema)}},
                'provider': {'require_parameters': True, 'max_price': {'prompt': 0, 'completion': 0, 'request': 0}}}
        if settings.json_mode == 'json_object':
            body['response_format']={'type':'json_object'}
            body['messages']=copy.deepcopy(messages)
            body['messages'][0]['content']+='\n아래 JSON 스키마에 맞는 객체만 반환하세요. 스키마 자체를 답으로 복사하지 마세요.\n'+json.dumps(strict_schema(output_schema),ensure_ascii=False)
        endpoint = OPENROUTER_URL + '/chat/completions'
    else:
        headers = {}
        body = {'model': model, 'messages': messages, 'stream': False, 'think': False,
                'format': output_schema, 'keep_alive': '10m', 'options': {
                    'temperature': 0.2, 'seed': 42, 'num_ctx': context_size, 'num_predict': output_limit}}
        endpoint = url.rstrip('/') + '/api/chat'
    try:
        async with lock, httpx.AsyncClient(timeout=240) as client:
            response = await client.post(endpoint, headers=headers, json=body)
            if settings.provider == 'openrouter' and response.is_error:
                raise ModelProviderError(remote_error(response.status_code))
            response.raise_for_status()
            raw = response.json()
    except httpx.HTTPError:
        if settings.provider == 'openrouter':
            raise ModelProviderError('OpenRouter 연결 시간이 초과됐거나 연결이 끊겼어요. 다시 시도해 주세요.') from None
        raise
    if settings.provider == 'openrouter':
        # Some upstream errors arrive inside an HTTP 200 response.
        if raw.get('error'):
            raise ModelProviderError(remote_error(raw['error'].get('code')))
        choices = raw.get('choices') or []
        if not choices:
            raise ModelProviderError('무료 모델이 답변을 반환하지 않았어요. 다시 시도해 주세요.')
        choice = choices[0]
        if choice.get('error'):
            raise ModelProviderError('무료 모델에서 생성 오류가 발생했어요. 다시 시도해 주세요.')
        content = choice.get('message', {}).get('content')
        reason = choice.get('finish_reason')
        usage = raw.get('usage') or {}
        metrics = {'provider': 'openrouter', 'actual_model': raw.get('model', model),
                   'response_format': settings.json_mode,
                   'input_tokens': usage.get('prompt_tokens'), 'output_tokens': usage.get('completion_tokens'),
                   'done_reason': reason}
    else:
        content = raw.get('message', {}).get('content')
        reason = raw.get('done_reason')
        metrics = {'provider': 'ollama', 'actual_model': raw.get('model', model),
                   'input_tokens': raw.get('prompt_eval_count'), 'output_tokens': raw.get('eval_count'),
                   'done_reason': reason}
    if reason == 'length': raise ValueError('모델 출력 한도에 도달했습니다.')
    if not isinstance(content, str) or not content.strip():
        raise ValueError('모델이 JSON 본문을 반환하지 않았습니다.')
    metrics['seconds'] = round(time.monotonic() - started, 2)
    return content, metrics


async def health_status(settings=None):
    """Read model availability without sending personal data or generating text."""
    settings = CONFIG if settings is None else settings
    state = {'ready': False, 'provider': settings.provider, 'model': settings.model}
    try:
        settings.check()
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(OPENROUTER_URL + '/models' if settings.provider == 'openrouter' else settings.url + '/api/tags')
            r.raise_for_status()
            raw = r.json()
        if settings.provider == 'openrouter':
            entry = next((m for m in raw.get('data', []) if m['id'] == settings.model), None)
            if entry is None: raise ModelProviderError('무료 모델 목록에 설정한 모델이 없어요. OPENROUTER_MODEL을 확인해 주세요.')
            pricing = entry.get('pricing', {})
            if any(float(pricing.get(k, 0)) != 0 for k in ['prompt', 'completion', 'request']):
                raise ModelProviderError('이 모델은 현재 무료가 아니어서 사용을 중단했어요.')
            required_parameter='structured_outputs' if settings.json_mode=='json_schema' else 'response_format'
            if required_parameter not in entry.get('supported_parameters', []):
                raise ModelProviderError('이 모델은 필요한 JSON 구조 출력을 지원하지 않아요. 다른 무료 모델을 선택해 주세요.')
            state.update(ready=True, credential_verified=False)
        else:
            state['ready'] = any(m['name'] == settings.model for m in raw.get('models', []))
            if not state['ready']: state['reason'] = '설정한 로컬 모델을 찾을 수 없어요.'
    except ModelProviderError as exc:
        state['reason'] = str(exc)
    except (httpx.HTTPError, ValueError, KeyError):
        state['reason'] = '모델 목록에 연결하지 못했어요. 서버 연결을 확인해 주세요.'
    return state
