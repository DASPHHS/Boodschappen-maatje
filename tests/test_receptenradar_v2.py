"""Regressietests voor kassaprijzen en voorzichtige productmatching."""
import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from receptenradar_catalog import RECIPES, RECIPE_METHODS, validate_dish_ingredients
from receptkwaliteit import pantry_for_recipe, cooking_instructions, dish_quality_issues
from actie_maaltijden import DISH_TEMPLATES
from receptenradar_v2 import fresh_spinach_required,measure,measure_offer,offer_size_label,verified_discount,verified_discount_percentage,match_ingredient,total_for,promo_for,offer_price,ingredient_price,nutrition_profile,product_context,audit_promotions,alternative_offers,audit_recipe_quality,AUDIT_GROUPS

class PrijsTest(unittest.TestCase):
    def test_kcal_per_portie_en_totaal(self):
        recipe=nutrition_profile([
            ("kipfilet",800,"g"),("broccoli",1000,"g"),
            ("aardappel",400,"g")])
        # 880 kcal kip + 340 kcal broccoli + 320 kcal aardappelen.
        self.assertEqual(recipe["kcal_total_estimate"],1540)
        self.assertEqual(recipe["kcal_per_serving_estimate"],385)
        self.assertEqual(recipe["kcal_unknown"],[])

    def test_geen_schijnzekerheid_bij_ontbrekende_voedingswaarde(self):
        recipe=nutrition_profile([("kipfilet",800,"g"),("onbekend",100,"g")])
        self.assertIsNone(recipe["kcal_per_serving_estimate"])
        self.assertIn("onbekend",recipe["kcal_unknown"])

    def test_dertig_gram_eiwit_per_portie(self):
        # 650g kipfilet + 800g broccoli voor vier porties.
        high=nutrition_profile([("kipfilet",650,"g"),("broccoli",800,"g")])
        self.assertGreaterEqual(high["protein_g_per_serving_estimate"],30)
        self.assertTrue(high["protein_source"])
        low=nutrition_profile([("tofu",450,"g"),("broccoli",600,"g")])
        self.assertLess(low["protein_g_per_serving_estimate"],30)
        self.assertFalse(low["protein_source"])

    def test_meer_groenten_in_plaats_van_zetmeel(self):
        sufficient=nutrition_profile([("kipfilet",650,"g"),
            ("spruiten",1100,"g"),("aardappel",400,"g")])
        self.assertEqual(sufficient["vegetable_g_per_serving_estimate"],275)
        self.assertTrue(sufficient["lower_carb"])
        self.assertTrue(sufficient["priority"])
        insufficient=nutrition_profile([("kipfilet",650,"g"),
            ("spruiten",800,"g"),("aardappel",900,"g")])
        self.assertFalse(insufficient["vegetable_forward"])
        self.assertFalse(insufficient["lower_carb"])

    def test_ontbijt_zonder_groente_toch_passend(self):
        p=nutrition_profile([
          ("kwark",1400,"g"),("havermout",160,"g"),
          ("banaan",480,"g"),("blauwe_bessen",300,"g")],meal_type="Ontbijt")
        self.assertTrue(p["priority"])
        self.assertTrue(p["protein_source"])
        self.assertGreater(p["kcal_per_serving_estimate"],300)

    def test_lunch_met_groenten(self):
        p=nutrition_profile([("kipfilet",800,"g"),("broccoli",800,"g"),
                             ("wortel",300,"g"),("rijst",140,"g")],meal_type="Lunch")
        self.assertTrue(p["priority"])
        self.assertGreaterEqual(p["protein_g_per_serving_estimate"],30)

    def test_jumbo_magere_milde_kwark_herkend(self):
        self.assertTrue(match_ingredient(
            {"norm":"campina magere milde kwark naturel voordeelpak 1 kg"},"kwark"))
        self.assertTrue(match_ingredient(
            {"norm":"jumbo nederlandse aardbeien 400 g"},"aardbeien"))
        self.assertFalse(match_ingredient(
            {"norm":"optimel kwark met yoghurt aardbei 500 g"},"kwark"))

    def test_vaste_aanbieding_voor_prijs(self):
        promo={"price":2.49,"original_price":3.49,
               "promotion_type":"voor € 2,49"}
        self.assertEqual(total_for(2,3.49,promo),(4.98,2))
        unverified_bundle={"price":2.99,"original_price":3.49,
                           "promotion_type":"2 voor 2,99"}
        self.assertEqual(total_for(2,3.49,unverified_bundle),(6.98,2))

    def test_gezonde_varianten_en_diepvries(self):
        self.assertTrue(match_ingredient(
            {"norm":"optimel magere kwark vanille zonder toegevoegde suiker 500 g"},"kwark"))
        self.assertTrue(match_ingredient(
            {"norm":"skyr aardbei 450 g"},"kwark"))
        self.assertTrue(match_ingredient(
            {"norm":"diepvries blauwe bessen 750 g"},"blauwe_bessen"))
        self.assertTrue(match_ingredient(
            {"norm":"diepvries broccoli roosjes 1000 g"},"broccoli"))
        self.assertTrue(match_ingredient(
            {"norm":"diepvries zalmfilet 500 g"},"zalm"))
        self.assertFalse(match_ingredient(
            {"norm":"aardbeien kwark dessert mousse"},"kwark"))
        self.assertFalse(match_ingredient(
            {"norm":"blauwe bessen jam"},"blauwe_bessen"))
        ctx=product_context({"name":"Diepvries blauwe bessen 750 g"},"blauwe_bessen")
        self.assertTrue(ctx["frozen"])
        flav=product_context({"name":"Skyr aardbei 450 g"},"kwark")
        self.assertTrue(flav["nutrition_unverified"])

    def test_audit_herkent_ontbrekende_receptmatch(self):
        offer={"name":"Diepvries blauwe bessen 750 g","norm":"diepvries blauwe bessen 750 g",
               "quantity":750,"unit":"g","price":3.0,"original_price":5.0,
               "promotion_type":"","is_loyalty":False,"url":"https://example.com"}
        offers={"ah":[offer],"jumbo":[],"lidl":[]}
        empty={"ah":[],"jumbo":[],"lidl":[]}
        report=audit_promotions(offers,empty)
        group=report["ah"]["groups"]["Fruit"]
        self.assertEqual(group["recognized_offers"],1)
        self.assertEqual(group["unlinked_offers"],1)
        matched={"ah":[{"ingredients":[{"sale":True,
           "action":{"name":"Diepvries blauwe bessen 750 g"}}]}],"jumbo":[],"lidl":[]}
        report=audit_promotions(offers,matched)
        self.assertEqual(report["ah"]["groups"]["Fruit"]["linked_offers"],1)

    def test_audit_meldt_onbekende_verpakking(self):
        offer={"name":"Diepvries spinazie aanbieding",
               "norm":"diepvries spinazie aanbieding","quantity":None,
               "unit":None,"price":1.0,"original_price":2.0,
               "promotion_type":"","is_loyalty":False,"url":""}
        report=audit_promotions({"ah":[offer],"jumbo":[],"lidl":[]},
                                {"ah":[],"jumbo":[],"lidl":[]})
        self.assertEqual(report["ah"]["unlinked"][0]["reason"],"Verpakkingsmaat onbekend")

    def test_echt_actiealternatief_naast_goedkopere_schapprijs(self):
        regular={"product":"Jumbo huismerk kwark","cash_price":3.0,"sale":False}
        offer={"name":"Campina Magere Milde Kwark Naturel 1 kg",
               "norm":"campina magere milde kwark naturel 1 kg",
               "quantity":1000,"unit":"g","size_label":"1 kg","price":2.49,
               "original_price":3.49,"multi_buy_quantity":None,
               "multi_buy_price":None,"promotion_type":"vaste actieprijs",
               "url":"https://www.jumbo.com/aanbiedingen/"}
        alternative=alternative_offers("kwark",1400,"g",[offer],regular)
        self.assertEqual(len(alternative),1)
        self.assertEqual(alternative[0]["cash_price"],4.98)
        self.assertTrue(alternative[0]["more_expensive_than_selected"])

    def test_rookworst_klassieker_en_gezonder_alternatief(self):
        klassiek=[r for r in RECIPES if r[0]=="Boerenkoolstamppot met rookworst (af en toe)"]
        gezonder=[r for r in RECIPES if r[0]=="Boerenkoolstamppot met kruidige kip (lichter alternatief)"]
        self.assertEqual(len(klassiek),1)
        self.assertEqual(len(gezonder),1)
        self.assertEqual({x[0] for x in klassiek[0][3]},
                         {"boerenkool","aardappel","rookworst","ui"})
        self.assertTrue(match_ingredient({"norm":"ah gelderse rookworst 250 g"},"rookworst"))
        self.assertFalse(match_ingredient({"norm":"vegetarische rookworst 200 g"},"rookworst"))
        self.assertFalse(match_ingredient({"norm":"rookworstsaus 300 g"},"rookworst"))
        klassiek_nutrition=nutrition_profile(klassiek[0][3])
        beter_nutrition=nutrition_profile(gezonder[0][3])
        self.assertGreaterEqual(klassiek_nutrition["vegetable_g_per_serving_estimate"],250)
        self.assertTrue(klassiek_nutrition["processed_meat"])
        self.assertFalse(klassiek_nutrition["priority"])
        self.assertTrue(beter_nutrition["priority"])
        self.assertGreaterEqual(beter_nutrition["protein_g_per_serving_estimate"],30)

    def test_alle_productgroepen_zijn_in_de_controle(self):
        from receptenradar_catalog import ING
        covered={key for group in AUDIT_GROUPS.values() for key in group}
        self.assertEqual(set(ING),covered)
        for key in ("rookworst","boerenkool","kwark","aardbeien",
                    "zalm","broccoli","wraps","rijst","tofu"):
            self.assertIn(key,covered)

    def test_controle_per_eetmoment_zonder_onterechte_groente_eis_bij_ontbijt(self):
        basic={"complete":True,"sale_count":0,"other_offer_count":0,
               "offer_driven":False,"ingredients":[],"instructions":""}
        breakfast={**basic,"title":"Kwark met fruit","meal_type":"Ontbijt",
                   "nutrition":{"protein_g_per_serving_estimate":36,
                                "vegetable_g_per_serving_estimate":0}}
        dinner={**basic,"title":"Te kleine groenteportie","meal_type":"Avondeten",
                 "nutrition":{"protein_g_per_serving_estimate":36,
                              "vegetable_g_per_serving_estimate":150}}
        data=audit_recipe_quality({"jumbo":[breakfast,dinner]})["jumbo"]
        self.assertEqual(data["meals"]["Ontbijt"]["recipes"],1)
        self.assertEqual(data["meals"]["Avondeten"]["recipes"],1)
        self.assertEqual(data["review_needed"],1)
        self.assertEqual(data["examples"][0]["title"],dinner["title"])

    def test_audit_meldt_ontbrekend_ingrediënt_in_recepten(self):
        o={"name":"AH rookworst 250 g","norm":"ah rookworst 250 g",
           "quantity":250,"unit":"g","price":2.5,"original_price":3,
           "promotion_type":"","is_loyalty":False}
        report=audit_promotions({"ah":[o],"jumbo":[],"lidl":[]},
                                {"ah":[],"jumbo":[],"lidl":[]})
        self.assertEqual(report["ah"]["unlinked"][0]["reason"],
                         "Ingrediënt ontbreekt in beschikbare recepten")

    def test_smaakmakers_worden_concreet_en_afzonderlijk_benoemd(self):
        title="Kip teriyaki met wokgroenten"
        ings=[("kipfilet",800,"g"),("wok",1000,"g"),("rijst",140,"g")]
        pantry=pantry_for_recipe(title,ings)
        self.assertTrue(any("olijfolie" in x for x in pantry))
        self.assertTrue(any("sojasaus" in x for x in pantry))
        self.assertTrue(any("gember" in x for x in pantry))
        self.assertFalse(any(key in {"olijfolie","sojasaus","gemberpoeder"} for key,_,_ in ings))
        method=cooking_instructions(title,ings)
        self.assertGreater(len(method),100)

    def test_alle_recepten_hebben_bereiding_en_correcte_gerechtnaam(self):
        for title,category,minutes,ings in RECIPES:
            with self.subTest(title=title):
                self.assertEqual(dish_quality_issues(title,category,ings),[])
                method=cooking_instructions(title,ings,RECIPE_METHODS.get(title,""))
                self.assertGreater(len(method),75)
                pantry=pantry_for_recipe(title,ings,method)
                self.assertIsInstance(pantry,list)
                if not title.startswith("Ontbijt:"):
                    self.assertTrue(any("olijfolie" in x for x in pantry))

    def test_ook_actierecepten_hebben_consistente_gerechtnaam_en_bereiding(self):
        for protein,veg,side,veg2,title,method in DISH_TEMPLATES:
            with self.subTest(title=title):
                ings=[(protein,800,"g"),(veg,800,"g")]
                if side:ings.append((side,200,"g"))
                if veg2:ings.append((veg2,200,"g"))
                self.assertEqual(dish_quality_issues(title,"Kip" if protein.startswith("kip") else "Vlees",ings),[])
                self.assertGreater(len(cooking_instructions(title,ings,method)),30)

    def test_diepvries_mag_behalve_bij_rauwe_spinazie(self):
        self.assertTrue(fresh_spinach_required("Lunch: zalm-spinaziewrap", "spinazie"))
        self.assertFalse(fresh_spinach_required("Kikkererwtencurry met spinazie", "spinazie"))
        base={"unit":"g","quantity":500,"size_label":"500 g",
              "url":"https://www.ah.nl"}
        shelves=[dict(base,name="AH diepvries spinazie",norm="ah diepvries spinazie",price=0.79),
                 dict(base,name="AH verse spinazie",norm="ah verse spinazie",price=1.99)]
        cheapest=ingredient_price("spinazie",500,"g",shelves,[])
        for_raw=ingredient_price("spinazie",500,"g",shelves,[],fresh_only=True)
        self.assertTrue(cheapest["frozen"])
        self.assertFalse(for_raw["frozen"])
        self.assertEqual(for_raw["cash_price"],1.99)

    def test_echt_goedkoopste_product_wint_van_duurdere_aanbieding(self):
        shelf=[{"name":"AH Broccoli 500 g","norm":"ah broccoli 500 g",
                "unit":"g","quantity":500,"price":1.0,
                "size_label":"500 g","url":"https://www.ah.nl"}]
        offer=[{"name":"Duurdere broccoli","norm":"broccoli","unit":"g",
                "quantity":500,"price":1.05,"original_price":1.49,
                "promotion_type":"","is_loyalty":False,"size_label":"500 g",
                "url":"https://www.ah.nl"}]
        result=ingredient_price("broccoli",500,"g",shelf,offer)
        self.assertEqual(result["cash_price"],1.0)
        self.assertFalse(result["sale"])

    def test_risotto_heeft_echte_risottorijst(self):
        risottos=[r for r in RECIPES if "risotto" in r[0].lower()]
        self.assertTrue(risottos)
        for title,category,minutes,ings in risottos:
            keys={key for key,qty,unit in ings}
            self.assertIn("risottorijst",keys)
            self.assertNotIn("rijst",keys)
            self.assertFalse(validate_dish_ingredients(title,ings))
            self.assertIn(title,RECIPE_METHODS)
            profile=nutrition_profile(ings)
            self.assertGreaterEqual(profile["vegetable_g_per_serving_estimate"],250)
            self.assertGreaterEqual(profile["protein_g_per_serving_estimate"],30)
            self.assertIsNotNone(profile["kcal_per_serving_estimate"])

    def test_geen_verkeerde_rijst_voor_risotto(self):
        self.assertTrue(match_ingredient({"norm":"jumbo arborio risottorijst 500 g"},"risottorijst"))
        self.assertTrue(match_ingredient({"norm":"ah carnaroli rijst 500 g"},"risottorijst"))
        self.assertFalse(match_ingredient({"norm":"ah zilvervliesrijst 500 g"},"risottorijst"))
        self.assertFalse(match_ingredient({"norm":"risotto maaltijd met champignons"},"risottorijst"))
        self.assertFalse(match_ingredient({"norm":"arborio risottorijst 500 g"},"rijst"))
        self.assertTrue(validate_dish_ingredients(
            "Champignonrisotto", [("rijst",180,"g"),("champignons",1000,"g")]))
        self.assertTrue(validate_dish_ingredients(
            "Kipwrap", [("kipfilet",800,"g"),("sla",600,"g")]))
        self.assertTrue(validate_dish_ingredients(
            "Volkoren pasta met kip", [("rijst",200,"g"),("kipfilet",800,"g")]))

    def test_alle_recepten_hebben_passende_gerechtbasis(self):
        for title,category,minutes,ingredients in RECIPES:
            with self.subTest(title=title):
                self.assertEqual(validate_dish_ingredients(title,ingredients),[])

    def test_actierecepten_hebben_de_nodige_bereidingsstappen(self):
        examples=[
            ("Teriyaki-kip met broccoli en rijst",
             [("kipfilet",800,"g"),("broccoli",1000,"g"),("rijst",140,"g")],
             "Roerbak kip en broccoli; serveer met rijst.","Kook de zilvervliesrijst"),
            ("Italiaanse gehaktballetjes met pasta",
             [("kipgehakt",800,"g"),("pasta",300,"g"),("spinazie",500,"g")],
             "Bak kipgehaktballetjes en serveer met pasta.","Kook de volkoren pasta"),
            ("Tonijnwraps met tomaat",
             [("tonijn",500,"g"),("wraps",4,"st"),("tomaten",400,"g")],
             "Vul wraps met tonijn en tomaat.","Laat de tonijn"),
        ]
        for title,ingredients,method,required in examples:
            with self.subTest(title=title):
                result=cooking_instructions(title,ingredients,method)
                self.assertIn(required,result)
        self.assertIn("Verwarm de wraps",cooking_instructions(*examples[2][:2],
                                                              curated=examples[2][2]))

    def test_aanbiedingsbadge_alleen_bij_verifieerbare_korting(self):
        single={"price":2.49,"original_price":3.49}
        self.assertTrue(verified_discount(single))
        self.assertAlmostEqual(verified_discount_percentage(single),28.7)
        unknown={"price":2.49,"original_price":None}
        self.assertFalse(verified_discount(unknown))
        self.assertIsNone(verified_discount_percentage(unknown))
        bundle={"price":1.19,"original_price":1.19,
                "multi_buy_quantity":2,"multi_buy_price":1.99}
        self.assertTrue(verified_discount(bundle))
        self.assertAlmostEqual(verified_discount_percentage(bundle),16.4)
        no_saving={**bundle,"multi_buy_price":2.50}
        self.assertFalse(verified_discount(no_saving))

    def test_aanbieding_met_niet_geverifieerde_normaalprijs_niet_als_korting(self):
        product={"name":"Jumbo broccoli 500 g","norm":"jumbo broccoli 500 g",
                 "quantity":500,"unit":"g","size_label":"500 g",
                 "price":0.99,"original_price":None,"promotion_type":"actie",
                 "multi_buy_quantity":None,"multi_buy_price":None,
                 "is_loyalty":False,"url":"https://www.jumbo.com"}
        self.assertEqual(offer_price("broccoli",500,"g",[product]),[])
        product["original_price"]=1.49
        self.assertEqual(len(offer_price("broccoli",500,"g",[product])),1)

    def test_ingrediënt_in_titel_mag_niet_ontbreken(self):
        self.assertTrue(dish_quality_issues("Tofuwok met broccoli","Vegetarisch",
                                            [("tofu",600,"g"),("wok",800,"g")]))
        self.assertFalse(dish_quality_issues("Kip met broccoli","Kip",
                                            [("kipfilet",600,"g"),("broccoli",800,"g")]))

    def test_werkelijke_meerstukskorting_ondanks_gelijke_losse_prijs(self):
        bundle={"name":"Jumbo Minikrieltjes 600 g",
                "norm":"jumbo minikrieltjes 600 g","quantity":600,"unit":"g",
                "size_label":"600 g","price":1.19,"original_price":1.19,
                "multi_buy_quantity":2,"multi_buy_price":1.99,
                "promotion_type":"2 voor 1,99","is_loyalty":False,
                "url":"https://www.jumbo.com"}
        result=offer_price("aardappel",1200,"g",[bundle])
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["cash_price"],1.99)
        self.assertEqual(result[0]["packages"],2)
        bundle["multi_buy_price"]=2.50
        self.assertEqual(offer_price("aardappel",1200,"g",[bundle]),[])

    def test_numerieke_api_hoeveelheid_heeft_verpakkingsfallback(self):
        product={"name":"AH broccoli 500 g","quantity":500,"size":"500 g"}
        self.assertEqual(measure_offer(product),(500,"g"))
        self.assertEqual(offer_size_label(product,500,"g"),"500 g")
        self.assertEqual(measure_offer({"name":"Jumbo aardappelen 1 kg",
                                       "quantity":1000,"size":""}),(1000,"g"))

    def test_kwaliteitsaudit_met_onbevestigde_eiwitwaarden(self):
        recipe={"title":"Fruitkwark met vanille","meal_type":"Ontbijt",
                "complete":True,"offer_driven":False,"ingredients":[],
                "nutrition":{"protein_g_per_serving_estimate":None,
                             "vegetable_g_per_serving_estimate":0}}
        report=audit_recipe_quality({"ah":[recipe]})
        self.assertEqual(report["ah"]["review_needed"],1)
        self.assertIn("Eiwitwaarde van gekozen product niet geverifieerd",
                      report["ah"]["examples"][0]["issues"])

    def test_verpakkingen(self):
        self.assertEqual(measure("2 x 125 g"),(250,"g"))
        self.assertEqual(measure("0,75 liter"),(750,"ml"))
        self.assertEqual(measure("per stuk"),(1,"st"))
        self.assertEqual(measure("500 g"),(500,"g"))

    def test_bundel_kassa(self):
        promo={"price":2,"original_price":4,"multi_buy_quantity":2,"multi_buy_price":4}
        self.assertEqual(total_for(2,4,promo),(4,2))
        self.assertEqual(total_for(3,4,promo),(8,3))

    def test_blijf_weg_bij_verkeerde_ingrediënten(self):
        self.assertFalse(match_ingredient({"norm":"kipfilet plantaardig 200 g"},"kipfilet"))
        self.assertFalse(match_ingredient({"norm":"witte bonen tomatensaus"},"tomaten"))
        self.assertFalse(match_ingredient({"norm":"zoete aardappelgratin 400 g"},"zoete_aardappel"))
        self.assertFalse(match_ingredient({"norm":"jumbo spinazie a la creme 800 g"},"spinazie"))
        self.assertFalse(match_ingredient({"norm":"no fairytales paprika wraps"},"paprika"))
        self.assertFalse(match_ingredient({"norm":"gedroogde linzen 500 g"},"linzen"))
        self.assertTrue(match_ingredient({"norm":"ah kipfilet 600 g"},"kipfilet"))

    def test_geen_bonus_op_onjuist_artikel(self):
        shelf={"norm":"ah tomatenblokjes 400 g","unit":"g","quantity":400,"price":.69}
        offer={"norm":"ah cherrytomaten 400 g","unit":"g","quantity":400,"original_price":.69,"price":.35}
        self.assertIsNone(promo_for(shelf,[offer]))

    def test_onbekende_schapprijs_niet_geschat(self):
        self.assertIsNone(ingredient_price("kipfilet",600,"g",[],[]))

    def test_meerdere_verpakkingen(self):
        p={"norm":"ah kipfilet 400 g","name":"AH Kipfilet 400 g","quantity":400,
           "unit":"g","price":4.0,"size_label":"400 g","url":"https://ah.nl/"}
        r=ingredient_price("kipfilet",600,"g",[p],[])
        self.assertEqual(r["packages"],2)
        self.assertEqual(r["cash_price"],8)
        self.assertEqual(r["used_price"],6)
if __name__=="__main__":unittest.main()
