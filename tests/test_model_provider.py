import asyncio
import json
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from api import model_provider as provider
from api.model_provider import FREE_MODEL, ModelProviderError, Settings, complete, health_status

SCHEMA = {'type': 'object', 'properties': {'answer': {'type': 'string'}}, 'required': ['answer']}
MESSAGES = [{'role': 'system', 'content': '작성 지침'}, {'role': 'user', 'content': '계산값'}]
REMOTE = Settings(provider='openrouter', model=FREE_MODEL, api_key='test-secret-do-not-export')
CLIENT = httpx.AsyncClient


def mocked_client(handler):
    transport = httpx.MockTransport(handler)
    return patch('api.model_provider.httpx.AsyncClient', side_effect=lambda **kwargs: CLIENT(transport=transport, **kwargs))


class ProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_free_request_uses_server_headers_schema_and_records_actual_model(self):
        def respond(req):
            self.assertEqual(str(req.url), provider.OPENROUTER_URL + '/chat/completions')
            self.assertEqual(req.headers['Authorization'], 'Bearer ' + REMOTE.api_key)
            body = json.loads(req.content)
            self.assertEqual(body['messages'], MESSAGES)
            self.assertNotIn(REMOTE.api_key, req.content.decode())
            self.assertEqual(body['provider']['max_price'], {'prompt': 0, 'completion': 0, 'request': 0})
            self.assertTrue(body['provider']['require_parameters'])
            self.assertNotIn('models', body)
            self.assertEqual(body['response_format']['json_schema']['schema']['additionalProperties'], False)
            self.assertEqual(body['reasoning'], {'enabled': False})
            self.assertNotIn('num_ctx', body)
            return httpx.Response(200, json={'model': FREE_MODEL, 'choices': [{'message': {'content': '{"answer":"해설"}'}, 'finish_reason': 'stop'}],
                                            'usage': {'prompt_tokens': 100, 'completion_tokens': 10}})
        with mocked_client(respond):
            answer, metrics = await complete(SCHEMA, MESSAGES, FREE_MODEL, 'https://ignored.invalid', asyncio.Lock(), settings=REMOTE)
        self.assertEqual(json.loads(answer)['answer'], '해설')
        self.assertEqual(metrics['actual_model'], FREE_MODEL)
        self.assertNotIn(REMOTE.api_key, json.dumps(metrics))

    async def test_missing_key_and_paid_models_are_rejected_before_network(self):
        with patch('api.model_provider.httpx.AsyncClient') as client:
            for setting, model in [(Settings(provider='openrouter', model=FREE_MODEL), FREE_MODEL), (REMOTE, 'nvidia/paid-model')]:
                with self.assertRaises(ModelProviderError):
                    await complete(SCHEMA, MESSAGES, model, '', asyncio.Lock(), settings=setting)
            client.assert_not_called()

    async def test_auth_rate_limit_and_upstream_errors_do_not_leak_body(self):
        for status, expected in [(401, 'API 키'), (429, '한도'), (503, '연결하지')]:
            with self.subTest(status=status), mocked_client(lambda req: httpx.Response(status, json={'error': {'message': REMOTE.api_key}})):
                with self.assertRaises(ModelProviderError) as error:
                    await complete(SCHEMA, MESSAGES, FREE_MODEL, '', asyncio.Lock(), settings=REMOTE)
                self.assertIn(expected, str(error.exception))
                self.assertNotIn(REMOTE.api_key, str(error.exception))

    async def test_http_200_error_and_truncated_output_are_rejected(self):
        responses = [({'error': {'code': 429, 'message': REMOTE.api_key}}, ModelProviderError),
                     ({'choices': [{'message': {'content': '{'}, 'finish_reason': 'length'}]}, ValueError),
                     ({'choices': []}, ModelProviderError)]
        for body, error in responses:
            with mocked_client(lambda req: httpx.Response(200, json=body)):
                with self.assertRaises(error):
                    await complete(SCHEMA, MESSAGES, FREE_MODEL, '', asyncio.Lock(), settings=REMOTE)

    async def test_ollama_protocol_still_works_without_remote_key(self):
        def respond(req):
            self.assertEqual(str(req.url), 'http://127.0.0.1:11434/api/chat')
            self.assertNotIn('Authorization', req.headers)
            body = json.loads(req.content)
            self.assertEqual(body['format'], SCHEMA)
            self.assertFalse(body['think'])
            self.assertEqual(body['options']['num_ctx'], 12288)
            return httpx.Response(200, json={'message': {'content': '{"answer":"해설"}'}, 'done_reason': 'stop', 'eval_count': 10})
        with mocked_client(respond):
            answer, metrics = await complete(SCHEMA, MESSAGES, 'qwen3.5:9b', 'http://127.0.0.1:11434', asyncio.Lock(), settings=Settings())
        self.assertEqual(metrics['provider'], 'ollama')
        self.assertEqual(json.loads(answer)['answer'], '해설')

    async def test_json_object_models_receive_schema_in_instructions(self):
        setting=Settings(provider='openrouter',model='google/gemma-4-31b-it:free',api_key=REMOTE.api_key,json_mode='json_object')
        def respond(req):
            body=json.loads(req.content)
            self.assertEqual(body['response_format'],{'type':'json_object'})
            self.assertIn('JSON',body['messages'][0]['content'])
            self.assertIn('additionalProperties',body['messages'][0]['content'])
            return httpx.Response(200,json={'model':setting.model,'choices':[{'message':{'content':'{"answer":"형식 확인"}'},'finish_reason':'stop'}]})
        with mocked_client(respond):
            answer,metrics=await complete(SCHEMA,MESSAGES,setting.model,'',asyncio.Lock(),settings=setting)
        self.assertEqual(metrics['response_format'],'json_object')
        self.assertEqual(MESSAGES[0]['content'],'작성 지침')

    async def test_health_only_reads_catalog_and_never_exposes_credentials(self):
        def respond(req):
            self.assertEqual(req.method, 'GET')
            self.assertNotIn('Authorization', req.headers)
            return httpx.Response(200, json={'data': [{'id': FREE_MODEL, 'pricing': {'prompt': '0', 'completion': '0'}, 'supported_parameters': ['structured_outputs']}]})
        with mocked_client(respond):
            result = await health_status(REMOTE)
        self.assertTrue(result['ready'])
        self.assertFalse(result['credential_verified'])
        self.assertNotIn(REMOTE.api_key, json.dumps(result))

    async def test_health_blocks_model_that_became_paid_or_lost_schema_support(self):
        for price, parameters in [('1', ['structured_outputs']), ('0', ['temperature'])]:
            with mocked_client(lambda req: httpx.Response(200, json={'data': [{'id': FREE_MODEL, 'pricing': {'prompt': price}, 'supported_parameters': parameters}]})):
                self.assertFalse((await health_status(REMOTE))['ready'])

    async def test_api_propagates_safe_configuration_error_without_template_fallback(self):
        from api.server import Profile, ReadRequest, read, HTTPException
        with patch('api.model_readings.generate_report', AsyncMock(side_effect=ModelProviderError('API 키를 확인해 주세요.'))), patch('api.server.generate', AsyncMock()) as old:
            with self.assertRaises(HTTPException) as error:
                await read(ReadRequest(service='saju', profile=Profile(birth_date='2004-05-15')))
        self.assertEqual(error.exception.status_code, 503)
        self.assertIn('API 키', error.exception.detail)
        old.assert_not_called()

    async def test_full_read_and_followup_use_remote_transport_with_no_old_prose(self):
        from api.server import Profile, ReadRequest, read, ask, AskRequest, SESSIONS
        from api.model_readings import CACHE
        CACHE.clear()
        calls=[]
        def respond(req):
            body=json.loads(req.content)
            user=json.loads(body['messages'][1]['content'])
            self.assertNotIn('chapters',user['CALCULATIONS'])
            self.assertNotIn('VERIFIED_READING',user)
            self.assertNotIn('VERIFIED_DRAFT',user)
            ids=[e['id'] for e in user['CALCULATIONS']['evidence']]
            topics=[s['topic'] for s in user['SECTION_REQUESTS']]
            calls.append(topics or ['followup'])
            if topics:
                chapters=[]
                for topic in topics:
                    paragraphs=[f'{topic} 항목의 {i}번째 테스트 설명은 계산에서 읽은 서로 다른 역할을 생활 장면에 연결합니다. {topic} 예시 {i}에서는 실제로 겪은 일을 안다고 단정하지 않고, 가정한 상황에서 나타나는 장점과 그 장점이 과해졌을 때의 약점을 함께 설명합니다. {topic} 조건 {i}를 구분하여 단순한 반복으로 긴 본문을 채우지 않습니다.' for i in range(3)]
                    chapters.append({'topic':topic,'title':topic+' 항목의 개인 이야기','paragraphs':paragraphs,'reflection':'각 항목의 서로 다른 생활 조건을 살펴요.','evidence_ids':ids[:2]})
                output={'title':'계산으로 새로 읽는 개인 이야기','summary':'계산한 배치와 공통 참고 자료를 연결해 서로 다른 생활 영역을 설명해요.','chapters':chapters}
            else:
                output={'answer':'\n\n'.join([
                    '질문한 일하는 방식을 설명하는 테스트 답변입니다. 출생 정보에서 계산한 역할과 업무 조건을 연결하여, 자율적으로 결정하는 상황과 정해진 일정에 맞추는 상황을 나눠 읽어요. 확인한 자료 안에서 강점을 발휘할 수 있는 조건을 이야기합니다.',
                    '예를 들어 새로운 프로젝트를 맡았다는 가정으로 이해해 볼 수 있어요. 이것은 사용자가 실제로 경험한 일이 아니라 계산의 의미를 설명하기 위한 예시입니다. 계획을 세우는 과정과 실행을 구분해서 읽어야 해요.',
                    '주의할 부분은 장점을 모든 환경에서 같은 효과를 내는 능력으로 받아들이는 것입니다. 평가 기준이나 협업 조건에 따라 같은 태도도 다르게 작용할 수 있어요. 후속 질문 역시 기존 본문을 답안으로 복사하지 않고 처음의 계산 자료를 사용합니다.'
                ]), 'evidence_ids':ids[:2]}
            return httpx.Response(200,json={'model':FREE_MODEL,'choices':[{'message':{'content':json.dumps(output,ensure_ascii=False)},'finish_reason':'stop'}]})
        with patch('api.model_provider.CONFIG',REMOTE),patch('api.model_readings.CONFIG',REMOTE),mocked_client(respond):
            result=await read(ReadRequest(service='saju',profile=Profile(name='지민',birth_date='2004-05-15',birth_time='10:30')))
            try:
                self.assertEqual(result['generation']['provider'],'openrouter')
                self.assertEqual(result['generation']['actual_models'],[FREE_MODEL])
                self.assertEqual(len(result['report']['chapters']),11)
                self.assertFalse(result['generation']['previous_reading_used'])
                answer=await ask(AskRequest(reading_id=result['reading_id'],question='일하는 방식은 어떤가요?'))
                self.assertEqual(answer['answer_mode'],'fresh_model')
                self.assertEqual(answer['generation']['provider'],'openrouter')
            finally:SESSIONS.pop(result['reading_id'],None);CACHE.clear()
        self.assertEqual(len(calls),7)

    def test_remote_and_local_environment_settings_are_separate(self):
        env = {'MOA_LLM_PROVIDER': 'openrouter', 'OPENROUTER_API_KEY': REMOTE.api_key, 'MOA_MODEL': 'local-model'}
        settings = Settings.from_env(env)
        self.assertEqual(settings.model, FREE_MODEL)
        self.assertEqual(settings.url, provider.OPENROUTER_URL)
        self.assertNotIn(REMOTE.api_key, repr(settings))
        env['MOA_LLM_PROVIDER'] = 'ollama'
        self.assertEqual(Settings.from_env(env).model, 'local-model')
