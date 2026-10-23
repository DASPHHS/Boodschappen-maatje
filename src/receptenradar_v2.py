"""Koopkracht Receptenradar v2.

Combineert Checkjebon (normale online schapprijzen) met PrijsProfeet
(actuele promoties). Geen geschatte productprijzen en geen fictieve fallback.
"""
import json, math, os, re, sys, time, unicodedata
from datetime import datetime, date, timezone
from difflib import SequenceMatcher
from pathlib import Path
from zoneinfo import ZoneInfo
import requests
from receptenradar_catalog import ING, RECIPES

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"recepten"/"data.json"
SHELVES="https://raw.githubusercontent.com/supermarkt/checkjebon/main/data/supermarkets.json"
DEALS="https://www.prijsprofeet.nl/api/v1/products/promotional/all"
HEADERS={"User-Agent":"KoopkrachtRecepten/2.0 (+https://github.com/DASPHHS/koopkracht)","Accept":"application/json"}
KEY=os.getenv("PRIJS_PROFEET_KEY")
if KEY: HEADERS["X-API-Key"]=KEY
STORES={"ah":"Albert Heijn","jumbo":"Jumbo","lidl":"Lidl"}
TZ=ZoneInfo("Europe/Amsterdam")

_next_request_at=0.0
def fetch(url,params=None,tries=9):
    global _next_request_at
    last_error=None
    for attempt in range(tries):
        try:
            if "prijsprofeet.nl" in url:
                wait=max(0,_next_request_at-time.monotonic())
                if wait:time.sleep(wait)
                # Snelheidslimiet voor bulk-endpoints: geen API-key vereist.
                _next_request_at=time.monotonic()+2.9
            r=requests.get(url,params=params,headers=HEADERS,timeout=30)
            if r.status_code==429:
                delay=min(110,max(8,int(r.headers.get("Retry-After","65"))))
                last_error=f"PrijsProfeet HTTP 429, retry after {delay}s, URL {r.url}"
                print(last_error,flush=True)
                time.sleep(delay)
                continue
            if r.status_code in (500,502,503,504):
                last_error=f"HTTP {r.status_code} {r.url}"
                time.sleep(min(40,2**attempt))
                continue
            if not r.ok:
                raise RuntimeError(f"HTTP {r.status_code}, URL {r.url}, respons {r.text[:170]}")
            return r
        except (requests.RequestException,ValueError) as ex:
            last_error=f"{type(ex).__name__}: {str(ex)[:200]}"
            if attempt<tries-1:time.sleep(min(30,3+2**attempt))
        except RuntimeError:raise
    raise RuntimeError(last_error or "Geen geldige API-respons")

def num(x):
    try:
        v=float(str(x).replace(",","."))
        return v if math.isfinite(v) and v>0 else None
    except (TypeError,ValueError): return None

def normalize(text):
    t=unicodedata.normalize("NFKD",str(text).lower())
    t="".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+"," ",re.sub(r"[^\w\s]"," ",t)).strip()

def measure(text):
    """Hoeveelheid per VERPAKKING; onbekend blijft onbekend."""
    s=str(text or "").lower().replace(",",".")
    # 4x125 gram of 2 x 1 l
    x=re.search(r"(\d+)\s*[x×]\s*(\d+(?:\.\d+)?)\s*(kg|gram|gr|g|liter|l|ml|cl)\b",s)
    if x:
        q=float(x.group(1))*float(x.group(2));unit=x.group(3)
    else:
        x=re.search(r"(\d+(?:\.\d+)?)\s*(kg|gram|gr|g|liter|ml|cl|l|stuks|st|stuk|stukken)\b",s)
        if x: q=float(x.group(1));unit=x.group(2)
        elif "per stuk" in s or s.strip() in ("stuk","st"): return (1,"st")
        else:return (None,None)
    if unit=="kg":return (q*1000,"g")
    if unit in ("gram","gr","g"):return (q,"g")
    if unit in ("liter","l"):return (q*1000,"ml")
    if unit=="cl":return(q*10,"ml")
    if unit=="ml":return(q,"ml")
    return(q,"st")

def store_code(x):
    n=normalize(x).replace(" ","")
    if n in ("ah","albertheijn","albert_heijn"):return "ah"
    if n.startswith("jumbo"):return "jumbo"
    if n.startswith("lidl"):return "lidl"
    return None

def load_shelves():
    response=fetch(SHELVES)
    payload=response.json()
    if not isinstance(payload,list): raise ValueError("Checkjebon-dataset is geen lijst")
    prices={s:[] for s in STORES}
    for store in payload:
        code=store_code(store.get("n",""))
        if not code: continue
        base=store.get("u") or ""
        for item in store.get("d",[]):
            if not isinstance(item,dict):continue
            cost=num(item.get("p"))
            size,unit=measure(item.get("s") or "")
            label=str(item.get("n") or "")
            if not label or not cost or not size or not unit:continue
            link=(base+str(item["l"])) if item.get("l") else ""
            prices[code].append({"name":label,"norm":normalize(label),"price":cost,"quantity":size,
                                 "unit":unit,"size_label":item.get("s") or "","url":link,"source":"Checkjebon"})
    return prices,response.headers.get("Last-Modified"),{s:len(rows) for s,rows in prices.items()}

