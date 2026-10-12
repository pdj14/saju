import unittest
from api.server import Profile,ReadRequest,facts_for,NOTES
from api.model_readings import raw_stars,payload,STAR_THEMES,issues
from tests.test_model_readings import model_batch


class StarThemeTests(unittest.TestCase):
    def test_themes_combine_real_planets_with_service_specific_evidence(self):
        f=facts_for(ReadRequest(service='stars',profile=Profile(name='가람',birth_date='2004-05-15',birth_time='10:30')),fresh=True)
        data=raw_stars(f['astrology'],f['chart']['report']['profile'])
        self.assertEqual(list(STAR_THEMES),['overview','work','relationships','shadow'])
        for topic,question in STAR_THEMES.items():
            user=payload('stars',data,NOTES,[(topic,question)])
            required=user['SECTION_REQUESTS'][0]['required_evidence_ids']
            self.assertTrue(required)
            batch=model_batch(data,[topic]);batch.chapters[0].evidence_ids=required
            self.assertEqual(issues(batch,data,[topic],'stars'),[])
            batch.chapters[0].evidence_ids=['astrology_scope']
            self.assertIn('종합',' '.join(issues(batch,data,[topic],'stars')))

    def test_unknown_time_does_not_create_moon_ascendant_or_houses(self):
        f=facts_for(ReadRequest(service='stars',profile=Profile(birth_date='2004-05-15')),fresh=True)
        data=raw_stars(f['astrology'],f['chart']['report']['profile'])
        user=payload('stars',data,NOTES,list(STAR_THEMES.items()))
        self.assertFalse(data['hour_known']);self.assertFalse(data['aspects'])
        self.assertNotIn('planet:Moon',user['SECTION_REQUESTS'][0]['required_evidence_ids'])
        self.assertNotIn('houses',user['CALCULATIONS']);self.assertNotIn('ascendant',user['CALCULATIONS'])
