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
    """Controleer alleen dezelfde verpakking en een sterk overeenkomende naam.

    Checkjebon gebruikt soms een andere merkprefix dan PrijsProfeet. Een aanbieding
    hoeft niet exact dezelfde huidige schapprijs te hebben; de opgegeven
    oorspronkelijke prijs is de beste aanvullende kwaliteitscontrole.
    """
    hits=[]
    sn=shelf["norm"]
    for offer in offer_list:
        if shelf["unit"]!=offer["unit"] or shelf["quantity"]!=offer["quantity"]:continue
        if offer.get("is_loyalty"):continue
        original=offer.get("original_price")
        if not original or abs(original-shelf["price"])/max(shelf["price"],.01)>.30:continue
        on=offer["norm"]
        similarity=SequenceMatcher(None,sn,on).ratio()
        # Exacte itemnaam met prefixverschil is toegestaan, geen generieke
        # ingrediëntfuzzy-match. Bijvoorbeeld Lidl "Gewassen spinazie" tegenover
        # Checkjebon "Spinazie".
        stop={"ah","jumbo","lidl","de","het","een","gram","gr","g","kg","ml","l","liter","bio","biologisch","vers","original","origineel","pak","zak","doos"}
        ss={t for t in sn.split() if t not in stop and not t.isdigit()}
        os={t for t in on.split() if t not in stop and not t.isdigit()}
        # Vereis hetzelfde inhoudelijke productwoord; alleen merk, gewicht of
        # winkelnaam matchen is niet genoeg (tomatenblokjes != cherrytomaten).
        if not (ss & os):continue
        overlap=len(ss&os)/max(len(ss),len(os))>=.66
        safe_single=(len(ss)==1 and ss.issubset(os) and len(os)<=2) or (len(os)==1 and os.issubset(ss) and len(ss)<=2)
        if similarity<.90 and not overlap and not safe_single:continue
        hits.append((similarity,offer))
    if not hits:return None
    return sorted(hits,key=lambda x:(x[0],x[1].get("discount") or 0),reverse=True)[0][1]

def offer_price(ing,amount,unit,offers):
    """Actieartikel zelf als bron als de normale dataset de variant niet bevat.

    Alleen simpele individuele actieprijzen met exact bekende maatvoering.
    Voor complexe combinaties/bonuskaarten wordt geen kassaprijs verzonnen.
    """
    options=[]
    for o in offers:
        if o["unit"]!=unit or not o["quantity"] or not match_ingredient(o,ing):continue
        if o.get("is_loyalty"):continue
        typ=normalize(o.get("promotion_type",""))
        if o.get("multi_buy_quantity") or any(z in typ for z in ("multi","one_plus_one","gratis","bundle","voor","2 1","1 1")):continue
        original=o.get("original_price")
        if original is not None and original<=o["price"]:continue
        n=math.ceil(amount/o["quantity"])
        if n>15:continue
        cost=round(n*o["price"],2)
        options.append((cost,{"key":ing,"label":ING[ing][0],"required":amount,"unit":unit,
             "product":o["name"],"package":o["size_label"] or (str(o["quantity"])+" "+unit),
             "package_size":o["quantity"],"packages":n,"cash_price":cost,
             "used_price":round(amount/o["quantity"]*o["price"],2),
             "regular_cash":round(n*(original or o["price"]),2),"sale":True,
             "action":{"name":o["name"],"price":o["price"],"valid_until":o.get("valid_until"),
                 "multi_buy_quantity":None,"multi_buy_price":None,"url":o["url"]},
             "source":"PrijsProfeet","url":o["url"]}))
    return [x[1] for x in sorted(options,key=lambda x:x[0])]

def ingredient_price(ing,amount,unit,shelves,offers):
    options=[]
    for p in shelves:
        if p["unit"]!=unit or not match_ingredient(p,ing):continue
        if unit=="g" and p["quantity"]>5000:continue
        if unit=="ml" and p["quantity"]>4000:continue
        if unit=="st" and p["quantity"]>30:continue
        n=math.ceil(amount/p["quantity"])
        if n>20:continue
        regular=round(n*p["price"],2)
        promo=promo_for(p,offers)
        cost,packs=total_for(n,p["price"],promo)
        if cost>=regular:
            cost,packs,promo=regular,n,None
        used=round(amount/p["quantity"]*(cost/packs),2) if packs else None
        options.append({"key":ing,"label":ING[ing][0],"required":amount,"unit":unit,
                       "product":p["name"],"package":p["size_label"],"package_size":p["quantity"],
                       "packages":packs,"cash_price":cost,"used_price":used,"regular_cash":regular,
                       "sale":bool(promo),"action":promo and {"name":promo["name"],"price":promo["price"],
                         "valid_until":promo.get("valid_until"),"multi_buy_quantity":promo.get("multi_buy_quantity"),
                         "multi_buy_price":promo.get("multi_buy_price"),"url":promo["url"]},
                       "source":("PrijsProfeet + Checkjebon" if promo else "Checkjebon"),
                       "url":p["url"]})
    options.extend(offer_price(ing,amount,unit,offers))
    if not options:return None
    # Prioriteit bij boodschappen blijft lage prijs; bij beperkte meerkosten
    # mag een echte actie winnen. Vergelijk feitelijke kassakosten, geen opgeblazen
    # kortingspercentage ten opzichte van een dure adviesprijs.
    minimum=min(x["cash_price"] for x in options)
    preferred=[x for x in options if x["sale"] and x["cash_price"]<=minimum*1.12]
    if preferred:
        preferred.sort(key=lambda x:(x["cash_price"],-max(0,x["regular_cash"]-x["cash_price"])))
        return preferred[0]
    return min(options,key=lambda x:(x["cash_price"],x["used_price"]))


