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
    report = calculate(basket, quotes, cfg["stores"], cfg["weekly_budget_eur"])
    if not basket:
        report["status"] = "basket_not_configured"
        report["recommended"] = None
    target = ROOT/args.output
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n")
    print(json.dumps(report, ensure_ascii=False))

if __name__ == "__main__":
    main()
