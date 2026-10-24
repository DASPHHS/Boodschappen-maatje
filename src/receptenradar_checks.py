"""Consistentiecontrole voor te publiceren recepten en prijzen.

Stop de dagelijkse publicatie bij aantoonbaar tegenstrijdige bedragen of
prijsstatussen. Ontbrekende prijzen blijven toegestaan mits zichtbaar gemeld.
"""
from collections import Counter


def validate_publication(recipes):
    issues=[]
    for store,items in recipes.items():
        ids=[r["id"] for r in items]
        for key,count in Counter(ids).items():
            if count>1:
                issues.append(f"{store}: dubbele recept-id {key}")
        for r in items:
            name=f"{store}: {r['title']}"
            lines=r.get("ingredients") or []
            absent=r.get("missing") or []
            complete=bool(r.get("complete"))
            if complete != (bool(lines) and not absent):
                issues.append(f"{name}: onjuiste indicatie volledig geprijsd")
            if r.get("covered_count")!=len(lines):
                issues.append(f"{name}: geprijsde regel-aantallen kloppen niet")
            if r.get("ingredient_count")!=len(lines)+len(absent):
                issues.append(f"{name}: ingrediënten ontbreken uit totaaloverzicht")
            checked=round(sum(l.get("cash_price",0) for l in lines),2)
            if abs(checked-r.get("known_subtotal",0))>.015:
                issues.append(f"{name}: subtotaal wijkt af van productprijzen")
            if complete:
                if r.get("checkout") is None or abs(checked-r["checkout"])>.015:
                    issues.append(f"{name}: afrekenbedrag wijkt af van productprijzen")
                consumed=round(sum(l.get("used_price",0) for l in lines),2)
                if r.get("per_serving") is None or abs(round(consumed/4,2)-r["per_serving"])>.015:
                    issues.append(f"{name}: portieprijs wijkt af van ingrediënten")
            else:
                if r.get("checkout") is not None or r.get("per_serving") is not None:
                    issues.append(f"{name}: onvolledige mand toont toch volledige prijs")
            used=sum(bool(l.get("sale")) for l in lines)
            if r.get("sale_count")!=used:
                issues.append(f"{name}: aantal werkelijk gebruikte acties onjuist")
            if any(l.get("sale") and not l.get("action") for l in lines):
                issues.append(f"{name}: actie zonder bron en voorwaarden")
            offer=r.get("deal_basket") or {}
            offer_lines=offer.get("ingredients") or []
            if offer.get("used_actions")!=sum(bool(l.get("sale")) for l in offer_lines):
                issues.append(f"{name}: actieaantal in actiemand onjuist")
            if len(offer_lines)!=len(lines):
                issues.append(f"{name}: actiemand bevat andere ingrediënten")
            offer_total=round(sum(l.get("cash_price",0) for l in offer_lines),2)
            if abs(offer_total-(offer.get("known_subtotal") or 0))>.015:
                issues.append(f"{name}: actiemand-bedrag klopt niet")
            if complete and (offer.get("checkout") is None or
                             abs(offer_total-offer["checkout"])>.015):
                issues.append(f"{name}: volledige actiemand heeft onjuist bedrag")
            if len(issues)>=50:
                break
        if len(issues)>=50:
            break
    if issues:
        raise ValueError("Receptenradar publicatie afgekeurd: "+"; ".join(issues[:12]))
    return sum(len(items) for items in recipes.values())
