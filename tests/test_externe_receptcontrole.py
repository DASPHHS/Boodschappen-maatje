"""Externe recepten tellen pas mee wanneer echte broningrediënten overeenkomen."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from recepten_ontdekker import ingredient_confirmed_candidate,verify_meal,ingredient_key

def source():
    return {"idMeal":"12345","strMeal":"Chicken Broccoli Curry",
            "strArea":"Indian","strSource":"https://www.themealdb.com/meal/12345",
            "strInstructions":"Cook until chicken is fully done.",
            "strIngredient1":"Chicken thighs","strMeasure1":"500g",
            "strIngredient2":"Broccoli","strMeasure2":"400g",
            "strIngredient3":"Rice","strMeasure3":"1 cup",
            "strIngredient4":"Onion","strMeasure4":"1 medium",
            "strIngredient5":"Curry paste","strMeasure5":"2 tbsp"}

class ExterneBroncontroleTests(unittest.TestCase):
    def test_ingredienten_gecontroleerd_maarniet_als_kassaprijs(self):
        meal=source()
        found=ingredient_confirmed_candidate(meal,{"kipdij","broccoli"})
        self.assertEqual(found["match_terms"],["broccoli","kipdij"])
        self.assertEqual(found["verification_level"],"ingredient_names_only")
        self.assertEqual(found["source_ingredient_names"]["kipdij"],["Chicken thighs"])
        self.assertFalse(found["price_verified"])
        self.assertFalse(found["servings_verified"])
        self.assertEqual(found["cuisine"],"Indiaas")
        self.assertIsNone(verify_meal(meal,{"kipdij","broccoli"}),
                          "Zonder controleerbare originele porties geen geprijsd recept")

    def test_broningredienten_mogen_geen_ander_product_worden(self):
        for ingredient in ("Rice Noodles","Rice Paper","Egg Noodles",
                           "Tomato Paste","Tomato Sauce","Onion Powder",
                           "Cheese Sauce","Mushroom Soup","Salmon Roe"):
            with self.subTest(ingredient=ingredient):
                self.assertIsNone(ingredient_key(ingredient))
        self.assertEqual(ingredient_key("Rice"),"rijst")
        self.assertEqual(ingredient_key("Brown Rice"),"rijst")
        self.assertEqual(ingredient_key("Eggs"),"eieren")
        self.assertEqual(ingredient_key("Chicken Thighs"),"kipdij")
        self.assertEqual(ingredient_key("Cherry Tomatoes"),"tomaten")

    def test_twee_actieproducten_vereist(self):
        self.assertIsNone(ingredient_confirmed_candidate(source(),{"kipdij"}))
        self.assertIsNone(ingredient_confirmed_candidate(source(),set()))

    def test_bron_en_instructie_zijn_verplicht(self):
        broken=source();broken["strInstructions"]=""
        self.assertIsNone(ingredient_confirmed_candidate(broken,{"kipdij","broccoli"}))
        broken=source();broken["strSource"]="javascript:bad"
        self.assertIsNone(ingredient_confirmed_candidate(broken,{"kipdij","broccoli"}))

if __name__=="__main__":unittest.main()
