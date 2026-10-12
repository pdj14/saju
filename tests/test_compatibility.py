"""Real computed synthetic pairs exercise support, conflicts and missing data."""
from copy import deepcopy
import unittest
from unittest.mock import AsyncMock, patch
from api.server import Profile,ReadRequest,facts_for,read,ask,AskRequest,SESSIONS,compatibility_preview,chart
from api.compatibility import branch_relations,BRANCH_TABLES


def request(right='2004-01-18',left_time='10:30',right_time='10:30'):
    return ReadRequest(service='compatibility',
        profile=Profile(name='지민',birth_date='2004-05-15',birth_time=left_time),
        partner=Profile(name='서연',birth_date=right,birth_time=right_time))


class CompatibilityTests(unittest.IsolatedAsyncioTestCase):
    def test_support_candidates_are_directional_and_use_actual_positions(self):
        c=facts_for(request())['compatibility'];a,b=c['directions']
        self.assertEqual((a['element'],a['visible_count']),('수',2))
        self.assertEqual((b['element'],b['visible_count']),('화',3))
        self.assertEqual(a['status'],'candidate_present')
        self.assertTrue(all(m['element']=='수' for m in a['matches']))
        self.assertEqual(len(c['people'][0]['report']['chapters']),13)
        self.assertNotIn('상대 명식을 아직 입력받지',str(c['people']))
        self.assertNotIn('score',c)

    def test_support_candidate_never_cancels_real_day_branch_clash(self):
        c=facts_for(request('2004-05-21'))['compatibility']
        self.assertEqual(c['directions'][0]['status'],'candidate_present')
        self.assertEqual(c['directions'][1]['status'],'no_visible_candidate')
        self.assertEqual(c['directions'][0]['visible_count'],1)
        self.assertIn('육충',[r['kind'] for r in c['primary_relations']])
        self.assertIn('day-branch-tension',[r['id'] for r in c['risks']])
        self.assertIn('사라지지',c['summary'])
        self.assertIn('근거를 찾지 못',c['directions'][1]['text'])

    def test_hour_missing_keeps_unknown_receiver_and_partial_other_separate(self):
        c=facts_for(request(left_time=None))['compatibility'];a,b=c['directions']
        self.assertEqual(a['status'],'unknown')
        self.assertFalse(b['other_hour_known'])
        self.assertTrue(any('시간' in w for w in c['warnings']))
        self.assertFalse(c['people'][0]['report']['balance']['available'])
        self.assertEqual(sum(p['known'] for p in c['people'][0]['report']['pillars']),3)

    def test_swap_people_swaps_support_direction_without_altering_chart(self):
        original=request();swapped=ReadRequest(service='compatibility',profile=original.partner,partner=original.profile)
        a=facts_for(original);b=facts_for(swapped)
        self.assertEqual(a['chart']['pillars'],b['partner_chart']['pillars'])
        self.assertEqual(a['compatibility']['directions'][0]['matches'],b['compatibility']['directions'][1]['matches'])
        self.assertEqual(a['compatibility']['primary_relations'][0]['kind'] if a['compatibility']['primary_relations'] else None,
                         b['compatibility']['primary_relations'][0]['kind'] if b['compatibility']['primary_relations'] else None)

    def test_pairwise_tables_match_pinned_engine_and_do_not_infer_triples(self):
        from korean_saju.saju import hapchung as engine
        for kind,rows in [('육합',engine._YUK_HAPS),('육충',engine._CHUNGS),('파',engine._PAS),('해',engine._HAES)]:
            expected={frozenset(x.hanja for x in (row.pair if kind=='육합' else row)) for row in rows}
            self.assertEqual({frozenset(p) for p in BRANCH_TABLES[kind]},expected)
        self.assertEqual(set(branch_relations('巳','申')),{'육합','파'})
        self.assertEqual(branch_relations('子','子'),[])
        self.assertEqual(branch_relations('辰','辰'),['형'])
        self.assertNotIn('삼합',branch_relations('申','子'))

    def test_personal_risks_have_conditional_balance_basis(self):
        weak=chart(Profile(birth_date='2004-05-15',birth_time='10:30'))['report']
        missing=chart(Profile(birth_date='2004-05-15'))['report']
        self.assertIn('output-with-weak-support',[p['id'] for p in weak['review_points']])
        self.assertNotIn('output-with-weak-support',[p['id'] for p in missing['review_points']])
        point=next(p for p in weak['review_points'] if p['id']=='output-with-weak-support')
        self.assertIn('불리한 조건',point['text']);self.assertIn('신약',point['basis'])

    async def test_preview_and_followup_reuse_comparison_not_personality_fitting(self):
        req=request('2004-05-21');preview=await compatibility_preview(req)
        c=deepcopy(preview['compatibility_report'])
        chapter={'topic':'support','title':'서로에게 다른 도움과 부담','paragraphs':['두 사람의 도움과 마찰을 함께 읽어요.'],
                 'body':'두 사람의 도움과 마찰을 함께 읽어요.','reflection':'도움이 있어도 충돌이 사라지지는 않아요.',
                 'source_ids':['saju-relations'],'evidence_ids':['support:0','support:1']}
        c['chapters']=[chapter]*3
        generated={'editorial':{'title':'두 사람의 서로 다른 관계 방식','summary':'계산에서 확인한 도움과 충돌을 함께 풀어 읽어요.','chapters':c['chapters']},'report':None,'compatibility':c,'metadata':{'mode':'fresh_model'}}
        with patch('api.model_readings.generate_report',AsyncMock(return_value=generated)):
            result=await read(req)
            key=result['reading_id'];before=deepcopy(SESSIONS[key]['facts'])
            try:
                self.assertEqual(result['compatibility_report']['primary_relations'],preview['compatibility_report']['primary_relations'])
                self.assertEqual(result['compatibility_report']['directions'],preview['compatibility_report']['directions'])
                mock={'answer':'물의 기운이 보완 후보로 보여도 계산에서 확인한 충돌 관계는 남아요.','source_ids':['saju-relations'],'answer_mode':'fresh_model'}
                with patch('api.model_readings.followup',AsyncMock(return_value=mock)):
                    answer=await ask(AskRequest(reading_id=key,question='나는 잘 맞는다고 생각해. 물 기운을 보완해주면 안 맞는 점은 없어?'))
                self.assertIn('충돌',answer['answer']);self.assertIn('물의 기운',answer['answer'])
                self.assertIn('육충',[r['kind'] for r in before['compatibility']['primary_relations']])
                self.assertEqual(SESSIONS[key]['facts'],before)
                self.assertTrue(answer['sources'])
            finally:SESSIONS.pop(key,None)
