import asyncio
import copy
import json
import unittest
from unittest.mock import AsyncMock, patch

from api.server import Profile, ReadRequest, facts_for, NOTES
from api.model_readings import (life_stage_data, raw_saju, payload, add_life_readings,
                                without_authored_prose, issues, CACHE,write_life,LifeDraft,LifeInterval)
from tests.test_model_readings import model_batch


def report(gender='male'):
    return facts_for(ReadRequest(service='saju',profile=Profile(name='가람',birth_date='2004-05-15',birth_time='10:30',gender=gender)),fresh=True)['chart']['report']


class LifeReadingsTests(unittest.IsolatedAsyncioTestCase):
    async def test_model_cannot_omit_an_index_and_ui_dates_are_calculated(self):
        CACHE.clear();r=report();data=life_stage_data(r,r['luck_cycles']['stages'][3])
        draft=LifeDraft(title='경험을 나누고 생활을 이어가는 흐름',intro='이 시기의 변화는 맡는 역할과 관계의 조건을 함께 살펴볼 수 있는 이야기예요. 과거의 사건을 알아낸 뜻이 아니라 어떤 활동에서 힘을 쓰고 부담이 생기는지 읽어요.',
            before_first_cycle=None,intervals=[LifeInterval(period_index=p['index'],paragraph=f"이 구간의 역할 {p['index']}에서는 생활의 새로운 조건을 바탕으로 각자의 경험을 나누고 약속을 함께 조율하는 장면을 떠올릴 수 있어요. 예를 들어 구간 {p['index']}의 모임에서 맡을 일을 정하고 서로의 역할을 구분하며 무엇을 시작하고 무엇을 유지할지 살펴보는 가정 상황이에요.") for p in data['luck_cycles']['periods']])
        with patch('api.model_readings.call_model',AsyncMock(return_value=(draft,{'seconds':0}))):
            result=await write_life(data,NOTES,'test','test',None)
        for p in data['luck_cycles']['periods']:self.assertIn(p['stage_age_label'],result['chapters'][0]['body'])
        self.assertEqual(result['metadata']['timeline_labels'],'calculated')
        CACHE.clear();draft.intervals.pop()
        bad=AsyncMock(return_value=(draft,{'seconds':0}))
        with patch('api.model_readings.call_model',bad):
            with self.assertRaises(ValueError):await write_life(data,NOTES,'test','test',None)
        self.assertEqual(bad.await_count,2)

    def test_age_prose_never_enters_writer_or_followup(self):
        r=report()
        for p in r['luck_cycles']['periods']:p.update(title='LEGACY',paragraphs=['LEGACY'],transition='LEGACY',calculation_text='LEGACY')
        for s in r['luck_cycles']['stages']:s['paragraphs']=['LEGACY']
        data=life_stage_data(r,r['luck_cycles']['stages'][0])
        self.assertNotIn('LEGACY',json.dumps(payload('saju',data,NOTES,[('life:growth','성장기 설명')]),ensure_ascii=False))
        followup=raw_saju(r,include_cycles=True)
        self.assertNotIn('LEGACY',json.dumps(followup))
        self.assertEqual(len(followup['luck_cycles']['periods']),10)
        self.assertNotIn('luck_cycles',raw_saju(r))

    def test_age_band_clips_periods_without_resetting_cycle_boundary(self):
        r=report();data=life_stage_data(r,r['luck_cycles']['stages'][1])
        for p in data['luck_cycles']['periods']:
            self.assertEqual(p['stage_start_months'],max(240,p['start_months']))
            self.assertEqual(p['stage_end_months'],min(480,p['end_months']))
        self.assertIsNone(data['life_stage']['before_first_cycle_until'])
        self.assertEqual(data['elements'],r['elements'])

    async def test_missing_calculation_criterion_never_generates_ages(self):
        r=report(None)
        with patch('api.model_readings.write_life',new_callable=AsyncMock) as writer:
            await add_life_readings(r,NOTES,'test','test',asyncio.Lock())
        writer.assert_not_awaited();self.assertFalse(r['luck_cycles']['available'])

    async def test_all_four_stages_are_new_and_require_actual_periods(self):
        r=without_authored_prose(report())
        r['generation']={'calls':[],'seconds':0,'actual_models':['test']}
        async def writer(data,notes,*args):
            topic='life:'+data['life_stage']['key'];batch=model_batch(data,[topic])
            while len(batch.chapters[0].paragraphs)<len(data['luck_cycles']['periods']):
                i=len(batch.chapters[0].paragraphs)
                batch.chapters[0].paragraphs.append(f'{topic}의 추가 구간 {i}에서는 실제로 계산한 기간의 흐름을 타고난 성향과 함께 이해하는 서로 다른 생활 예를 충분한 길이로 설명합니다.')
            batch.chapters[0].evidence_ids=[topic]+['cycle:'+str(p['index']) for p in data['luck_cycles']['periods']]
            batch.chapters[0].paragraphs[0]+=' '.join(p['stage_age_label'] for p in data['luck_cycles']['periods'])
            self.assertEqual(issues(batch,data,[topic],'saju'),[])
            bad=copy.deepcopy(batch);bad.chapters[0].evidence_ids=[topic]
            self.assertIn('기간',' '.join(issues(bad,data,[topic],'saju')))
            return {'chapters':[batch.chapters[0].model_dump()], 'metadata':{'calls':[],'seconds':1,'actual_models':['test'],'previous_reading_used':False}}
        with patch('api.model_readings.write_life',side_effect=writer):
            await add_life_readings(r,NOTES,'test','test',asyncio.Lock())
        self.assertEqual([s['key'] for s in r['luck_cycles']['stages']],['growth','youth','middle','later'])
        self.assertTrue(all(s['paragraphs'] for s in r['luck_cycles']['stages']))
        self.assertEqual(len(r['generation']['life_readings']),4)