def load_deals():
    offers={s:[] for s in STORES}
    errors=[]
    today=datetime.now(TZ).date().isoformat()
    for store,slug in (("ah","albert_heijn"),("jumbo","jumbo"),("lidl","lidl")):
        try:
            page=1;seen=set()
            while page<=100:
                response=fetch(DEALS,{"retailer":slug,"page":page,"page_size":100})
                data=response.json()
                rows=data.get("results") or data.get("products") or data.get("items") or []
                if not isinstance(rows,list):raise ValueError("Onbekend PrijsProfeet-resultaatformaat")
                for r in rows:
                    if not isinstance(r,dict):continue
                    status=r.get("promotion_status")
                    start=str(r.get("valid_from") or "")[:10]
                    until=str(r.get("valid_until") or "")[:10]
                    if status not in (None,"active") or (start and start>today) or (until and until<today):continue
                    if store_code(r.get("retailer",slug))!=store:continue
                    name=str(r.get("name") or "").strip()
                    price=num(r.get("price"))
                    if not name or not price:continue
                    key=str(r.get("id") or (name+str(price)))
                    if key in seen:continue
                    seen.add(key)
                    size,unit=measure(r.get("quantity") or r.get("size") or name)
                    offers[store].append({
                       "name":name,"norm":normalize(name),"price":price,"quantity":size,"unit":unit,
                       "size_label":str(r.get("quantity") or r.get("size") or ""),
                       "original_price":num(r.get("original_price")),
                       "multi_buy_quantity":num(r.get("multi_buy_quantity")),
                       "multi_buy_price":num(r.get("multi_buy_price")),
                       "promotion_type":str(r.get("promotion_type") or ""),
                       "valid_until":until,"valid_from":start,
                       "discount":num(r.get("savings_percentage")) or num(r.get("discount_percentage")),
                       "url":r.get("url") or r.get("product_url") or "https://www.prijsprofeet.nl",
                       "ean":str(r.get("ean") or ""),"source":"PrijsProfeet",
                       "is_loyalty":bool(r.get("loyalty_price"))})
                total=data.get("total")
                if not rows or len(rows)<100 or (isinstance(total,int) and page*100>=total):break
                page+=1
                time.sleep(.12)
            if page==100:errors.append(f"{store}: boven paginalimiet, acties mogelijk onvolledig")
        except Exception as e:
            errors.append(f"{store}: {type(e).__name__}: {str(e)[:180]}")
    return offers,errors

def match_ingredient(product,ingredient):
    label,pattern,exclude=ING[ingredient]
    name=product["norm"]
    return bool(re.search(pattern,name,re.I)) and not bool(re.search(exclude,name,re.I))

def total_for(n,unit_price,promo=None):
    if not promo:return round(n*unit_price,2),n
    k=promo.get("multi_buy_quantity")
    kprice=promo.get("multi_buy_price")
    if k and k>=2 and kprice:
        k=int(k)
        # Inclusief onvermijdelijke extra verpakkingen als bundel voordeliger is.
        options=[]
        for qty in (n,max(n,math.ceil(n/k)*k)):
            packages=qty//k
            base=promo.get("original_price") or unit_price
            amount=round(packages*kprice+(qty%k)*base,2)
            options.append((amount,qty))
        return min(options)
    # Geen expliciet leesbare bundel = prijs slechts overnemen wanneer aanbieding
    # NIET via onbetrouwbare 1+1- of meer-voor-actiecondities loopt.
    ptype=normalize(promo.get("promotion_type",""))
    if any(x in ptype for x in ("1 1","2 1","3 2","gratis","multi","bundle","voor")):
        return round(n*unit_price,2),n
    return round(n*promo["price"],2),n

def promo_for(shelf,offer_list):
    """Gebruik alleen aanbod bij nagenoeg identieke productnaam, exacte verpakking en referentieprijs."""
    hits=[]
    for offer in offer_list:
        if shelf["unit"]!=offer["unit"] or shelf["quantity"]!=offer["quantity"]:continue
        similarity=SequenceMatcher(None,shelf["norm"],offer["norm"]).ratio()
        if similarity<.92:continue
        original=offer.get("original_price")
        if original is None or abs(original-shelf["price"])/shelf["price"]>.18:continue
        if offer.get("is_loyalty"):continue # speciale ledenvoorwaarde alleen in dealslijst
        hits.append((similarity,offer))
    if not hits:return None
    return max(hits,key=lambda x:x[0])[1]

