"""Fresh generation must work with no previous personal prose available."""
import copy
import json
import unittest
from unittest.mock import AsyncMock,patch

from api.server import Profile,ReadRequest,facts_for,NOTES,read,SESSIONS,HTTPException
from api.model_readings import (raw_saju,raw_stars,raw_pair,payload,write,issues,
                                Batch,Chapter,SAJU,STARS,PAIR,CACHE,generate_report)
from api.model_readings import write_aspect_chapter


def facts(service='saju',unknown=False):
    return facts_for(ReadRequest(service=service,profile=Profile(name='가람',birth_date='2004-05-15',birth_time=None if unknown else '10:30'),
        partner=Profile(name='나래',birth_date='2004-05-21',birth_time='10:30') if service=='compatibility' else None))


def model_batch(data,topics):
    evidence=[e['id'] for e in data['evidence']]
    chapters=[]
    for topic in topics:
        paragraphs=[f'{topic} 항목의 {i}번째 설명은 서로 다른 생활 영역을 보여주는 테스트용 문장입니다. {topic} 장면 {i}에서는 개인의 실제 과거를 추정하지 않고 계산에서 읽는 역할의 장점과 그 장점이 과해지는 상황을 함께 다룹니다. {topic} 예시 {i}는 어떤 상황인지 이해할 수 있게 구체적인 장면을 충분한 길이로 작성합니다.' for i in range(3)]
        chapters.append(Chapter(topic=topic,title=topic+' 항목의 개인 해설',paragraphs=paragraphs,
                                reflection='이 항목에서는 생활의 서로 다른 조건을 함께 살펴요.',evidence_ids=evidence[:2]))
    return Batch(title='각자의 계산으로 읽는 개인 이야기',summary='계산한 배치와 공통 참고자료를 연결해 사람마다 다른 생활 영역을 설명해요.',chapters=chapters)


