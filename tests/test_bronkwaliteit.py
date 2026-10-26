import sys,unittest
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from bronkwaliteit import analyse
NOW=datetime(2026,10,27,12,tzinfo=timezone.utc)
class CoverageTests(unittest.TestCase):
 def test_lidl_complete_api_not_complete_week(self):
  a=analyse({"updated_at":NOW.isoformat(),"shelf_products":{"lidl":5369},"promotion_mentions":{"lidl":28}},
      {"updated_at":NOW.isoformat(),"coverage":{"lidl":{"complete":True,"received":37,"total":37}},
       "stores":{"lidl":[{"name":"x"}]*37}},now=NOW)
  self.assertTrue(a["retailers"]["lidl"]["api_pagination_complete"])
  self.assertFalse(a["retailers"]["lidl"]["retailer_coverage_complete"])
  self.assertIn("weinig_acties_voor_weekdekking",a["retailers"]["lidl"]["issues"])
 def test_other_shops_not_verified_without_data(self):
  a=analyse({},now=NOW)
  self.assertEqual(a["retailers"]["action"]["quality"],"needs_attention")
 def test_stale_sources_reported(self):
  a=analyse({"updated_at":"2026-10-26T10:00:00+00:00"},now=NOW)
  self.assertIn("hoofdaanvoer_verouderd",a["retailers"]["ah"]["issues"])
if __name__=="__main__":unittest.main()
