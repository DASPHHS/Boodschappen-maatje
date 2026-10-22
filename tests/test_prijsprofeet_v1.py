import sys, unittest
sys.path.insert(0,"src")
from prijsprofeet_v1 import normalize, num

class TestPrijsProfeetV1(unittest.TestCase):
    def test_number(self):
        self.assertEqual(num("2.49"),2.49)
        self.assertIsNone(num(None))
    def test_retailer(self):
        deal={"brand":"Test","savings_percentage":35,
              "representative_product":{"id":123,"name":"Volkoren pasta 500 g",
              "price":1.49,"original_price":2.29,"valid_from":"2026-10-20",
              "valid_until":"2026-10-27","promotion_status":"active"}}
        r=normalize(deal,"jumbo","top_by_percentage")
        self.assertEqual(r["store"],"Jumbo")
        self.assertEqual(r["price"],1.49)
        self.assertEqual(r["promotion_status"],"active")
    def test_historical_excluded(self):
        d={"representative_product":{"name":"Product","price":1,"promotion_status":"historical"}}
        self.assertIsNone(normalize(d,"lidl","top_by_amount"))

if __name__=="__main__":unittest.main()
