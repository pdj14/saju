"""Check cycle direction, real boundaries, offsets and conditional scope."""
import unittest
from unittest.mock import patch
from datetime import datetime, timezone
from korean_saju import Daewoon, Gender, GanJi, Saju
from korean_saju.saju.daewoon import DaewoonEntry
from korean_saju.calendar.solar_term import SolarTermType
from api.server import Profile, chart, TERMS, moment, SESSIONS, AskRequest, ask
from api.luck_cycles import build_luck_cycles
import asyncio,time

class LuckCycleTests(unittest.TestCase):
    def make(self,day='2004-05-15',gender='male',clock='10:30'):
        return Profile(name='지민',birth_date=day,birth_time=clock,gender=gender)
    def test_direction_uses_year_polarity_and_explicit_criterion(self):
        for day in ['2004-05-15','2005-05-15']:
            male,female=[chart(self.make(day,g))['report'] for g in ['male','female']]
            expected=male['pillars'][0]['stem']['polarity']=='양'
            self.assertEqual(male['luck_cycles']['forward'],expected)
            self.assertEqual(female['luck_cycles']['forward'],not expected)
            self.assertEqual(male['elements'],female['elements'])
            self.assertEqual(male['ten_gods'],female['ten_gods'])
            self.assertNotEqual(male['luck_cycles']['periods'][0]['ganji'],female['luck_cycles']['periods'][0]['ganji'])
    def test_exact_boundary_and_ten_year_continuity(self):
        for gender in ['male','female']:
            p=self.make(gender=gender);r=chart(p)['report'];c=r['luck_cycles']
            boundary=datetime.fromisoformat(c['boundary']);gap=abs((boundary-moment(p).astimezone(timezone.utc)).total_seconds())/86400
            self.assertAlmostEqual(c['days_to_boundary'],gap,places=5)
            self.assertEqual(c['start_months'],round(gap*4))
            seq=c['periods'];self.assertEqual(len(seq),10)
            for i,x in enumerate(seq):
                self.assertEqual(x['start_months'],c['start_months']+i*120)
                self.assertEqual(x['end_months']-x['start_months'],120)
                self.assertEqual(x['start_months_offset'],c['start_months']%12)
                if i:self.assertEqual(seq[i-1]['end_months'],x['start_months'])
            self.assertEqual(len(c['stages']),4)
            self.assertTrue(r['interpretation_frame']['includes_luck_cycles'])
    def test_missing_time_or_criterion_never_filled_in(self):
        for gender,clock in [(None,'10:30'),('male',None),(None,None)]:
            r=chart(self.make(gender=gender,clock=clock))['report'];c=r['luck_cycles']
            self.assertFalse(c['available']);self.assertEqual(c['periods'],[])
            self.assertFalse(r['interpretation_frame']['includes_luck_cycles'])
    def test_twelve_month_offset_normalized_and_propagated(self):
        p=self.make();saju=Saju.from_birth(kst_moment=moment(p),solar_terms=TERMS,longitude=126.9784,hour_known=True,yaja_si_separated=True)
        r=chart(p)['report'];fake=Daewoon(entries=[DaewoonEntry(5, GanJi.by_index(i),12 if i==0 else 0) for i in range(10)],forward=True,days_to_boundary=17.9)
        with patch('api.luck_cycles.Daewoon.compute',return_value=fake):c=build_luck_cycles(saju,p,TERMS,r)
        self.assertEqual(c['start_months'],72)
        self.assertEqual([x['start_months'] for x in c['periods']],[72+i*120 for i in range(10)])
    def test_cycle_explanations_follow_calculated_roles_and_age_overlap(self):
        r=chart(self.make())['report'];c=r['luck_cycles'];ids={e['id'] for e in r['evidence']}
        self.assertIn('luck_cycles',ids)
        for p in c['periods']:
            self.assertIn(p['ganji'],p['calculation_text']);self.assertIn(p['branch_god'],p['calculation_text'])
            self.assertNotIn(p['ganji'],p['paragraphs'][0])
            self.assertEqual(p['support_elements'],[e for e in dict.fromkeys(p['elements']) if e in [r['balance']['yong_element'],r['balance']['hee_element']]])
        for stage in c['stages']:
            self.assertTrue(stage['paragraphs'])
            for index in stage['period_indices']:
                self.assertLess(c['periods'][index]['start_months'],100*12)
    def test_followup_returns_actual_calculated_periods(self):
        r=chart(self.make())['report'];key='luck-cycle-session-12345'
        SESSIONS[key]={'facts':{'chart':{'report':r}},'created':time.monotonic(),'questions':0,'service':'saju'}
        try:
            answer=asyncio.run(ask(AskRequest(reading_id=key,question='청년기 대운은 어떻게 달라져?')))
            self.assertEqual(answer['answer_mode'],'calculated_luck_cycles')
            for paragraph in r['luck_cycles']['stages'][1]['paragraphs']:self.assertIn(paragraph,answer['answer'])
            self.assertNotIn('노년기\n',answer['answer'])
        finally:SESSIONS.pop(key,None)

if __name__=='__main__':unittest.main()
