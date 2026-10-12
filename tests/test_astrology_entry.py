"""The astrology entry must present astronomical signs, not a saju introduction."""
import unittest
from unittest.mock import AsyncMock,patch
from api.server import Profile,ReadRequest,saju_preview,read,ask,AskRequest,Editorial,SESSIONS,NOTES
from api.model_readings import raw_stars


class AstrologyEntryTests(unittest.IsolatedAsyncioTestCase):
    async def test_stars_has_own_intro_and_role_specific_readings(self):
        req=ReadRequest(service='stars',profile=Profile(name='지민',birth_date='2004-05-15',birth_time='10:30'))
        result=await saju_preview(req);a=result['report']['astrology']
        self.assertIn('별자리',result['title']);self.assertNotIn('사주',result['title'])
        self.assertIn(a['sun']['sign'],result['summary']);self.assertIn(a['moon']['sign'],result['summary'])
        self.assertEqual(a['interpretation'],[])
        self.assertTrue(result['analysis_pending'])
        for key in ['Sun','Moon','Mercury','Venus','Mars']:
            position=next(p for p in a['positions'] if p['key']==key)
            self.assertTrue(position['sign_confirmed'])
            self.assertTrue(position['sign'])

    async def test_default_astrology_questions_do_not_fall_back_to_saju(self):
        req=ReadRequest(service='stars',profile=Profile(name='지민',birth_date='2004-05-15',birth_time='10:30'))
        preview=await saju_preview(req)
        a=preview['report']['astrology']
        chapter={'topic':'sun','title':'태양 '+a['sun']['sign'],'paragraphs':['태양의 별자리로 자신을 표현하는 방식을 읽어요.'],'body':'태양의 해설','reflection':'별자리의 뜻을 일상의 말로 읽어요.','evidence_ids':['planet:Sun'],'source_ids':['stars-natal']}
        preview['report']['astrology']['interpretation']=[chapter]
        generated={'editorial':{'title':'나의 별자리 해설','summary':'태양과 달의 별자리로 표현과 편안함을 함께 읽어요.','chapters':[chapter]*3},'report':preview['report'],'compatibility':None,'metadata':{'mode':'fresh_model'}}
        with patch('api.model_readings.generate_report',AsyncMock(return_value=generated)):
            result=await read(req)
        key=result['reading_id']
        try:
            self.assertIn('별자리',result['title']);self.assertNotIn('사주',result['title'])
            mock={'answer':'금성 '+next(p['sign'] for p in a['positions'] if p['key']=='Venus')+'의 애정 표현을 읽어요.','source_ids':['stars-symbols'],'answer_mode':'fresh_model'}
            with patch('api.model_readings.followup',AsyncMock(return_value=mock)):
                answer=await ask(AskRequest(reading_id=key,question='내 연애운과 취향은 어때?'))
            self.assertEqual(answer['answer_mode'],'fresh_model');self.assertIn('금성',answer['answer'])
            self.assertNotIn('용신',answer['answer']);self.assertNotIn('일간',answer['answer']);self.assertNotIn('사주',answer['answer'])
        finally:SESSIONS.pop(key,None)

    async def test_missing_hour_never_invents_moon_or_aspects(self):
        result=await saju_preview(ReadRequest(service='stars',profile=Profile(birth_date='2004-05-15')))
        a=result['report']['astrology']
        self.assertNotIn('moon',a);self.assertEqual(a['aspects'],[])
        self.assertEqual(a['interpretation'],[])
