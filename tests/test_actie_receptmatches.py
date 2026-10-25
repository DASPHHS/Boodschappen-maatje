"""Bewaar onderscheid tussen titelkandidaten en doorgerekende recepten."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from actie_receptmatches import select_candidates, matched_keys,normalized

class TitelMatchTest(unittest.TestCase):
    def test_roti_kip_en_broccoli_mogelijke_actie(self):
        keys={"kipfilet","broccoli"}
        index=[{"title":"Surinaamse roti met kip en broccoli","source":"Jumbo","url":"https://example.org/recept","cuisine":"Surinaams","category":"Kip"}]
        found=select_candidates(index,keys)
        self.assertEqual(len(found),1)
        self.assertEqual(found[0]["matched_title_terms"],2)
        self.assertEqual(found[0]["verification"],"ALLEEN TITELMATCH — broningrediënten niet gecontroleerd")
        self.assertFalse(found[0]["price_verified"])
        self.assertFalse(found[0]["servings_verified"])

    def test_geen_valse_ingredient_substitutie(self):
        self.assertEqual(matched_keys("Kouseband met knoflook",{"bonen"}),{})
        self.assertEqual(matched_keys("Surinaamse bami",{"pasta"}),{})
        self.assertEqual(matched_keys("Geroosterde zoete aardappel",{"aardappel"}),{})
        self.assertEqual(matched_keys("Gerookte zalm",{"broccoli"}),{})
        self.assertIn("zoete_aardappel",matched_keys("Zoete aardappel bowl",{"zoete_aardappel"}))
        self.assertIn("kip",matched_keys("Kippendijreepjes met gember",{"kipdij"}))

    def test_geen_korting_geen_kandidaat(self):
        self.assertEqual(select_candidates([{"title":"Kipfilet met broccoli"}],set()),[])

    def test_alleen_titels_en_originele_links(self):
        inputs=[
          {"title":"Kip met broccoli","source":"Jumbo","url":"https://jumbo.example/recept","cuisine":"Surinaams"},
          {"title":"Kip met broccoli","source":"Jumbo","url":"https://jumbo.example/recept","cuisine":"Surinaams"},
          {"title":"Kip met paprika","source":"Fout","url":"javascript:alert(1)"},
          {"title":"Recepten: kip","kind":"collection","source":"Collectie"}
        ]
        found=select_candidates(inputs,{"kipfilet","broccoli"})
        self.assertEqual(len(found),1)
        self.assertNotIn("ingredients",found[0])
        self.assertNotIn("instructions",found[0])
        self.assertNotIn("checkout",found[0])

    def test_verschillende_keukens_worden_niet_uitgedrukt(self):
        inputs=[{"title":f"Kipfilet met groente {i}","source":"Bron","cuisine":"Surinaams"} for i in range(40)]
        inputs += [{"title":"Kip in Japanse stijl","source":"Bron","cuisine":"Japans"}]
        found=select_candidates(inputs,{"kipfilet"},limit=80)
        self.assertLessEqual(len([x for x in found if x["cuisine"]=="Surinaams"]),18)
        self.assertIn("Japans",{x["cuisine"] for x in found})

if __name__=="__main__":
    unittest.main()
