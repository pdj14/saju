import copy
import json
import unittest
from unittest.mock import AsyncMock,patch
from pydantic import ValidationError

from api.server import Profile,ReadRequest,NameCandidate,facts_for,NOTES,read,name_preview,SESSIONS,HTTPException
from api.name_readings import (naming_calculations,material,preview_names,comparison_issues,
                              name_issues,NameDraft,NameContext,NameChapter,ComparisonDraft,Choice,generate_names,CACHE,prose_issues)


def request():
    return ReadRequest(service='name',profile=Profile(name='지민',surname='박',birth_date='2026-05-15',birth_time='10:30'),
                       name_candidates=[NameCandidate(name='서연'),NameCandidate(name='가람')])


class NameInputTests(unittest.TestCase):
    def test_unvalidated_sound_element_fit_is_not_a_ranking_input(self):
        req=request();data=naming_calculations(req,facts_for(req,fresh=True),NOTES)
        user=material(data)
        for p in user['candidates']:
            self.assertNotIn('sound_elements',p)
            self.assertNotIn('sound_matches_birth_element',p)
            self.assertTrue(all('element' not in row for row in p['sound_structure']))
        self.assertEqual(user['birth']['profile']['name'],'아이')
        self.assertTrue(prose_issues('서연은 오행이 맞지 않아 다른 이름을 권합니다.',data))

    def test_inputs_bound_count_validate_characters_and_reject_duplicate(self):
        for kwargs in [dict(name_candidates=[NameCandidate(name='지민')]),
                       dict(name_candidates=[NameCandidate(name='서연')]*5)]:
            with self.assertRaises(ValidationError):ReadRequest(service='name',profile=Profile(name='지민'),**kwargs)
        for name,hanja in [('test',''),('지민','智'),('지민','ab')]:
            with self.assertRaises(ValidationError):NameCandidate(name=name,name_hanja=hanja)

    def test_first_generation_excludes_all_legacy_character_and_combination_prose(self):
        req=request();facts=facts_for(req,fresh=True)
        facts['chart']['report']['chapters']=[{'body':'LEGACY_SECRET'}]
        with patch('api.naming.CHARACTER_NOTES',{'智':['LEGACY_SECRET']*3}):
            data=naming_calculations(req,facts,NOTES)
        encoded=json.dumps(material(data),ensure_ascii=False)
        self.assertNotIn('LEGACY_SECRET',encoded)
        self.assertNotIn('"interpretation":',encoded)
        self.assertNotIn('"story":',encoded)
        self.assertEqual([p['name'] for p in data['candidates']],['지민','서연','가람'])
        self.assertTrue(data['birth']['pillars'])
        self.assertTrue(all(h['registry']['status']=='listed' for p in data['candidates'] for c in p['combinations'] if c['verified'] for h in c['characters']))

    def test_unverified_hanja_is_preserved_but_not_recommended(self):
        req=ReadRequest(service='name',profile=Profile(name='지민',name_hanja='智林'))
        data=naming_calculations(req,facts_for(req,fresh=True),NOTES)
        selected=data['candidates'][0]['combinations'][0]
        self.assertEqual(selected['id'],'selected');self.assertFalse(selected['verified'])

    def test_comparison_cannot_recommend_name_without_confirmed_combinations(self):
        req=request();data=naming_calculations(req,facts_for(req,fresh=True),NOTES)
        value=ComparisonDraft(title='같은 아이의 이름을 함께 비교해요',summary='확인한 한자의 뜻과 가족의 바람을 바탕으로 세 이름의 차이를 비교해요.',
            recommended_ids=['name:2'],choices=[Choice(id=p['id'],reason='확인한 글자와 원하는 의미를 바탕으로 후보별 차이를 설명하는 검증용 문장입니다.',concern='이 후보의 확인 자료와 가족의 바람에 맞는지 함께 살펴봐야 해요.') for p in data['candidates']],
            paragraphs=['후보들의 차이를 서로 비교해요.','자료가 없으면 추천을 보류하고 추가로 확인해요.'])
        self.assertTrue(comparison_issues(value,data))
        value.recommended_ids=['name:0'];self.assertEqual(comparison_issues(value,data),[])
        value.choices.pop();self.assertTrue(comparison_issues(value,data))


class NameFlowTests(unittest.IsolatedAsyncioTestCase):
    async def test_preview_has_pending_new_prose_and_raw_candidates_only(self):
        result=await name_preview(request())
        self.assertIsNone(result['report'])
        self.assertIsNone(result['naming_report']['comparison'])
        self.assertTrue(all(not p['chapters'] for p in result['naming_report']['candidate_reports']))

    async def test_read_failure_never_returns_legacy_naming(self):
        with patch('api.name_readings.generate_names',AsyncMock(side_effect=ValueError('bad'))),patch('api.server.generate',AsyncMock()) as legacy:
            with self.assertRaises(HTTPException) as error:await read(request())
        self.assertEqual(error.exception.status_code,503);legacy.assert_not_awaited()

    async def test_individual_and_comparison_calls_only_receive_raw_facts(self):
        req=request();data=naming_calculations(req,facts_for(req,fresh=True),NOTES)
        seen=[]
        async def call(schema,raw,instruction,validator,*args):
            seen.append(raw)
            self.assertNotIn('OLD_MODEL_PERSONAL_BODY',json.dumps(raw))
            if schema in [NameDraft,NameContext]:
                p=raw['candidates'][0]
                base=dict(title=p['name']+'의 뜻을 자세히 읽어봐요',summary='확인한 글자 뜻과 이름 소리를 각각 충분히 설명하고 선택 조건을 함께 살펴봐요.',
                    status='consider' if p['recommendable'] else 'needs_verification',verdict='이 이름은 가족의 바람과 확인된 뜻을 함께 비교하며 선택할 조건을 살펴볼 수 있어요.',
                    concerns=['확인 가능한 뜻과 가족이 바라는 의미가 얼마나 가까운지 살펴봐야 해요.'])
                value=NameContext(**base,chapters=[NameChapter(topic='sound',title='이름의 소리와 조건을 살펴봐요',paragraphs=['OLD_MODEL_PERSONAL_BODY '*20])]) if schema is NameContext else NameDraft(**base,combinations=[])
            else:
                value=ComparisonDraft(title='확인한 뜻으로 이름을 비교해요',summary='세 이름의 글자 뜻을 살펴보고 가족이 전하고 싶은 바람과 비교해 볼 수 있어요.',recommended_ids=['name:0'],
                    choices=[Choice(id=p['id'],reason='확인한 글자의 뜻과 원하는 바람 사이의 구체적인 차이를 비교해 볼 수 있어요.',concern='선택 조건과 확인 범위도 함께 읽어본 뒤 결정하면 좋아요.') for p in raw['candidates']],
                    paragraphs=['확인된 뜻을 비교해요.','기준이 다르면 다른 이름도 비교할 수 있어요.'])
            return value,{'calls':[],'seconds':0,'actual_models':['test'],'previous_reading_used':False}
        birth={'chapters':[],'metadata':{'calls':[],'seconds':0,'actual_models':['test'],'previous_reading_used':False}}
        with patch('api.name_readings.fresh_call',side_effect=call),patch('api.model_readings.write',AsyncMock(return_value=birth)):
            result=await generate_names(data,'test','test',None)
        self.assertEqual(len(seen),6);self.assertEqual([len(d['candidates']) for d in seen],[1,1,1,1,1,3])
        self.assertEqual(len(result['candidate_reports']),3)
