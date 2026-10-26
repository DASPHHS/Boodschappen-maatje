"""Conservatieve scanbewaking: brondekking, prijssanity en herstelstatus.

Waarschuwingen zijn geen bevestigde productfouten. Een lege of deels defecte
bron mag nooit als volledig betrouwbare winkeldekking worden gemarkeerd.
"""
from math import isfinite

MIN_SHELF={"ah":1000,"jumbo":1000,"lidl":1000}
MIN_PROMOS={"ah":100,"jumbo":100,"lidl":100}

def inspect_snapshot(shelves,offers,errors=()):
    warnings=list(errors)
    metrics={}
    for store in ("ah","jumbo","lidl"):
        products=shelves.get(store,[])
        promotions=offers.get(store,[])
        bad_prices=sum(1 for p in products if not isinstance(p.get("price"),(int,float))
                       or not isfinite(p["price"]) or p["price"]<=0)
        bad_promos=sum(1 for p in promotions if not isinstance(p.get("price"),(int,float))
                       or not isfinite(p["price"]) or p["price"]<=0
                       or not p.get("valid_from") or not p.get("valid_until")
                       or p["valid_from"]>p["valid_until"])
        if len(products)<MIN_SHELF[store]:
            warnings.append(f"{store}: slechts {len(products)} assortimentprijzen beschikbaar")
        if len(promotions)<MIN_PROMOS[store]:
            warnings.append(f"{store}: slechts {len(promotions)} actievermeldingen; onvolledige dekking mogelijk")
        if bad_prices or bad_promos:
            warnings.append(f"{store}: {bad_prices} ongeldige schapprijzen, {bad_promos} ongeldige acties")
        metrics[store]={"shelf_records":len(products),"promotion_records":len(promotions),
                        "invalid_shelf_prices":bad_prices,"invalid_promotions":bad_promos,
                        "coverage_status":"attention" if (len(products)<MIN_SHELF[store] or
                          len(promotions)<MIN_PROMOS[store] or bad_prices or bad_promos
                          or any(str(e).startswith(store+":") for e in errors)) else "plausible_not_complete"}
    return {"stores":metrics,"warnings":list(dict.fromkeys(warnings)),
            "all_sources_complete":False,"local_stock_verified":False}
