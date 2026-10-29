import datetime as dt
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import sync_retailer_catalog as m

DAY=dt.date(2026,10,29)
COMMIT=[{"sha":"abc123","commit":{"committer":{"date":"2026-10-29T06:06:06Z"}}}]

class CatalogTest(unittest.TestCase):
    def test_official_links_not_guessed_for_lidl(self):
        a=m.normalize({"n":"Houdbare volle melk","p":.98,"s":"1 L","l":"128759"},"lidl")
        b=m.normalize({"n":"AH Houdbare volle melk","p":1.29,"s":"1 l","l":"wi450535/ah-houdbare-volle-melk"},"ah")
        c=m.normalize({"n":"Jumbo Houdbare Volle Melk 1 L","p":.99,"s":"1 L","l":"jumbo-houdbare-volle-melk-1-l-49608STK"},"jumbo")
        self.assertEqual(a[3],None)
        self.assertEqual(b[3],"https://www.ah.nl/producten/product/wi450535/ah-houdbare-volle-melk")
        self.assertEqual(c[3],"https://www.jumbo.com/producten/jumbo-houdbare-volle-melk-1-l-49608STK")

    def test_invalid_prices_and_links_refused(self):
        self.assertIsNone(m.normalize({"n":"bad","p":0,"s":"1 l","l":"12"},"lidl"))
        self.assertIsNone(m.normalize({"n":"bad","p":-20,"s":"1 l","l":"12"},"lidl"))
        self.assertIsNone(m.normalize({"n":"bad","p":1,"s":"1 l","l":"https://evil.example"},"lidl"))
        self.assertIsNone(m.normalize({"n":"bad","p":1,"s":"1 l","l":"https://evil.example"},"jumbo"))

    def test_freshness_and_refusal_on_incomplete_data(self):
        item=lambda store,k:{"n":f"Product {k}","p":1.02,"s":"1 kg",
                             "l":("wi" + str(k) + "/test" if store=="ah" else
                                  f"product-{k}-123456STK" if store=="jumbo" else str(k+100))}
        data=[{"n":store,"d":[item(store,k) for k in range(1001)]} for store in m.STORES]
        result=m.build(data,COMMIT,DAY)
        self.assertEqual(len(result["stores"]["lidl"]),1001)
        self.assertEqual(result["source_date"],"2026-10-29")
        with self.assertRaises(ValueError): m.build(data,COMMIT,dt.date(2026,11,4))
        with self.assertRaises(ValueError): m.build(data[:2],COMMIT,DAY)

if __name__ == "__main__":unittest.main()
