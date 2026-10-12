"""Check actual distinctions and evidence boundaries, not prose length alone."""
from datetime import date, timedelta
import time
import unittest
from unittest.mock import AsyncMock, patch
from api.server import Profile, ReadRequest, chart, facts_for, TEN_GODS
from api.saju_report import build_chapters
from api.chart_context import context, role_for
from api.server import SESSIONS, ask, AskRequest, HTTPException, Answer, unsupported_interpretation, naming_output_issues


def report(day, time='10:30'):
    return chart(Profile(name='지민', birth_date=day, birth_time=time))['report']


class ReadingContextTests(unittest.TestCase):
    def test_same_stem_and_counts_different_placement(self):
        # Real dates either side of the solar month boundary. Their visible
        # ten-god histograms match; their month/day roles trade positions.
        left, right = report('2003-01-04'), report('2003-01-14')
        lc, rc = context(left), context(right)
        self.assertEqual(lc['day']['stem'], rc['day']['stem'])
        histogram=lambda r: sorted((g['name'],g['count']) for g in r['ten_gods'])
        self.assertEqual(histogram(left),histogram(right))
        self.assertNotEqual(lc['root'],rc['root'])
        self.assertNotEqual(lc['private'],rc['private'])
        a,b=build_chapters(left),build_chapters(right)
        self.assertNotEqual(a[0]['lead'],b[0]['lead'])
        for topic in ['overview','shadow','work','money','relationships','family','friends']:
            x=next(c for c in a if c['topic']==topic)
            y=next(c for c in b if c['topic']==topic)
            self.assertNotEqual(x['body'],y['body'],topic)
        pa={p for c in a for p in c['paragraphs']};pb={p for c in b for p in c['paragraphs']}
        self.assertLess(len(pa&pb)/min(len(pa),len(pb)),.4)

    def test_season_and_balance_are_not_count_rank(self):
        r=report('2004-05-15');c=context(r);chapters={x['topic']:x for x in build_chapters(r)}
        self.assertEqual(c['root'],'식신')
        self.assertEqual(c['outside'],'정재')
        self.assertEqual(c['private'],'상관')
        self.assertEqual(r['balance']['yong_element'],'수')
        self.assertIn('불을 돕는 계절',chapters['balance']['body'])
        self.assertIn('불 3개',chapters['elements']['body'])
        self.assertIn('말이나 결과물로',chapters['elements']['body'])
        self.assertEqual(role_for('화',c['day']['stem']['element']),'식상')
        self.assertIn('실제 성격을 알아낸 결과는 아닙니다',chapters['relationships']['body'])
        self.assertIn('아직 입력받지',chapters['relationships']['body'])
        self.assertNotIn('물이 많은 사람과 반드시 잘 맞',chapters['relationships']['body'])

    def test_unknown_hour_never_selects_partner_element(self):
        r=report('2004-05-15',None)
        self.assertFalse(r['balance']['available'])
        cs={x['topic']:x for x in build_chapters(r)}
        self.assertIn('아직 고르지',cs['relationships']['body'])
        self.assertIn('아직 모르는',cs['charm']['body'])
        self.assertNotIn('시주의 위 글자는',cs['charm']['body'])

    def test_visible_roles_and_evidence_references(self):
        for n in range(72):
            r=report(date(1997,2,1)+timedelta(days=n),None if n%2 else '10:30')
            observed={g['name'] for g in r['ten_gods']}
            ids={e['id'] for e in r['evidence']}
            for c in build_chapters(r):
                body=c['body']
                # A calculated pattern may borrow a hidden monthly stem; its
                # name is not a claim that this role is visibly counted.
                if c['topic']=='elements' and r['balance']['available']:
                    body=body.replace(r['balance']['pattern'],'')
                self.assertLessEqual({g for g in TEN_GODS if g in body},observed)
                self.assertLessEqual(set(c['evidence_ids']),ids)
                self.assertNotRegex(c['body'],r'여지을|신뢰을|태도이 |괴강|재고 귀인|이번 주')

    def test_element_relationship_is_relative_to_daymaster(self):
        self.assertEqual(role_for('화','목'),'식상')
        self.assertEqual(role_for('화','수'),'재성')
        self.assertEqual(role_for('화','금'),'관성')

    def test_generic_model_additions_are_rejected(self):
        facts=facts_for(ReadRequest(service='saju',profile=Profile(name='지민',birth_date='2004-05-15',birth_time='10:30')))
        for text in ['불이 많아서 밝고 활발한 사람이에요.','화가 많으면 감정이 격해져요.','창의력이 매우 뛰어나요.','나무가 불에 태워져 타인을 성장시키는 힘이에요.']:
            self.assertTrue(unsupported_interpretation(Answer(answer=text,source_ids=['saju-daymaster']),facts,'내 화의 기운은?'))
        self.assertFalse(unsupported_interpretation(Answer(answer='방법의 문제를 말하다 상대를 평가하는 말로 들릴 수 있어요.',source_ids=['saju-interpretation-rules']),facts,'내 약점은?'))


