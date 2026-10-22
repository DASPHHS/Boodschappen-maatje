"""Plan recipes within ONE supermarket, using only genuine currently indexed deals.

A complete basket price is not claimed when regular shelf prices / package size
and ingredient quantities are missing.
"""
import re
from collections import defaultdict
from datetime import date

RECIPES=[
 ("Harissa-kipwraps",["kip","wrap","paprika","spinazie"],"Kruid kip met harissa, bak en serveer in volkoren wraps met verse groenten."),
 ("Groenterijke nasi met ei",["rijst","ei","prei","wortel"],"Kook rijst, wok groenten en roerbak het ei erdoor."),
 ("Kip met geroosterde groenten",["kip","courgette","paprika"],"Rooster gekruide kip en groenten in de oven."),
 ("Shakshuka",["ei","tomaat","paprika"],"Stoof de groenten en gaar eieren in de saus."),
 ("Tonijnbonensalade",["tonijn","bonen","tomaat"],"Meng tonijn, bonen en groenten."),
 ("Zalm met broccoli",["zalm","broccoli"],"Bak zalm en stoom broccoli."),
 ("Kip-kerrie met bloemkoolrijst",["kip","bloemkool","kerrie"],"Bak kip met kerrie, bereid bloemkoolrijst."),
 ("Vegetarische chili",["bonen","paprika","tomaat"],"Laat bonen en groenten met kruiden sudderen."),
 ("Kip uit de airfryer",["kip","sla","aardappel"],"Bereid gekruide kip in de airfryer en maak een salade."),
 ("Volkoren pastasalade",["pasta","tomaat","kip"],"Kook pasta en meng met kip en groenten."),
 ("Frittata met groenten",["ei","spinazie","champignon"],"Bak de groenten, voeg ei toe en laat stollen."),
 ("Gevulde paprika met gehakt",["paprika","gehakt","tomaat"],"Vul paprika's met gebakken gehakt en groenten en gaar in de oven."),
 ("Wraps met tofu",["tofu","wrap","komkommer"],"Bak tofu en serveer met rauwkost in wraps."),
 ("Couscous met gegrilde groenten",["couscous","courgette","aubergine"],"Grill groenten en meng met couscous."),
 ("Kruidige linzensoep",["linzen","wortel","tomaat"],"Kook linzen met groenten en specerijen.")
]
ALIASES={
 "kip":("kip","kipfilet","kipdij"),"wrap":("wrap","wraps","tortilla"),
 "ei":("eieren","ei "," eieren"),"tomaat":("tomaat","tomaten"),
 "bonen":("bonen","kidney","black beans"),"pasta":("pasta","penne","fusilli"),
 "rijst":("rijst","basmati"),"kerrie":("kerrie","curry"),
 "gehakt":("gehakt",),"sla":("sla","slamelange"),
 "aardappel":("aardappel","krieltjes"),"wortel":("wortel","winterpeen"),
 "tonijn":("tonijn",),"spinazie":("spinazie",),"tofu":("tofu",),
 "paprika":("paprika",),"courgette":("courgette",),
 "broccoli":("broccoli",),"zalm":("zalm",),"linzen":("linzen",),
 "couscous":("couscous",),"aubergine":("aubergine",),
 "komkommer":("komkommer",),"prei":("prei",),"champignon":("champignon",),
 "bloemkool":("bloemkool",)
}
def eligible(offer,day=None):
    today=day or date.today().isoformat()
    if offer.get("price") is None:return False
    if offer.get("promotion_status")=="historical":return False
    if offer.get("valid_from") and str(offer["valid_from"])[:10]>today:return False
    if offer.get("valid_until") and str(offer["valid_until"])[:10]<today:return False
    return True

def matches(text,ingredient):
    name=" "+re.sub(r"[^a-z0-9 ]+"," ",text.lower())+" "
    return any(re.search(r"(?<![a-z])"+re.escape(alias)+r"(?![a-z])",name) for alias in ALIASES.get(ingredient,(ingredient,)))

def plan_one_store(offers, day=None):
    by_store=defaultdict(list)
    for o in offers:
        if eligible(o,day):
            by_store[o["store"]].append(o)
    plans=[]
    for title,ingredients,method in RECIPES:
        for store,items in by_store.items():
            found=[]; missing=[]
            for ingredient in ingredients:
                choices=[o for o in items if matches(o.get("text",""),ingredient)]
                if not choices:
                    missing.append(ingredient)
                    continue
                # Lowest currently known promotional price from this ONE store.
                best=min(choices,key=lambda x:(float(x["price"]),-float(x.get("savings_percentage") or 0)))
                found.append({"ingredient":ingredient,"product":best["text"],"price":best["price"],
                              "unit_price":best.get("unit_price"),"discount_percentage":best.get("savings_percentage"),
                              "url":best.get("url"),"valid_until":best.get("valid_until")})
            # Only show recipes genuinely built on multiple confirmed action products.
            # A single matched ingredient is NOT an action-based recipe.
            if len(found)<2 or len(found)*2<len(ingredients):
                continue
            plans.append({"name":title,"store":store,"servings":4,"ingredients":ingredients,
                          "method":method,"matches":found,"missing":missing,
                          "coverage":round(len(found)/len(ingredients)*100),
                          "matched_count":len(found),"missing_count":len(missing),
                          "known_promotion_product_sum":round(sum(float(x["price"]) for x in found),2),
                          "total_price":None,
                          "cost_note":"Niet de receptprijs: normale prijzen, vereiste hoeveelheden en ontbrekende ingrediënten zijn niet bekend."})
    return sorted(plans,key=lambda p:(p["missing_count"],-p["matched_count"],p["known_promotion_product_sum"],p["store"]))[:80]
