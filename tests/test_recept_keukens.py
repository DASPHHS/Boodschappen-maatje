"""Regressies voor echte keukenfilters en veilige Nederlandstalige recepten."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from recept_keukens import infer_cuisine,dutch_title,SPECIFIC_CUISINES
from actie_receptmatches import select_candidates

class WereldkeukenEnTaalTests(unittest.TestCase):
    def test_specifieke_keukens_met_echte_herkomst(self):
        cases=[
          ("Surinaamse roti met kip",None,"Surinaams"),
          ("Roti met kousenband", "Surinaams", "Surinaams"),
          ("Saoto soep","Overig / wereldwijd","Surinaams"),
          ("Bibimbap met groenten",None,"Koreaans"),
          ("Kip teriyaki","Aziatisch","Japans"),
          ("Pad thai met tofu",None,"Thais"),
          ("Vegetarische gado-gado",None,"Indonesisch"),
          ("Tajine met kip","Overig","Marokkaans"),
          ("Mexicaanse taco's",None,"Mexicaans"),
          ("Costa Ricaanse gallo pinto",None,"Costa Ricaans"),
          ("Pasta alla carbonara",None,"Italiaans"),
          ("Stamppot boerenkool","Overig","Nederlands"),
          ("Moksi alesi met rijst",None,"Surinaams"),
          ("Biryani met rijst",None,"Indiaas"),
          ("Caribische jerk chicken",None,"Caribisch"),
          ("Fire Roasted Tomato Beef with Rice","Overig / wereldwijd","Internationaal"),
        ]
        for title,label,expected in cases:
            with self.subTest(title=title):
                self.assertEqual(infer_cuisine(title,label),expected)

    def test_onzekere_culturele_herkomst_niet_verzinnen(self):
        for title in ("Chicken with Orange, Spinach and Cherry Tomatoes",
                      "Chicken Bowls with Rice and Lentils",
                      "Kip met rijst en broccoli","Pittige gehaktroerbak met volkorenpasta"):
            self.assertEqual(infer_cuisine(title),"Internationaal",title)
        self.assertEqual(infer_cuisine("Roti", "Surinaams"),"Surinaams")
        self.assertEqual(infer_cuisine("Roti", None),"Internationaal")
        self.assertGreaterEqual(len(SPECIFIC_CUISINES),20)

    def test_screenshot_titels_correct_vertaald(self):
        translations={
          "Chicken Bowls with Rice and Lentils":"Kipbowls met rijst en linzen",
          "Chicken Soup with Rice and Potatoes":"Kippensoep met rijst en aardappelen",
          "Chicken with Orange, Spinach and Cherry Tomatoes":
            "Kip met sinaasappel, spinazie en cherrytomaten",
          "Chili Garlic Chicken with Rice and Beans":"Chili-knoflookkip met rijst en bonen",
          "Lentil, Potato, and Tomato Curry":"Curry met linzen, aardappel en tomaat",
          "Spinach Mushroom Pesto Spaghetti":"Spaghetti met spinazie, champignons en pesto",
          "Chicken Bacon Broccoli Alfredo Spaghetti":
            "Spaghetti Alfredo met kip, spek en broccoli"
        }
        for title,dutch in translations.items():
            with self.subTest(title=title):
                self.assertEqual(dutch_title(title),(dutch,True))

    def test_onbekende_engelse_woorden_worden_niet_stilzwijgend_vertaald(self):
        title="Chicken with Mysterious Hokkien Ingredient"
        self.assertEqual(dutch_title(title),(title,False))
        self.assertEqual(dutch_title("Surinaamse roti met kousenband"),
                         ("Surinaamse roti met kousenband",False))

    def test_gezonde_titels_voor_voorlopige_sortering_geen_gezond_claim(self):
        titles=[
          "Chicken Bacon Broccoli Alfredo Spaghetti",
          "Chicken with Orange, Spinach and Cherry Tomatoes",
          "Chicken Soup with Rice and Potatoes",
          "Chicken Bowls with Rice and Lentils",
        ]
        items=[{"title":t,"source":"Wikibooks","url":"https://example.com/"+str(i)}
               for i,t in enumerate(titles)]
        found=select_candidates(items,{"kipfilet","spinazie","tomaten","broccoli","pasta","rijst","linzen","aardappel"})
        labels={r["title"]:r for r in found}
        self.assertEqual(labels[titles[0]]["health_priority"],"lage prioriteit")
        self.assertEqual(labels[titles[1]]["health_priority"],"kansrijk voor controle")
        self.assertEqual(labels[titles[2]]["health_priority"],"nader beoordelen")
        self.assertEqual(labels[titles[3]]["health_priority"],"kansrijk voor controle")
        self.assertEqual(labels[titles[1]]["title_nl"],
                          "Kip met sinaasappel, spinazie en cherrytomaten")
        self.assertEqual(labels[titles[1]]["cuisine"],"Internationaal")
        self.assertFalse(labels[titles[1]]["price_verified"])
        self.assertLess(found.index(labels[titles[1]]),found.index(labels[titles[0]]))

if __name__=="__main__":unittest.main()
