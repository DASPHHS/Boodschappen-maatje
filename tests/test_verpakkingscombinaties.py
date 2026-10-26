import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from verpakkingscombinaties import mixed_pack_option

def item(name,size,price,sale=False):
    return {
      "product":name,"package":str(size)+" g","package_size":size,
      "packages":1,"cash_price":price,"regular_cash":price+(1 if sale else 0),
      "required":800,"unit":"g","label":"kip","source":"Test","url":"https://example.org",
      "sale":sale,"action":{"name":name,"price":price,"url":"https://example.org"} if sale else None,
      "frozen":False,"flavoured_dairy":False,
    }

class MixedPackageTests(unittest.TestCase):
    def test_500_plus_300(self):
        best=mixed_pack_option("kipfilet",800,"g",[
            item("actie 500",500,3.0,True),item("regulier 300",300,2.0)])
        self.assertEqual(best["cash_price"],5.0)
        self.assertEqual(best["required"],800)
        self.assertEqual(sum(c["package_size"]*c["packages"] for c in best["components"]),800)
        self.assertTrue(best["sale"])
    def test_750_instead_of_800(self):
        best=mixed_pack_option("kipfilet",800,"g",[
            item("actie 750",750,5.99,True),item("regulier 300",300,4.35)])
        # Mengcombinaties mogen duurder zijn; de hoofdfunctie vergelijkt met 750 g.
        self.assertGreater(best["cash_price"],5.99)
    def test_bundles_are_not_split(self):
        bundled=item("2 voor 5",500,2.5,True)
        bundled["action"]["multi_buy_quantity"]=2
        self.assertIsNone(mixed_pack_option("kipfilet",800,"g",[bundled,item("300",300,2.0)]))
    def test_exact_quantities_for_staples(self):
        best=mixed_pack_option("rijst",800,"g",[item("rijst 500",500,2.0),item("rijst 250",250,1.0)])
        self.assertIsNotNone(best)
        self.assertGreaterEqual(best["package_size"],800)
    def test_empty(self):
        self.assertIsNone(mixed_pack_option("kipfilet",800,"g",[]))

if __name__=="__main__":unittest.main()
