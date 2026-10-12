"""Real locality coordinates, shared selectors and legacy clock conventions."""
import unittest
from pydantic import ValidationError
from api.birthplaces import PLACES, CATALOG
from api.server import Profile, chart


class BirthplaceTests(unittest.TestCase):
    def test_catalog_reaches_every_district_and_locality(self):
        places=list(PLACES.values())
        self.assertGreater(len(places),3800)
        for label in ['강릉시','울릉군','신안군','수원시장안구','서귀포시','세종특별자치시']:
            self.assertTrue(any(label in p['label'] for p in places),label)
        for p in places:
            self.assertTrue(122 < p['longitude'] < 134 and 30 < p['latitude'] < 40)
            if p['locality']:
                self.assertTrue(any(q['region']==p['region'] and q['district']==p['district'] and not q['locality'] for q in places),p['label'])
        self.assertEqual({p['region'] for p in places},{r['id'] for r in CATALOG['regions']})

    def test_selected_region_drives_clock_and_report_label(self):
        ids=[p['id'] for p in PLACES.values() if p['label'] in ['울릉군','신안군'] or p['label']=='전남 신안군']
        self.assertEqual(len(ids),2)
        reports=[chart(Profile(birth_date='2004-02-28',birth_time='01:30',city=place))['report'] for place in ids]
        for place,r in zip(ids,reports):
            self.assertEqual(r['input_basis']['longitude'],PLACES[place]['longitude'])
            self.assertIn(PLACES[place]['label'],r['profile']['city'])
            self.assertEqual(r['input_basis']['birthplace_id'],place)
        self.assertNotEqual(reports[0]['input_basis']['corrected_time'],reports[1]['input_basis']['corrected_time'])

    def test_legacy_coordinates_are_preserved_invalid_places_rejected(self):
        for city,lon in [('seoul',126.9784),('busan',129.0756),('jeju',126.5312)]:
            self.assertEqual(chart(Profile(birth_date='2004-05-15',birth_time='10:30',city=city))['report']['input_basis']['longitude'],lon)
        for city in ['','unknown','new-york','kr-0000000000']:
            with self.assertRaises(ValidationError):Profile(city=city)
