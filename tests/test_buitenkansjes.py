import datetime as dt
import sys
import unittest
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from buitenkansjes import compare,normalize,render,pull

DAY=dt.date(2026,10,23)

def offer(retailer,price,original,ean="000123",name="Volle melk 1 liter",start="2026-10-21",end="2026-10-27",quantity="1 liter"):
    return {"product_id":retailer+ean,"base_product_id":retailer+ean,
        "name":name,"retailer":retailer,"price":price,"original_price":original,
        "ean":ean,"quantity":quantity,"valid_from":start,"valid_until":end,
        "is_promotional":True,"promotion_status":"active"}

class TestVerifiedDeals(unittest.TestCase):
    def test_exact_competitor_confirms(self):
        r=compare([offer("jumbo",0.79,1.49),offer("albert_heijn",1.19,1.49)],DAY)
        self.assertEqual(len(r["confirmed"]),1)
        self.assertEqual(r["confirmed"][0]["retailer"],"jumbo")
    def test_large_discount_not_enough(self):
        r=compare([offer("jumbo",5,12,name="Wasmiddel 2 liter")],DAY)
        self.assertEqual(len(r["confirmed"]),0)
        self.assertEqual(len(r["candidates"]),1)
    def test_other_store_cheaper(self):
        r=compare([offer("jumbo",1.29,2.50),offer("albert_heijn",0.99,1.20)],DAY)
        self.assertEqual(len(r["confirmed"]),0)
    def test_future_only_future(self):
        r=compare([offer("lidl",0.79,1.49,start="2026-10-26",end="2026-11-01")],DAY)
        self.assertEqual(len(r["confirmed"]),0)
        self.assertEqual(len(r["next_week"]),1)
    def test_old_offer_excluded(self):
        self.assertIsNone(normalize(offer("jumbo",0.79,1.49,end="2026-10-20"),DAY))
    @patch("buitenkansjes.time.sleep")
    @patch("buitenkansjes.api")
    def test_api_met_meer_dan_5000_aanbiedingen_is_volledig(self,api,sleep):
        def response(params):
            page=params["page"]
            return {"products":[{"name":str(page)}]*100 if page<=57 else [],
                    "total":5700}
        api.side_effect=response
        rows,meta=pull("albert_heijn")
        self.assertTrue(meta["complete"])
        self.assertEqual(meta["received"],5700)
        self.assertEqual(len(rows),5700)
        self.assertEqual(api.call_count,57)

    def test_html_safe(self):
        r=compare([offer("jumbo",5,12,name="Wasmiddel <extra> 2 liter")],DAY)
        self.assertIn("&lt;extra&gt;",render(r))

if __name__=="__main__": unittest.main()
