"""Semantic regressions and convention differences, using synthetic profiles."""
from copy import deepcopy
from datetime import datetime
import time
import unittest
from unittest.mock import patch, AsyncMock
from api.server import Profile, ReadRequest, chart, facts_for, unsupported_interpretation, Answer, SESSIONS, ask, AskRequest, HTTPException
from api.chart_context import context
from api.saju_report import build_chapters
from api.time_basis import equation_of_time_minutes


class InterpretationAuditTests(unittest.IsolatedAsyncioTestCase):
    def test_monthly_finance_roles_distinguish_expression(self):
        contexts=[]
        for birthday,outside in [('1997-01-15','편재'),('1998-06-07','정재')]:
            r=chart(Profile(birth_date=birthday,birth_time='10:30'))['report'];c=context(r);contexts.append(c)
            self.assertEqual((c['root'],c['outside']),('식신',outside))
            chapters={x['topic']:x for x in build_chapters(r)}
            self.assertIn('monthly-roles:식신+'+outside,chapters['work']['rule_ids'])
            self.assertIn('생각',chapters['work']['body'])
            self.assertNotIn('새 아이디어만 내는 자리보다',chapters['work']['body'])
            self.assertNotIn(outside,chapters['money']['body'])
            self.assertIn('새로운 수요와 거래' if outside=='편재' else '수입·비용·약속',chapters['money']['body'])
        self.assertNotEqual(contexts[0]['work_title'],contexts[1]['work_title'])
        self.assertNotEqual(contexts[0]['work_risk'],contexts[1]['work_risk'])

    def test_private_role_does_not_replace_monthly_work_combination(self):
        r=chart(Profile(birth_date='1997-01-15',birth_time='10:30'))['report'];changed=deepcopy(r)
        next(p for p in changed['pillars'] if p['position']=='day')['branch']['ten_god']='정인'
        left,right=context(r),context(changed)
        self.assertEqual(left['work_pair_text'],right['work_pair_text'])
        self.assertEqual(left['work_title'],right['work_title'])
        self.assertNotEqual(left['private'],right['private'])

    def test_time_comparison_never_replaces_selected_chart(self):
        p=Profile(birth_date='2004-02-28',birth_time='01:30',city='busan')
        r=chart(p)['report'];basis=r['input_basis'];options={x['key']:x for x in basis['comparison']['options']}
        self.assertTrue(basis['comparison']['changes_pillars'])
        actual={x['position']:x for x in r['pillars']}
        self.assertEqual(actual['hour']['ganji'],options['mean']['hour'])
        self.assertNotEqual(options['mean']['hour'],options['apparent']['hour'])
        self.assertFalse(basis['equation_of_time_applied'])
        self.assertEqual(p.city,'busan')
        unknown=chart(p.model_copy(update={'birth_time':None}))['report']['input_basis']
        self.assertIsNone(unknown['corrected_time']);self.assertNotIn('comparison',unknown)

    def test_noaa_equation_units_and_sign(self):
        self.assertAlmostEqual(equation_of_time_minutes(datetime(2004,2,28,1,30)),-13.16668903,places=7)
        self.assertGreater(equation_of_time_minutes(datetime(2004,11,3,12)),15)

    async def test_claimed_personality_does_not_change_calculated_facts(self):
        facts=facts_for(ReadRequest(service='saju',profile=Profile(birth_date='1997-01-15',birth_time='10:30')))
        before=deepcopy(facts);key='synthetic-audit-personality'
        SESSIONS[key]={'facts':facts,'service':'saju','reading':{'chapters':build_chapters(facts['chart']['report'])},'notes':[],'created':time.monotonic(),'questions':0}
        try:
            failure=HTTPException(503,'rejected output')
            failure.__cause__=ValueError('Ungrounded editorial output')
            with patch('api.server.retrieve',return_value=[]), patch('api.server.generate',AsyncMock(side_effect=failure)):
                answer=await ask(AskRequest(reading_id=key,question='나는 창의적인 아이디어를 좋아해. 내 직업 성향은?'))
            self.assertEqual(facts,before)
            self.assertTrue(answer['answer'])
            self.assertTrue(unsupported_interpretation(Answer(answer='새 아이디어보다 반복 업무가 맞아요.',source_ids=['saju-ten-gods']),facts,'직업 성향은?'))
        finally:SESSIONS.pop(key,None)

    def test_career_has_actual_roles_not_invented_promotions(self):
        for day in ['1997-01-15','1998-06-07','2004-05-15']:
            r=chart(Profile(birth_date=day,birth_time='10:30'))['report']
            chapters=build_chapters(r);self.assertEqual(len(chapters),13)
            career=next(c for c in chapters if c['topic']=='career')
            self.assertIn('권한',career['body']);self.assertIn('평가',career['body'])
            self.assertIn('승진 여부',career['body'])
            self.assertNotIn('승진이 보장',career['body'])