def nutrition_profile(ings):
    """Conservatieve receptscreening, géén voedingswaarde-analyse.

    Eiwitrijk betekent hier een substantiële zichtbare eiwitbron.
    Relatief koolhydraatarm betekent een beperkte portie zetmeelbron.
    Dit is dus geen bewezen gram/portie of medisch voedingsadvies.
    """
    amounts={key:float(qty) for key,qty,unit in ings}
    protein_sources={
       "kipfilet":125,"kipdij":125,"kipgehakt":125,"shoarma":125,
       "gehakt":125,"zalm":125,"gerookte_zalm":70,"tonijn":70,
       "tofu":150,"eieren":2,"kikkererwten":160,"linzen":160,"bonen":160,
    }
    protein_cues=[key for key,limit in protein_sources.items() if amounts.get(key,0)>=limit*4]
    # Geen exacte eiwitclaim mogelijk zonder voedingswaardetabel, maar wel aanwijzing.
    protein=bool(protein_cues)
    dry_starches=("rijst","pasta","couscous")
    dense_starches=("aardappel","zoete_aardappel")
    dry_per_portion=sum(amounts.get(key,0) for key in dry_starches)/4
    potato_per_portion=sum(amounts.get(key,0) for key in dense_starches)/4
    breads_per_portion=sum(amounts.get(key,0) for key in ("wraps","naan"))/4
    lowish_carb=dry_per_portion<=45 and potato_per_portion<=200 and breads_per_portion<=1
    vegetables=("wok","spinazie","broccoli","bloemkool","paprika","courgette",
                "champignons","tomaten","tomatenblokjes","ui","komkommer","wortel",
                "sla","spruiten","boerenkool")
    # Producten per stuk niet naar grammen omrekenen zonder gewichtsbron.
    veg_g=sum(amounts.get(key,0) for key in vegetables if key not in ("paprika","courgette","komkommer","bloemkool"))
    veg_pieces=sum(amounts.get(key,0) for key in ("paprika","courgette","komkommer","bloemkool"))
    vegetables_present=veg_g>=500 or (veg_g>=280 and veg_pieces>=1) or veg_pieces>=3
    priority=protein and lowish_carb and vegetables_present
    return {"priority":priority,"protein_source":protein,
            "lower_carb":lowish_carb,"vegetable_forward":vegetables_present,
            "protein_cues":protein_cues,
            "basis":"Indicatie uit ingrediënten en hoeveelheden, niet berekende voedingswaarden"}

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
            nutrition=nutrition_profile(ings)
            inspiration=("HelloFresh-variant" if title.startswith("HelloFresh-geïnspireerd:")
                         else "Mealprep-variant" if title.startswith("Mealprep:")
                         else "Eigen recept")
            all_recipes.append({"id":str(idx+1),"title":title,"category":category,"minutes":minutes,
              "inspiration":inspiration, "mealprep":title.startswith("Mealprep:") or minutes>=30,
              "nutrition":nutrition,
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
        # Bewaar de volledige receptenbibliotheek. De website toont standaard
        # de sterkste acties, maar laat ook vlees, vis en vega zonder actie zien.
        # Deze gerechten mogen nooit als actie worden aangeduid.
        final[store]=all_recipes
    return final

def export_shopping_index(shelves,offers):
    """Compacte echte online winkelprijzen voor een lokale boodschappenchat.

    De index bevat schapprijzen plus de nog geldige actieproducten, zonder
    fictieve fallback. Browser ontvangt nooit API-credentials.
    """
    result={}
    for store in STORES:
        ordinary=[]
        for p in shelves[store]:
            ordinary.append([p["name"],p["price"],p["quantity"],p["unit"],p.get("url","")])
        promos=[]
        for p in offers[store]:
            if not p.get("quantity") or not p.get("unit"):continue
            promos.append([p["name"],p["price"],p["quantity"],p["unit"],
                p.get("original_price"),p.get("multi_buy_quantity"),
                p.get("multi_buy_price"),p.get("promotion_type",""),
                p.get("valid_until"),p.get("url",""),p.get("is_loyalty",False)])
        result[store]={"ordinary":ordinary,"promotions":promos}
    path=ROOT/"recepten"/"winkelprijzen.json"
    temp=path.with_suffix(".tmp")
    temp.write_text(json.dumps({"updated_at":datetime.now(TZ).isoformat(),
        "source":"Checkjebon en PrijsProfeet","stores":result},
        ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    temp.replace(path)

def main():
    errors=[]
    shelves,last_modified,counts=load_shelves()
    if not any(counts.values()):
        raise RuntimeError("Geen reguliere prijzen terug uit Checkjebon: geen misleidende lege publicatie")
    offers,errors=load_deals()
    export_shopping_index(shelves,offers)
    result={"updated_at":datetime.now(TZ).isoformat(),"shelf_source_modified":last_modified,
            "sources":{"ordinary":"Checkjebon open dataset","promotions":"PrijsProfeet gratis aanbiedingen-API"},
            "source_links":{"ordinary":"https://github.com/supermarkt/checkjebon",
                            "promotions":"https://www.prijsprofeet.nl"},
            "store_names":STORES,"counts":{"ordinary":counts,"promotions":{s:len(offers[s]) for s in STORES}},
            "recipes":make_recipes(shelves,offers),
            "deals":{s:sorted(offers[s],key=lambda d:-(d.get("discount") or 0)) for s in STORES},
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
