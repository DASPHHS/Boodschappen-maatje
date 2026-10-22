"""Koopkracht 1.0: gratis PrijsProfeet-aanbiedingen zonder OCR of API-key."""
import json, os, sys, time, urllib.parse
from datetime import datetime, timezone, date
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from koopkracht import render, recipe_suggestions

BASE="https://www.prijsprofeet.nl/api/v1"
RETAILERS=["albert_heijn","jumbo","lidl","aldi","dirk","plus","hoogvliet","vomar","dekamarkt","ekoplaza"]
NAMES={"albert_heijn":"Albert Heijn","jumbo":"Jumbo","lidl":"Lidl","aldi":"Aldi","dirk":"Dirk","plus":"PLUS","hoogvliet":"Hoogvliet","vomar":"Vomar","dekamarkt":"DekaMarkt","ekoplaza":"Ekoplaza"}
HEADERS={"User-Agent":"KoopkrachtPersonal/1.0 (https://github.com/DASPHHS/koopkracht; personal research)",
         "Accept":"application/json"}
if os.getenv("PRIJS PROFEET_KEY".replace(" ","_")):
    HEADERS["X-API-Key"]=os.environ["PRIJS_PROFEET_KEY"]

def request(path,params=None):
    url=BASE+path
    err=None
    for n in range(3):
        try:
            r=requests.get(url,params=params,headers=HEADERS,timeout=20)
            if r.status_code==429 or r.status_code>=500:
                err=f"HTTP {r.status_code} {r.url}";time.sleep(2**n);continue
            r.raise_for_status()
            return r.json()
        except (requests.RequestException,ValueError) as e:
            err=str(e)
            time.sleep(n+1)
    raise RuntimeError(err)

def num(value):
    if value is None or isinstance(value,bool):return None
    try:return round(float(str(value).replace(",",".")),2)
    except (ValueError,TypeError):return None

def first(obj,*names):
    for name in names:
        val=obj.get(name)
        if val is not None and val!="":return val
    return None

def normalize(deal,retailer,kind):
    product=deal.get("representative_product") or deal.get("product") or deal
    if not isinstance(product,dict):product={}
    name=first(product,"name","product_name") or first(deal,"name","brand")
    if not name:return None
    price=num(first(product,"price","deal_price","promotional_price"))
    if price is None:price=num(first(deal,"price","deal_price"))
    original=num(first(product,"original_price","regular_price"))
    if original is None:original=num(first(deal,"original_price","regular_price"))
    savings=num(first(deal,"savings_percentage","discount_percentage"))
    if savings is None and price is not None and original and original>price:
        savings=round(100*(original-price)/original,1)
    status=first(product,"promotion_status","status") or first(deal,"promotion_status")
    valid_from=first(product,"valid_from") or first(deal,"valid_from")
    valid_until=first(product,"valid_until") or first(deal,"valid_until")
    if status=="historical":return None
    retailer_name=NAMES.get(retailer,retailer)
    pid=str(first(product,"id","product_id") or first(deal,"id","brand") or name)
    return {"id":retailer+":"+pid+":"+kind,"store":retailer_name,"text":str(name),
            "price":price,"original_price":original,"savings_percentage":savings,
            "valid_from":valid_from,"valid_until":valid_until,"promotion_status":status or "unknown",
            "brand":first(product,"brand") or first(deal,"brand"),"category":first(product,"unified_category","category"),
            "unit_price":first(product,"unit_price"),"image_url":first(product,"image_url","image"),
            "url":first(product,"url","product_url") or "https://www.prijsprofeet.nl",
            "source":"prijsprofeet","verified":False,"kind":kind}

def main():
    offers=[]; failures=[]; counts={}
    for retailer in RETAILERS:
        try:
            data=request("/deals/top",{"retailer":retailer,"limit":50})
            rows=[]
            for kind in ("top_by_percentage","top_by_amount"):
                for deal in data.get(kind,[]):
                    if isinstance(deal,dict):
                        row=normalize(deal,retailer,kind)
                        if row:rows.append(row)
            unique={}
            for row in rows:
                key=(row["store"],row["text"].casefold(),row.get("price"))
                if key not in unique:unique[key]=row
            result=list(unique.values())
            counts[retailer]=len(result)
            offers.extend(result)
            print(f"{retailer}: {len(result)} aanbiedingen",flush=True)
            time.sleep(1)
        except Exception as exc:
            failures.append({"store":retailer,"reason":str(exc)[:250]})
            print(f"{retailer}: FOUT {exc}",flush=True)
    # Never claim completed when primary chains failed.
    if any(counts.get(r,0)==0 for r in ("albert_heijn","jumbo","lidl")):
        raise SystemExit("Essentiële supermarkten missen gegevens. Diagnostiek: "+json.dumps({"counts":counts,"failures":failures},ensure_ascii=False))
    offers.sort(key=lambda x:(x.get("savings_percentage") or 0),reverse=True)
    now=datetime.now(timezone.utc).isoformat()
    old={}
    path=ROOT/"data"/"latest.json"
    if path.exists():
        try:old=json.loads(path.read_text())
        except (OSError,ValueError):pass
    report={"scanned_at":now,"folders":old.get("folders",[]),
            "offers":offers,"recipes":recipe_suggestions(offers),
            "stats":{"source":"PrijsProfeet openbare API","offer_entries":len(offers),
                     "retailers_with_offers":len(counts),"per_store":counts,
                     "failed_retailers":failures,"status":"live_api"},
            "errors":[str(e) for e in failures],
            "quality_notice":"Aanbiedingen via PrijsProfeet (prijsprofeet.nl). Actieprijzen zijn indicatief. Geen complete prijsvergelijking van reguliere assortimenten."}
    watchlist=ROOT/"data"/"watchlist.json"
    if watchlist.exists():
        try:report["watchlist"]=json.loads(watchlist.read_text())
        except (OSError,ValueError):pass
    render(report)
    print(json.dumps(report["stats"],ensure_ascii=False),flush=True)

if __name__=="__main__":main()
