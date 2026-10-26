"""Vergelijk een of twee verpakkingstypen voor hetzelfde ingrediënt.

Bundelaanbiedingen zijn uitgesloten van mengcombinaties omdat een
actieprijs dan niet noodzakelijk per losse verpakking geldt.
"""
import math
from itertools import combinations
from portie_flexibiliteit import needed_quantity

def mixed_pack_option(ingredient,amount,unit,options,max_types=16):
    singles=[]
    seen=set()
    for item in options:
        size=item.get("package_size")
        packs=item.get("packages")
        if not size or not packs or size<=0 or packs<=0:
            continue
        action=item.get("action") or {}
        if (action.get("multi_buy_quantity") or 0)>=2:
            continue
        price=round(item["cash_price"]/packs,2)
        regular=round(item["regular_cash"]/packs,2)
        if price<=0:continue
        key=(item["product"],size,price)
        if key in seen:continue
        seen.add(key)
        singles.append({**item,"single_price":price,"single_regular":regular})
    # Neem zowel de goedkoopste eenheidsprijzen als kleine verpakkingen op.
    ranked=sorted(singles,key=lambda x:(x["single_price"]/x["package_size"],x["single_price"]))
    small=sorted(singles,key=lambda x:(x["package_size"],x["single_price"]))
    selected=list({(x["product"],x["package_size"],x["single_price"]):x
                   for x in ranked[:max_types]+small[:max_types]}.values())
    best=None
    for a,b in combinations(selected,2):
        if a["frozen"]!=b["frozen"] or a["flavoured_dairy"]!=b["flavoured_dairy"]:
            continue
        if a["product"]==b["product"] and a["package_size"]==b["package_size"]:
            continue
        # Bij maximaal twee verpakkingstypen ontstaan beheersbare kassaregels.
        for na in range(1, min(12, math.ceil(amount/a["package_size"])+1)):
            for nb in range(1, min(12, math.ceil(amount/b["package_size"])+1)):
                available=na*a["package_size"]+nb*b["package_size"]
                if available<=0:continue
                required=needed_quantity(ingredient,amount,unit,available)
                if available<required:continue
                cost=round(na*a["single_price"]+nb*b["single_price"],2)
                regular=round(na*a["single_regular"]+nb*b["single_regular"],2)
                components=[]
                for p,n in ((a,na),(b,nb)):
                    components.append({
                        "product":p["product"],"package":p["package"],
                        "package_size":p["package_size"],"packages":n,
                        "unit_price":p["single_regular"],
                        "cash_price":round(n*p["single_price"],2),
                        "sale":p["sale"],"action":p.get("action"),
                        "url":p.get("url")})
                sale=any(c["sale"] for c in components)
                offer=next((c["action"] for c in components if c["sale"]),None)
                result={
                    "key":ingredient,"label":a["label"],"required":required,
                    "original_required":amount,"adjusted":required<amount,
                    "unit":unit,"product":" + ".join(c["product"] for c in components),
                    "package":" + ".join(f'{c["packages"]} × {c["package"]}' for c in components),
                    "package_size":available,"packages":1,"cash_price":cost,
                    "used_price":round(required/available*cost,2),
                    "regular_cash":regular,"sale":sale,"action":offer,
                    "source":"Combinatie van winkelverpakkingen",
                    "url":a["url"],"frozen":a["frozen"],
                    "flavoured_dairy":a["flavoured_dairy"],
                    "nutrition_unverified":a.get("nutrition_unverified") or b.get("nutrition_unverified"),
                    "components":components
                }
                # Goedkoopste kassaprijs, bij gelijkstand weinig restproduct,
                # daarna een echte korting. Nooit een actie boven prijs plaatsen.
                rank=(cost,available-required,not sale)
                if best is None or rank<best[0]:
                    best=(rank,result)
    return best[1] if best else None
