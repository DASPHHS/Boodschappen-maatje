"""Weekly single-store basket comparison using VERIFIED, complete product quotes only."""
import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def calculate(basket, quotes, stores, budget):
    """basket: [{id,quantity}]; quotes: [{id,store,price_eur,verified,available}].
    Prices are totals for the exact required basket quantity, including promotions.
    """
    prices = defaultdict(dict)
    for q in quotes:
        if not q.get("verified") or not q.get("available"):
            continue
        if q.get("price_eur") is None or float(q["price_eur"]) < 0:
            continue
        prices[q["store"]][q["id"]] = float(q["price_eur"])
    results = []
    for store in stores:
        missing = [x["id"] for x in basket if x["id"] not in prices[store]]
        total = round(sum(prices[store][x["id"]] for x in basket if x["id"] in prices[store]), 2)
        results.append({"store": store, "complete": not missing, "missing": missing,
                        "total_eur": total if not missing else None,
                        "within_budget": total <= budget if not missing else None})
    eligible = sorted((r for r in results if r["complete"]), key=lambda x:x["total_eur"])
    return {"generated_at": datetime.now(timezone.utc).isoformat(),
            "budget_eur": budget, "recommended": eligible[0] if eligible else None,
            "stores": results, "status": "ready" if eligible else "insufficient_verified_prices",
            "notice": "No store is recommended without verified prices for every basket item."}

def report_from_receptenradar(path,budget):
    """Automatische weekmenukeuze uit identieke, volledig geprijsde gerechten.

    Geen persoonlijke kassabon of totale huishoudelijke boodschappenprijs;
    Picnic ontbreekt zolang het eigen schapprijsbestand niet is gekoppeld.
    """
    try:
        data=json.loads(Path(path).read_text(encoding="utf-8"))
        m=data.get("weekmenu_advice") or {}
        source_at=data.get("updated_at")
        updated=datetime.fromisoformat(source_at)
        from datetime import timedelta
        if updated.tzinfo is None or datetime.now(timezone.utc)-updated>timedelta(hours=72):
            return {"status":"stale_recipe_prices","recommended":None,"stores":[],
                    "notice":"Receptprijzen ouder dan 72 uur: geen koopadvies zonder nieuwe scan."}
        if m.get("status")!="indicative_online_comparison":
            return {"status":"no_common_weekmenu","recommended":None,"stores":[],
                    "notice":m.get("message","Geen compleet vergelijkbaar menu bij alle drie winkels.")}
        names={"ah":"Albert Heijn","jumbo":"Jumbo","lidl":"Lidl"}
        stores=[]
        for store in ("ah","jumbo","lidl"):
            quote=(m.get("stores") or {}).get(store)
            if not quote or quote.get("checkout") is None:
                return {"status":"incomplete_recipe_prices","recommended":None,"stores":[],
                        "notice":"Een van de winkels mist een volledige kassaprijs."}
            total=round(float(quote["checkout"]),2)
            stores.append({"store":names[store],"complete":True,
                           "total_eur":total,
                           "within_budget":total<=budget})
        stores.sort(key=lambda x:x["total_eur"])
        stores.append({"store":"Picnic","complete":False,"total_eur":None,
                       "within_budget":None,
                       "missing":["Prijsdekking Picnic nog niet aangesloten"]})
        return {"status":"indicative_recipe_comparison",
                "source_updated_at":source_at,
                "recommended":stores[0],"stores":stores,
                "meals":m.get("meals",[]),
                "recipe_count":m["recipe_count"],"portion_count":m["portion_count"],
                "price_exclusions":m.get("price_exclusions",[]),
                "notice":"Vergelijking voor exact dezelfde geprijsde recepten bij AH, Jumbo en Lidl. Geen volledige huishoudelijke weekmand. Online schapprijzen en aanbiedingen kunnen afwijken van lokale winkelvoorraad."}
    except (OSError,ValueError,TypeError,KeyError) as exc:
        return {"status":"recipe_data_unavailable","recommended":None,"stores":[],
                "notice":"Weekmenugegevens niet betrouwbaar beschikbaar: "+type(exc).__name__}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--basket", default="data/basket.json")
    p.add_argument("--quotes", default="data/verified-prices.json")
    p.add_argument("--output", default="docs/weekly-advice.json")
    args = p.parse_args()
    cfg = json.loads((ROOT/"config"/"shopping-agent.json").read_text())
    basket_path, quote_path = ROOT/args.basket, ROOT/args.quotes
    basket = json.loads(basket_path.read_text()) if basket_path.exists() else []
    quotes = json.loads(quote_path.read_text()) if quote_path.exists() else []
    if basket:
        report=calculate(basket,quotes,cfg["stores"],cfg["weekly_budget_eur"])
    else:
        report=report_from_receptenradar(ROOT/"recepten"/"data.json",
                                        cfg["weekly_budget_eur"])
        report["comparison_type"]="zelfde drie recepten uit bestaande Recepten Radar"
    report["budget_eur"]=cfg["weekly_budget_eur"]
    report["generated_at"]=datetime.now(timezone.utc).isoformat()
    target = ROOT/args.output
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n")
    print(json.dumps(report, ensure_ascii=False))

if __name__ == "__main__":
    main()