class NamingMeaningTests(unittest.TestCase):
    def consultation(self,hanja='智旻',**extra):
        p=Profile(name='지민',surname='박',surname_hanja='朴',name_hanja=hanja,
                  naming_preference='wisdom',birth_date='2026-05-15',birth_time='10:30')
        return facts_for(ReadRequest(service='name',profile=p.model_copy(update=extra)))['naming']

    def test_meaning_focus_and_current_candidate_comparison(self):
        a=self.consultation();b=self.consultation('智敏')
        candidate=next(r for r in a['recommendations'] if r['name_hanja']=='智敏')
        self.assertIn('旻',candidate['comparison'])
        self.assertIn('하늘',candidate['comparison'])
        self.assertIn('민첩함·총명함',candidate['comparison'])
        self.assertIn('뜻이 한 주제로 모이는',candidate['comparison'])
        self.assertNotEqual(a['summary'],b['summary'])
        am=next(c for c in a['chapters'] if c['topic']=='meaning')
        bm=next(c for c in b['chapters'] if c['topic']=='meaning')
        self.assertIn('다른 가치를', '\n'.join(am['paragraphs']))
        self.assertIn('의미의 폭은 좁아질', '\n'.join(bm['paragraphs']))
        for h in a['characters'][1:]:
            self.assertTrue(h['interpretation'] and h['good_for'] and h['consideration'])

    def test_hanja_changes_do_not_change_sound_or_birth_compatibility(self):
        a=self.consultation();b=self.consultation('智敏')
        self.assertEqual(a['sound_structure'],b['sound_structure'])
        self.assertEqual(a['birth'],b['birth'])
        self.assertEqual(a['sound_structure'][1]['final'],'ㄴ')
        for n in [a,b]:
            birth=next(c for c in n['chapters'] if c['topic']=='birth')
            self.assertIn('사주 적합도가 높아진다고 계산한 추천은 아닙니다','\n'.join(birth['paragraphs']))

    def test_name_does_not_improve_a_childs_ability(self):
        facts=facts_for(ReadRequest(service='name',profile=Profile(name='지민',name_hanja='智旻')))
        self.assertTrue(naming_output_issues(Answer(answer='敏은 현재의 지혜를 빠르게 발휘할 수 있게 돕습니다.',source_ids=['name-recommendation-rules']),facts))
        self.assertFalse(naming_output_issues(Answer(answer='敏은 민첩함·총명함이라는 뜻을 담는 글자예요.',source_ids=['name-hanja-dictionary']),facts))

    def test_name_question_preserves_actual_birth_coverage(self):
        facts=facts_for(ReadRequest(service='name',profile=Profile(name='지민',birth_date='2026-05-15',birth_time='10:30')))
        for text in ['출생 정보가 없으므로 용신을 판단하지 않았어요.','출생 시간이 입력되지 않았어요.']:
            self.assertTrue(naming_output_issues(Answer(answer=text,source_ids=['name-recommendation-rules']),facts))

    def test_unknown_dictionary_meaning_does_not_gain_editorial(self):
        from api.naming import character_detail
        d=character_detail('龘','답',0)
        self.assertIsNone(d['meaning'])
        self.assertEqual(d['interpretation'],'')
        self.assertEqual(d['good_for'],'')


class QuestionFallbackTests(unittest.IsolatedAsyncioTestCase):
    async def test_element_and_relationship_question_keeps_both_topics(self):
        facts=facts_for(ReadRequest(service='saju',profile=Profile(name='지민',birth_date='2004-05-15',birth_time='10:30')))
        key='context-fallback-test'
        SESSIONS[key]={'created':time.monotonic(),'facts':facts,'service':'saju','questions':0,
                       'reading':{'chapters':build_chapters(facts['chart']['report'])}}
        try:
            failure=HTTPException(503,'test rejected output')
            failure.__cause__=ValueError('Ungrounded editorial output')
            with patch('api.server.generate',AsyncMock(side_effect=failure)):
                a=await ask(AskRequest(reading_id=key,question='내 화의 기운은 무슨 뜻이고 어떤 사람이 잘 맞아?'))
            self.assertEqual(a['answer_mode'],'grounded_report')
            self.assertIn('불 3개',a['answer'])
            self.assertIn('물의 기운',a['answer'])
            self.assertEqual(facts['chart']['report']['balance']['yong_method'],'조후')
            self.assertIn('실제 두 사람이 맞는지는 여기서 정하지 않았어요',a['answer'])
            self.assertTrue(a['sources'])
        finally:SESSIONS.pop(key,None)


if __name__=='__main__':unittest.main()
