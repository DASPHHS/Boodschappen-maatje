import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from lidl_officiele_acties import supplement

class LidlSourceTests(unittest.TestCase):
    def test_week_44_and_loyalty(self):
        offers={"lidl":[]}; future={"lidl":[]}
        supplement(offers,future,"2026-10-26")
        names={x["name"]:x for x in offers["lidl"]}
        self.assertIn("SALADINETTES Aardappelschijfjes",names)
        self.assertTrue(names["SALADINETTES Aardappelschijfjes"]["is_loyalty"])
        self.assertIn("CHEF SELECT Aardappelgratin",names)
        self.assertFalse(names["CHEF SELECT Aardappelgratin"]["is_loyalty"])
        self.assertIn("Kogelbiefstuk",{x["name"] for x in future["lidl"]})
        supplement(offers,future,"2026-10-26")
        self.assertEqual(len(offers["lidl"]),len(names))

    def test_expiry(self):
        offers={"lidl":[]}; future={"lidl":[]}
        supplement(offers,future,"2026-12-01")
        self.assertEqual(offers["lidl"],[])
        self.assertEqual(future["lidl"],[])

if __name__=="__main__":
    unittest.main()