class RawInputTests(unittest.TestCase):
    def test_fresh_calculations_work_when_legacy_builders_are_unavailable(self):
        with (patch('api.interpretation.build_narrative',side_effect=AssertionError('no old reading')),
              patch('api.compatibility.build_compatibility',side_effect=AssertionError('no old pair reading')),
              patch('api.profile_report.build_astrology_narrative',side_effect=AssertionError('no old stars reading'))):
            for service in ['saju','stars','compatibility']:
                req=ReadRequest(service=service,profile=Profile(birth_date='2004-05-15',birth_time='10:30'),partner=Profile(birth_date='2004-05-21',birth_time='10:30') if service=='compatibility' else None)
                f=facts_for(req,fresh=True)
                self.assertTrue(f['chart']['report']['pillars'])
                if service=='compatibility':self.assertFalse(f['compatibility']['chapters'])
                else:self.assertFalse(f['astrology']['interpretation'])

    def test_legacy_prose_is_not_a_dependency_or_model_input(self):
        for service in ['saju','stars','compatibility']:
            f=facts(service)
            if service=='compatibility':
                c=f['compatibility'];c['summary']='LEGACY_SECRET'
                c['chapters']=[{'body':'LEGACY_SECRET'}]
                for p in c['people']:p['report']['chapters']=[{'body':'LEGACY_SECRET'}]
                for d in c['directions']:d['text']='LEGACY_SECRET'
                data=raw_pair(c);sections=list(PAIR.items())
            elif service=='stars':
                f['astrology']['interpretation']=[{'paragraphs':['LEGACY_SECRET']}]
                data=raw_stars(f['astrology'],f['chart']['report']['profile']);sections=list(STARS.items())
            else:
                r=f['chart']['report'];r['chapters']=[{'body':'LEGACY_SECRET'}];r['review_points']=[{'text':'LEGACY_SECRET'}]
                data=raw_saju(r);sections=list(SAJU.items())
            text=json.dumps(payload(service,data,NOTES,sections),ensure_ascii=False)
            self.assertNotIn('LEGACY_SECRET',text)
            self.assertNotIn('VERIFIED_READING',text)
            self.assertNotIn('VERIFIED_DRAFT',text)
            self.assertNotIn('PREVIOUS_READING',text)

    def test_placement_and_directional_facts_survive(self):
        f=facts('compatibility');d=raw_pair(f['compatibility'])
        self.assertEqual(d['directions'][0]['visible_count'],1)
        self.assertEqual(d['directions'][1]['visible_count'],0)
        self.assertEqual(d['primary_relations'][0]['kind'],'육충')
        self.assertNotEqual(d['people'][0]['chart']['pillars'],d['people'][1]['chart']['pillars'])

    def test_unknown_hour_does_not_gain_balance_or_moon(self):
        f=facts('stars',True)
        self.assertFalse(raw_saju(f['chart']['report'])['balance']['available'])
        d=raw_stars(f['astrology'],f['chart']['report']['profile'])
        self.assertFalse(d['hour_known']);self.assertEqual(d['aspects'],[])
        self.assertFalse(any(p['key']=='Moon' for p in d['positions']))

    def test_bad_references_jargon_repetition_and_counts_rejected(self):
        data=raw_saju(facts()['chart']['report']);b=model_batch(data,['overview','work'])
        self.assertEqual(issues(b,data,['overview','work'],'saju'),[])
        b.chapters[0].evidence_ids=['invented'];b.chapters[0].paragraphs[0]+=' 편재라는 운명이고 불 99개예요.'
        b.chapters[1].paragraphs[0]=b.chapters[0].paragraphs[0]
        errors=' '.join(issues(b,data,['overview','work'],'saju'))
        for item in ['근거','전문','개수','반복']:self.assertIn(item,errors)

    def test_stars_rejects_wrong_sign_and_saju(self):
        f=facts('stars');d=raw_stars(f['astrology'],f['chart']['report']['profile'])
        b=model_batch(d,['sun']);b.chapters[0].paragraphs[0]+=' 사주로 보면 태양은 물고기자리예요.'
        self.assertTrue(issues(b,d,['sun'],'stars'))

    def test_required_references_are_given_before_generation(self):
        f=facts('compatibility');data=raw_pair(f['compatibility'])
        material=payload('compatibility',data,NOTES,list(PAIR.items()))
        support=next(s for s in material['SECTION_REQUESTS'] if s['topic']=='support')
        self.assertEqual(support['required_evidence_ids'],['support:0','support:1'])
        question_text=' '.join(s['question'] for s in material['SECTION_REQUESTS'])
        for term in ['월지','월간','일지']:self.assertNotIn(term,question_text)
        f=facts('stars');data=raw_stars(f['astrology'],f['chart']['report']['profile'])
        b=model_batch(data,['aspects']);b.chapters[0].evidence_ids=['aspect:0']
        self.assertIn('관계',' '.join(issues(b,data,['aspects'],'stars')))
        b.chapters[0].evidence_ids=['aspect:'+str(i) for i in range(len(data['aspects']))]
        b.chapters[0].paragraphs[0]+=' 계산한 관계의 천체는 '+', '.join(dict.fromkeys(a[k] for a in data['aspects'] for k in ['left','right']))+'입니다.'
        self.assertEqual(issues(b,data,['aspects'],'stars'),[])


class GenerationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):CACHE.clear()

    async def test_aspects_get_independent_calculations_with_original_ids(self):
        f=facts('stars');data=raw_stars(f['astrology'],f['chart']['report']['profile'])
        observed=[]
        async def provider(schema,system,user,*args,**kwargs):
            d=user['CALCULATIONS'];self.assertEqual(len(d['aspects']),1)
            relation=d['aspects'][0];names=relation['left']+' · '+relation['right']
            ids=[e['id'] for e in d['evidence'] if e['id'].startswith('aspect:')]
            observed.extend(ids)
            b=model_batch(d,['aspects']);b.chapters[0].evidence_ids=ids
            b.chapters[0].paragraphs=[p.replace('aspects',names) for p in b.chapters[0].paragraphs]
            return b,{'seconds':.1,'actual_model':'test-model'}
        with patch('api.model_readings.call_model',AsyncMock(side_effect=provider)):
            result=await write_aspect_chapter(data,NOTES,'test-model','test-url',None)
        expected=['aspect:'+str(i) for i in range(len(data['aspects']))]
        self.assertEqual(observed,expected)
        self.assertEqual(result['chapter']['evidence_ids'],expected)
        self.assertEqual(len(result['metadata']),len(data['aspects']))

    async def test_entire_body_generated_from_raw_facts_and_cached(self):
        f=facts();data=raw_saju(f['chart']['report'])
        async def provider(schema,system,user,*args,**kwargs):
            self.assertIn('이전 풀이',system)
            self.assertNotIn('chapters',user['CALCULATIONS'])
            topics=[x['topic'] for x in user['SECTION_REQUESTS']]
            return model_batch(user['CALCULATIONS'],topics),{'seconds':.1,'input_tokens':100,'output_tokens':200,'done_reason':'stop'}
        mock=AsyncMock(side_effect=provider)
        with patch('api.model_readings.call_model',mock):
            a=await write('saju',data,NOTES,list(SAJU.items()),'test-model','test-url',None)
            b=await write('saju',data,NOTES,list(SAJU.items()),'test-model','test-url',None)
        self.assertEqual(len(a['chapters']),len(SAJU));self.assertGreater(mock.call_count,1)
        self.assertFalse(a['metadata']['previous_reading_used']);self.assertTrue(b['metadata']['cache_hit'])
        self.assertEqual(a['chapters'],b['chapters'])
        for chapter in a['chapters']:self.assertEqual(chapter['body'],'\n\n'.join(chapter['paragraphs']))

    async def test_invalid_output_repairs_once_and_never_falls_back(self):
        data=raw_saju(facts()['chart']['report']);b=model_batch(data,['overview']);b.chapters[0].evidence_ids=['invented']
        mock=AsyncMock(return_value=(b,{'seconds':.1}))
        with patch('api.model_readings.call_model',mock):
            with self.assertRaises(ValueError):await write('saju',data,NOTES,[('overview',SAJU['overview'])],'test-model','test-url',None)
        self.assertEqual(mock.call_count,2);self.assertFalse(CACHE)

    async def test_read_returns_failure_without_legacy_fallback(self):
        with patch('api.model_readings.generate_report',AsyncMock(side_effect=ValueError('bad model'))),patch('api.server.generate',AsyncMock()) as old:
            with self.assertRaises(HTTPException) as error:await read(ReadRequest(service='saju',profile=Profile(birth_date='2004-05-15')))
        self.assertEqual(error.exception.status_code,503);old.assert_not_called()

    async def test_live_read_uses_generated_summary_not_old_profile_summary(self):
        async def provider(schema,system,user,*args,**kwargs):
            return model_batch(user['CALCULATIONS'],[x['topic'] for x in user['SECTION_REQUESTS']]),{'seconds':.1}
        with patch('api.model_readings.call_model',AsyncMock(side_effect=provider)):
            result=await read(ReadRequest(service='saju',profile=Profile(birth_date='2004-05-15',birth_time='10:30')))
        try:
            self.assertEqual(result['editorial_mode'],'fresh_model')
            self.assertEqual(result['summary'],'계산한 배치와 공통 참고자료를 연결해 사람마다 다른 생활 영역을 설명해요.')
            self.assertTrue(SESSIONS[result['reading_id']]['narrative'])
            self.assertEqual(result['report']['astrology']['interpretation'],[])
            self.assertEqual(result['report']['review_points'],[])
        finally:SESSIONS.pop(result['reading_id'],None)
