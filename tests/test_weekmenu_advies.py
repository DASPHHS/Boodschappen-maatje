"""Controle op complete vergelijkbare weekmenuprijzen, gedeelde verpakkingen en acties."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from weekmenu_advies import _cost_of_lines,build_weekmenu,matching_recipes

def line(key,required,package_size=500,price=2,action=None):
    packs=__import__("math").ceil(required/package_size)
    return {"key":key,"label":key,"product":key+" 500 g",
            "required":required,"unit":"g","package":str(package_size)+" g",
            "package_size":package_size,"packages":packs,
            "cash_price":price*packs,"regular_cash":3*packs,
            "sale":bool(action),"action":action,"used_price":required/package_size*price}

def recipe(title,cat,prices,store,idx):
    # 4 diverse ingrediënten, 4 porties, zelfde recept per retailer.
    ings=[line("groente",300),line("eiwit",350),
          line("groente2",250),line("bijgerecht",100)]
    for l in ings:
        l["cash_price"]=round(l["cash_price"]*prices[store]/2,2)
        l["regular_cash"]=round(l["regular_cash"]*prices[store]/2,2)
    return {"title":title,"id":str(idx),"category":cat,"minutes":35,
      "meal_type":"Avondeten","cuisine":"Internationaal","offer_driven":False,
      "complete":True,"ingredients":ings,
      "checkout":sum(l["cash_price"] for l in ings),
      "nutrition":{"protein_g_per_serving_estimate":36,
                   "vegetable_g_per_serving_estimate":260}}

class WeekmenuAdviesTests(unittest.TestCase):
    def test_voorkom_dubbel_betalen_voor_dezelfde_verpakking(self):
        x=line("broccoli",300,500,2)
        merged=_cost_of_lines([x,x])
        self.assertEqual(merged["checkout"],4.0)
        self.assertEqual(merged["products"][0]["packages"],2)
        two=_cost_of_lines([line("spinazie",100,500,2)]*2)
        self.assertEqual(two["checkout"],2.0)
        self.assertEqual(two["products"][0]["packages"],1)

    def test_bundel_alleen_als_hoeveelheid_voordeel_geeft(self):
        bundle={"multi_buy_quantity":2,"multi_buy_price":3.0,
                "price":2.0,"promotion_type":"2 voor 3","url":"https://example.org/p"}
        rows=[line("broccoli",260,500,2,bundle),
              line("broccoli",300,500,2,bundle)]
        basket=_cost_of_lines(rows)
        self.assertEqual(basket["checkout"],3.0)
        self.assertEqual(basket["products"][0]["packages"],2)
        # Voor één pak is de expliciet getoonde bundelprijs niet goedkoper
        # dan de reguliere prijs per stuk: geen fictief voordeel.
        one=_cost_of_lines([line("broccoli",220,500,2,bundle)])
        self.assertEqual(one["checkout"],3.0)
        self.assertEqual(one["products"][0]["packages"],1)

    def test_vergelijk_dezelfde_recepten_en_niet_drie_verschillende_lijstjes(self):
        names=[("Kip met groenten","Kip"),("Zalm uit oven","Vis"),
               ("Vegetarische tofu","Vegetarisch")]
        prices={"ah":2.8,"jumbo":2.2,"lidl":1.5}
        recipes={store:[recipe(t,c,prices,store,i) for i,(t,c) in enumerate(names)]
                 for store in prices}
        out=build_weekmenu(recipes)
        self.assertEqual(out["status"],"indicative_online_comparison")
        self.assertEqual(out["recipe_count"],3)
        self.assertEqual(out["portion_count"],12)
        self.assertEqual(out["cheapest_store"],"lidl")
        self.assertLess(out["stores"]["lidl"]["checkout"],
                        out["stores"]["ah"]["checkout"])
        self.assertTrue(out["same_recipes_all_stores"])
        self.assertEqual(len({r["category"] for r in out["meals"]}),3)

    def test_onvolledige_of_andere_ingredienten_blokkeren_vergelijking(self):
        names=[("Kip met groenten","Kip"),("Zalm uit oven","Vis")]
        prices={"ah":2,"jumbo":2,"lidl":2}
        recipes={s:[recipe(t,c,prices,s,i) for i,(t,c) in enumerate(names)]
                 for s in prices}
        recipes["lidl"][0]["ingredients"][0]["required"]=400
        out=build_weekmenu(recipes)
        self.assertEqual(out["status"],"insufficient_common_recipes")
        recipes["lidl"]=[]
        self.assertEqual(build_weekmenu(recipes)["status"],"incomplete_sources")

if __name__=="__main__":unittest.main()
