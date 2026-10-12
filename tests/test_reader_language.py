"""Plain public prose keeps differences, conflicts, and traceable facts."""
from datetime import date,timedelta
import re
import unittest
from api.server import Profile, chart, ReadRequest, facts_for
from api.saju_report import build_chapters, TEN_GODS

TERMS=list(TEN_GODS)+['일간','월지','월간','일지','일주','용신','희신','신약','신강','억부','격국','식상','재성','관성','비겁','인성','보완 후보']

class ReaderLanguageTests(unittest.TestCase):
    def test_plain_chapters_across_real_birth_charts_preserve_evidence(self):
        roots=set();bodies=set()
        for i in range(60):
            r=chart(Profile(birth_date=date(2004,1,1)+timedelta(days=17*i),birth_time=None if i%4==0 else '10:30',gender='female'))['report']
            chapters=build_chapters(r);ids={e['id'] for e in r['evidence']}
            self.assertEqual(len(chapters),13)
            self.assertGreater(sum(len(c['body']) for c in chapters),6500)
            for c in chapters:
                text=c['body']+c['title']+c['reflection']
                self.assertFalse(any(term in text for term in TERMS), (i,c['topic']))
                self.assertIsNone(re.search(r'[\u4e00-\u9fff]',text))
                self.assertTrue(set(c['evidence_ids'])<=ids)
                self.assertEqual(c['body'],'\n\n'.join(c['paragraphs']))
                self.assertGreaterEqual(len(c['paragraphs']),4)
            if r['luck_cycles']['available']:
                for obj in r['luck_cycles']['periods']+r['luck_cycles']['stages']:
                    text=' '.join(obj['paragraphs'])
                    self.assertFalse(any(t in text for t in TERMS))
                    self.assertIsNone(re.search(r'[\u4e00-\u9fff]',text))
            roots.add(next(p for p in r['pillars'] if p['position']=='month')['branch']['ten_god'])
            bodies.add(chapters[0]['body'])
        self.assertGreaterEqual(len(roots),8);self.assertEqual(len(bodies),60)

    def test_pair_support_does_not_repeat_in_strengths_or_hide_clashes(self):
        def pair(day):
            return facts_for(ReadRequest(service='compatibility',profile=Profile(name='지민',birth_date='2004-05-15',birth_time='10:30'),partner=Profile(name='서연',birth_date=day,birth_time='10:30')))['compatibility']
        a,b=pair('2004-01-18'),pair('2004-05-21')
        for c in [a,b]:
            chapters={x['topic']:x for x in c['chapters']}
            self.assertNotEqual(chapters['support']['body'],chapters['strengths']['body'])
            for chapter in c['chapters']:
                self.assertFalse(any(t in chapter['body'] for t in TERMS))
                self.assertIsNone(re.search(r'[\u4e00-\u9fff]',chapter['body']))
            self.assertTrue(all(x['text'] not in chapters['strengths']['body'] for x in c['directions']))
        self.assertNotEqual(a['chapters'][0]['body'],b['chapters'][0]['body'])
        self.assertIn('육충',[x['kind'] for x in b['primary_relations']])
        self.assertIn('충돌',next(x['body'] for x in b['chapters'] if x['topic']=='risks'))
        self.assertIn('근거를 찾지 못',b['directions'][1]['text'])
