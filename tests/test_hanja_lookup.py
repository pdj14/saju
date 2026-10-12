"""Regression checks for dictionary coverage beyond editorial name themes."""
import json
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from api.naming import candidates, character_detail, dictionary_options, REGISTRY
from api.name_readings import (NameAnswer, followup_name, naming_calculations,
                               prose_issues, has_verified_meaning, output_schema,
                               ComparisonDraft, NameDraft)
from api.server import Profile, ReadRequest, facts_for, NOTES


def calculations():
    request=ReadRequest(service='name',profile=Profile(name='이솔',surname='김'))
    return naming_calculations(request,facts_for(request,fresh=True),NOTES)


class HanjaLookupTests(unittest.TestCase):
    def test_esol_searches_beyond_editorial_themes_and_varies_last_character(self):
        rows,_=candidates(Profile(name='이솔'))
        self.assertEqual(len(rows),3)
        self.assertEqual(rows[0]['name_hanja'],'怡率')
        self.assertEqual({r['name_hanja'][-1] for r in rows},set('率帥䢦'))
        self.assertTrue(all(h['registry']['status']=='listed' for r in rows for h in r['characters']))
        with patch('api.naming.CHAR_THEMES',{}):
            self.assertTrue(candidates(Profile(name='이솔'))[0])

    def test_source_definition_can_be_used_without_inventing_korean_gloss(self):
        detail=character_detail('乺','솔',0)
        self.assertIsNone(detail['meaning'])
        self.assertTrue(detail['definition'])
        self.assertTrue(has_verified_meaning(detail))
        with patch('api.naming.DICTIONARY',{'乺':{'definition':'painting tool place name','readings':['솔']}}):
            rows,_=candidates(Profile(name='솔'))
            self.assertEqual([r['name_hanja'] for r in rows],['乺'])

    def test_reading_specific_meaning_and_court_only_readings_reach_picker(self):
        self.assertEqual(character_detail('率','솔',0)['meaning'],'거느림·이끎')
        self.assertEqual(character_detail('率','율',0)['meaning'],'비율·정도')
        choices=json.loads((Path(__file__).resolve().parents[1]/'dist/assets/hanja-choices.json').read_text())['readings']
        rate=next(h for h in choices['솔'] if h['c']=='率')
        self.assertEqual(rate['m'],'거느림·이끎');self.assertTrue(rate['legal'])
        for c in REGISTRY['readings']['솔']:
            self.assertIn(c,[h['c'] for h in choices['솔']])

    def test_false_absence_is_rejected_but_incomplete_coverage_is_not(self):
        data=calculations();data['dictionary_lookup']={'솔':dictionary_options('솔')}
        for text in ['솔에 해당하는 표준 한자가 없습니다.','솔 소리의 한자는 존재하지 않습니다.']:
            self.assertTrue(prose_issues(text,data))
        self.assertEqual(prose_issues('이솔의 기존 추천에는 없었지만 率은 솔 독음과 뜻이 확인됩니다.',data),[])
        self.assertTrue(prose_issues('率의 표준 독음은 율·률이므로 이름 독음에 차이가 있습니다.',data))
        self.assertTrue(prose_issues('국립전자문서센터의 자료에서 확인했습니다.',data))
        self.assertTrue(prose_issues('이율(李率)을 예시로 제시합니다.',data))

    def test_schema_separates_name_identifiers_from_combination_identifiers(self):
        data=calculations()
        names=output_schema(ComparisonDraft,data)
        self.assertEqual(names['$defs']['Choice']['properties']['id']['enum'],['name:0'])
        self.assertEqual(names['properties']['choices']['maxItems'],1)
        self.assertEqual(names['properties']['recommended_ids']['items']['enum'],['name:0'])
        combos=output_schema(NameDraft,data)
        self.assertEqual(combos['$defs']['CombinationDraft']['properties']['id']['enum'],['option:0','option:1','option:2'])


class HanjaFollowupTests(unittest.IsolatedAsyncioTestCase):
    async def test_followup_requeries_original_dictionary_not_just_old_recommendations(self):
        data=calculations()
        # Reproduce an older session that missed every combination.
        data['candidates'][0]['combinations']=[]
        data['candidates'][0]['recommendable']=False
        seen=[]
        async def call(schema,raw,instruction,validator,*args):
            seen.append(raw)
            self.assertTrue(any(h['character']=='率' and h['registry']['status']=='listed'
                                for h in raw['dictionary_lookup']['솔']))
            value=NameAnswer(answer='率은 거느릴 솔로 공식 독음을 확인한 글자이며 이끈다는 뜻을 담아요. 이전 추천 목록에서 빠진 것은 검색 범위의 문제였고, 이솔의 한자 조합으로 뜻을 다시 비교할 수 있어요.')
            self.assertEqual(validator(value),[])
            return value,{'mode':'fresh_model'}
        with patch('api.name_readings.fresh_call',side_effect=call):
            result=await followup_name({'name_calculations':data},'거느릴 솔이 있는데?', 'test','test',None)
        self.assertIn('率',result['answer'])
        self.assertNotIn('dictionary_lookup',data)
        self.assertEqual(len(seen),1)
