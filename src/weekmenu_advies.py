"""Vergelijk hetzelfde gezonde mealprep-weekmenu bij drie supermarkten.

Dit is GEEN vergelijking van de volledige huishoudelijke weekboodschappen:
uitsluitend drie identieke recepten (elk 4 porties), normale boodschappen uit
de winkel en daadwerkelijk gevonden acties. Bezorging, kruiden, lokaal
assortiment en voorraad zijn niet bevestigd.
"""
import math
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

STORES=("ah","jumbo","lidl")
GROUPS=("Kip","Vis","Vegetarisch","Vlees")
TZ=ZoneInfo("Europe/Amsterdam")

def matching_recipes(recipes):
    """Alleen exact dezelfde ingrediënten en hoeveelheden vergelijken."""
    lists={}
    for store in STORES:
        by_name={}
        for r in recipes.get(store,[]):
            if (not r.get("complete") or r.get("offer_driven") or
                r.get("meal_type")!="Avondeten" or not r.get("ingredients") or
                r.get("minutes",999)>45):
                continue
            signature=tuple(sorted((l["key"],float(l["required"]),l["unit"])
                                   for l in r["ingredients"]))
            if len(signature)<3:continue
            by_name[(r["title"],signature)]=r
        lists[store]=by_name
    shared=set.intersection(*(set(v) for v in lists.values()))
    return [(key,{store:lists[store][key] for store in STORES}) for key in shared]

def _cost_of_lines(lines):
    """Tel dezelfde verkoopeenheid samen, inclusief noodzakelijke bundels."""
    from receptenradar_v2 import total_for
    groups={}
    for line in lines:
        unit_size=float(line["package_size"])
        old_packs=math.ceil(float(line["required"])/unit_size)
        if not old_packs or not unit_size:raise ValueError("Onvolledige verpakkingseenheid")
        regular=round(float(line["regular_cash"])/old_packs,4)
        actual=round(float(line["cash_price"])/max(1,int(line["packages"])),4)
        action=line.get("action") if line.get("sale") else None
        promo_id=(action or {}).get("url") if action else None
        # Product/variant en prijsstructuur moeten identiek zijn om te combineren.
        key=(str(line["product"]).casefold(),unit_size,line["unit"],regular,
             None if action else actual,promo_id,bool(action))
        g=groups.setdefault(key,{"label":line["label"],"product":line["product"],
                     "package":line["package"],"package_size":unit_size,
                     "unit":line["unit"],"required":0.0,
                     "regular_unit_price":regular,"price_per_unit":actual,
                     "action":action})
        g["required"]+=float(line["required"])
    purchased=[]
    for x in groups.values():
        needed=math.ceil(round(x["required"],5)/x["package_size"])
        if x["action"]:
            total,packs=total_for(needed,x["regular_unit_price"],x["action"])
            # No assume deal if bundling or app conditions unknown.
            if total>=round(needed*x["regular_unit_price"],2):
                total=round(needed*x["regular_unit_price"],2);packs=needed
        else:
            total=round(needed*x["price_per_unit"],2);packs=needed
        purchased.append({"label":x["label"],"product":x["product"],
                          "required":round(x["required"],2),"unit":x["unit"],
                          "package":x["package"],"packages":packs,
                          "cash_price":round(total,2),
                          "regular_cash":round(needed*x["regular_unit_price"],2),
                          "sale":total+0.001<needed*x["regular_unit_price"]})
    purchased.sort(key=lambda x:(x["label"].casefold(),x["product"].casefold()))
    return {"checkout":round(sum(x["cash_price"] for x in purchased),2),
            "regular_reference":round(sum(x["regular_cash"] for x in purchased),2),
            "sale_line_count":sum(x["sale"] for x in purchased),
            "products":purchased}

def build_weekmenu(recipes,target=3):
    if any(not recipes.get(store) for store in STORES):
        return {"status":"incomplete_sources","message":"Niet alle drie supermarkten leveren receptprijzen."}
    shared=matching_recipes(recipes)
    if len(shared)<2:
        return {"status":"insufficient_common_recipes","common_recipes":len(shared),
                "message":"Onvoldoende identieke, volledig geprijsde recepten bij AH, Jumbo en Lidl."}
    ranked=[]
    for (title,signature),quotes in shared:
        nutrition=quotes["ah"].get("nutrition") or {}
        minimum_protein=min((q.get("nutrition") or {}).get("protein_g_per_serving_estimate") or 0
                            for q in quotes.values())
        minimum_veg=min((q.get("nutrition") or {}).get("vegetable_g_per_serving_estimate") or 0
                        for q in quotes.values())
        healthy=minimum_protein>=30 and minimum_veg>=200
        average=sum(float(q["checkout"]) for q in quotes.values())/len(STORES)
        promos=sum(max(q.get("sale_count",0),
                       (q.get("deal_basket") or {}).get("used_actions",0))
                   for q in quotes.values())
        ranked.append((not healthy,average,-promos,title,quotes,healthy,
                       minimum_protein,minimum_veg))
    ranked.sort(key=lambda x:x[:4])
    chosen=[];used_types=set()
    # Eerst waar mogelijk verschillende hoofdgroepen en minstens twee goede
    # voedzame maaltijden. Vul pas daarna aan.
    for row in ranked:
        cat=row[4]["ah"].get("category")
        if len(chosen)>=target:break
        if cat not in used_types and row[5]:
            chosen.append(row);used_types.add(cat)
    for row in ranked:
        if len(chosen)>=target:break
        if row not in chosen and row[5]:
            chosen.append(row)
    for row in ranked:
        if len(chosen)>=target:break
        if row not in chosen:chosen.append(row)
    dishes=[{"title":row[3],"category":row[4]["ah"].get("category"),
             "cuisine":row[4]["ah"].get("cuisine"),
             "minutes":row[4]["ah"].get("minutes"),
             "portions":4,"protein_min_g_per_portion":round(row[6],1),
             "vegetable_min_g_per_portion":round(row[7]),
             "passes_nutrition_preference":row[5]} for row in chosen]
    totals={}
    for store in STORES:
        all_lines=[line for row in chosen for line in row[4][store]["ingredients"]]
        totals[store]=_cost_of_lines(all_lines)
    order=sorted(STORES,key=lambda x:totals[x]["checkout"])
    result={"status":"indicative_online_comparison",
            "updated_at":datetime.now(TZ).isoformat(),
            "recipe_count":len(chosen),"portion_count":len(chosen)*4,
            "same_recipes_all_stores":True,
            "meals":dishes,"stores":totals,
            "cheapest_store":order[0],
            "order_cheapest_first":order,
            "price_exclusions":["kruiden en andere standaardvoorraad",
                                "bezorgkosten en eventuele minimale bestelkosten",
                                "persoonlijke kortingen en lokale winkelvoorraad"],
            "disclaimer":"Indicatieve online kassaprijs van verpakkingen voor dezelfde recepten bij elke supermarkt, zonder lokaal bevestigde voorraad."}
    return result