def ingredient_price(ing,amount,unit,shelves,offers):
    options=[]
    for p in shelves:
        if p["unit"]!=unit or not match_ingredient(p,ing):continue
        # Uitgesproken afwijkende hoeveelheden in de productcatalogus vermijden
        if unit=="g" and p["quantity"]>5000:continue
        if unit=="ml" and p["quantity"]>4000:continue
        if unit=="st" and p["quantity"]>30:continue
        n=math.ceil(amount/p["quantity"])
        if n>20:continue
        regular=round(n*p["price"],2)
        promo=promo_for(p,offers)
        cost,packs=total_for(n,p["price"],promo)
        # Actie is niet noodzakelijk goedkoper bij een vereiste bundel
        if cost>=regular:
            cost,packs,promo=regular,n,None
        used=round(amount/p["quantity"]*(cost/packs),2) if packs else None
        options.append((cost,used,{"key":ing,"label":ING[ing][0],"required":amount,"unit":unit,
                       "product":p["name"],"package":p["size_label"],"package_size":p["quantity"],
                       "packages":packs,"cash_price":cost,"used_price":used,"regular_cash":regular,
                       "sale":bool(promo),"action":promo and {"name":promo["name"],"price":promo["price"],
                         "valid_until":promo.get("valid_until"),"multi_buy_quantity":promo.get("multi_buy_quantity"),
                         "multi_buy_price":promo.get("multi_buy_price"),"url":promo["url"]},
                       "source":("PrijsProfeet + Checkjebon" if promo else "Checkjebon"),
                       "url":p["url"]}))
    if not options:return None
    # Optimaliseer kassaprijs, bij gelijkspel de kleinste verspillingswaarde.
    options.sort(key=lambda x:(round(x[0],2),round(x[1],2)))
    return options[0][2]

def make_recipes(shelves,offers):
    final={}
    for store in STORES:
        all_recipes=[]
        for idx,(title,category,minutes,ings) in enumerate(RECIPES):
            lines=[];missing=[];discounts=0
            for key,amount,unit in ings:
                line=ingredient_price(key,amount,unit,shelves[store],offers[store])
                if line:
                    lines.append(line)
                    discounts+=bool(line["sale"])
                else:
                    missing.append({"label":ING[key][0],"amount":amount,"unit":unit})
            complete=len(missing)==0 and bool(lines)
            checkout=round(sum(x["cash_price"] for x in lines),2)
            consumed=round(sum(x["used_price"] for x in lines),2)
            saving=round(sum(max(0,x["regular_cash"]-x["cash_price"]) for x in lines),2)
            all_recipes.append({"id":str(idx+1),"title":title,"category":category,"minutes":minutes,
              "servings":4,"ingredient_count":len(ings),"sale_count":discounts,
              "covered_count":len(lines),"complete":complete,
              "checkout":checkout if complete else None,"known_subtotal":checkout,
              "used_total":consumed if complete else None,
              "per_serving":round(consumed/4,2) if complete else None,
              "saving":saving,"ingredients":lines,"missing":missing,
              "optional_pantry":"Olie, zout, peper en kruiden naar smaak (niet in prijs inbegrepen)."})
        # Beste ACTIECOMBINATIES voorop, daarbinnen kleinste complete prijs per portie.
        all_recipes.sort(key=lambda r:(-r["sale_count"],not r["complete"],
                                    r["per_serving"] if r["per_serving"] is not None else 1e7,
                                    r["minutes"]))
        # Niet vijftien variaties dezelfde eiwitbron tonen: verdeel categorieën.
        selected=[];counts={}
        for recipe in all_recipes:
            if counts.get(recipe["category"],0)>=6:continue
            selected.append(recipe);counts[recipe["category"]]=counts.get(recipe["category"],0)+1
            if len(selected)==15:break
        final[store]=selected
    return final

def main():
    errors=[]
    shelves,last_modified,counts=load_shelves()
    if not any(counts.values()):
        raise RuntimeError("Geen reguliere prijzen terug uit Checkjebon: geen misleidende lege publicatie")
    offers,errors=load_deals()
    result={"updated_at":datetime.now(TZ).isoformat(),"shelf_source_modified":last_modified,
            "sources":{"ordinary":"Checkjebon open dataset","promotions":"PrijsProfeet gratis aanbiedingen-API"},
            "source_links":{"ordinary":"https://github.com/supermarkt/checkjebon",
                            "promotions":"https://www.prijsprofeet.nl"},
            "store_names":STORES,"counts":{"ordinary":counts,"promotions":{s:len(offers[s]) for s in STORES}},
            "recipes":make_recipes(shelves,offers),
            "deals":{s:sorted(offers[s],key=lambda d:-(d.get("discount") or 0))[:180] for s in STORES},
            "errors":errors,
            "disclaimer":"Online prijzen indicatief. Kassaprijzen zijn berekend uit beschikbare verpakkingen. Kruiden/olie uit voorraad en eventuele persoonlijke coupons niet inbegrepen. Geen garantie op winkelvoorraad."}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    tmp=OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(result,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    tmp.replace(OUT)
    print(json.dumps({"shelf":counts,"offers":result["counts"]["promotions"],
                      "fully_priced_recipes":{s:sum(r["complete"] for r in result["recipes"][s]) for s in STORES},
                      "errors":errors},ensure_ascii=False))
if __name__=="__main__":main()
