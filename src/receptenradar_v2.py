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
from receptenradar_catalog import ING, RECIPES, RECIPE_METHODS, validate_dish_ingredients
from receptkwaliteit import pantry_for_recipe, cooking_instructions, dish_quality_issues
from receptenradar_checks import validate_publication
from actie_maaltijden import meal_candidates, DISH_BY_KEYS, DISH_TEMPLATES

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

def measure_offer(offer):
    """Lees de eerste bruikbare hoeveelheid mét eenheid, ook bij numerieke API-velden."""
    for value in (offer.get("quantity"),offer.get("size"),offer.get("name")):
        quantity,unit=measure(value)
        if quantity and unit:
            return quantity,unit
    return None,None

def offer_size_label(product,quantity,unit):
    """Presenteer altijd de gemeten maat met eenheid, ook bij numerieke API-velden."""
    for field in ("quantity","size"):
        value=product.get(field)
        if measure(value)==(quantity,unit) and isinstance(value,str):
            return value.strip()
    return f"{int(quantity) if float(quantity).is_integer() else quantity} {unit}" if quantity else "Onbekend"

def verified_discount(offer):
    """Alleen numeriek controleerbaar prijsvoordeel verdient een kortingsbadge."""
    if offer.get("is_loyalty"):
        return False
    price=offer.get("price") or 0
    old=offer.get("original_price") or 0
    count=offer.get("multi_buy_quantity") or 0
    bundle=offer.get("multi_buy_price") or 0
    if count>=2 and bundle>0:
        return bundle<count*(old or price)
    # Een incomplete meerstuksactie is géén aantoonbare individuele korting.
    promotion=normalize(offer.get("promotion_type") or "")
    if any(term in promotion for term in ("gratis","one_plus_one","multi","bundle",
                                           "1 1","2 1","3 2")) or re.search(
                                               r"\b\d+\s+voor\b",promotion):
        return False
    return old>price>0

def verified_discount_percentage(offer):
    if not verified_discount(offer):
        return None
    price=offer.get("price") or 0
    old=offer.get("original_price") or price
    count=offer.get("multi_buy_quantity") or 0
    bundle=offer.get("multi_buy_price") or 0
    if count>=2 and bundle>0:
        return round(100*(1-bundle/(count*old)),1)
    return round(100*(1-price/old),1)

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
                    size,unit=measure_offer(r)
                    offers[store].append({
                       "name":name,"norm":normalize(name),"price":price,"quantity":size,"unit":unit,
                       "size_label":offer_size_label(r,size,unit),
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
    # Aanvulling uit officiële Jumbo-aanbiedingspagina, gecontroleerd op
    # 23 oktober 2026; expliciete einddatum conservatief t/m 27 oktober.
    # Deze tijdelijke correctie is nodig omdat de bulkfeed sommige
    # Kies & Mix-campagnes niet aanlevert. Niet automatisch verlengen.
    if today<="2026-10-27" and not any(
       "jumbo kipburgers" in p["norm"] and p.get("multi_buy_quantity")==2
       for p in offers["jumbo"]):
        offers["jumbo"].append({
          "name":"Jumbo Kipburgers 250 g","norm":"jumbo kipburgers 250 g",
          "price":3.59,"quantity":250.0,"unit":"g","size_label":"250 g",
          "original_price":3.59,"multi_buy_quantity":2.0,
          "multi_buy_price":6.0,"promotion_type":"Kies & Mix 2 voor 6",
          "valid_from":"2026-01-07","valid_until":"2026-10-27",
          "discount":16.4,
          "url":"https://www.jumbo.com/aanbiedingen/hamburgers/3013651",
          "ean":"","source":"Jumbo officiële aanbiedingspagina (handmatig geverifieerd)",
          "is_loyalty":False})
    # Tijdelijke, officieel gecontroleerde Jumbo-schappromoties 21-27 okt.
    # De bulkfeed mist soms categorie-acties; de einddatum voorkomt dat de
    # handmatige aanvulling na deze week als actuele korting blijft staan.
    if "2026-10-21"<=today<="2026-10-27":
        verified=[
          {"name":"Jumbo Varkenshaas Culinair 1 Stuk ca. 405 g",
           "price":4.82,"quantity":405,"unit":"g","size_label":"ca. 405 g",
           "original_price":6.74,"multi_buy_quantity":None,"multi_buy_price":None,
           "promotion_type":"€ 1,19 per 100 gram","discount":28.5,
           "url":"https://www.jumbo.com/aanbiedingen/varkenshaas-of-beenham-culinair/3021340"},
          {"name":"Jumbo Minikrieltjes 600 g",
           "price":1.19,"quantity":600,"unit":"g","size_label":"600 g",
           "original_price":1.19,"multi_buy_quantity":2,"multi_buy_price":1.99,
           "promotion_type":"2 voor € 1,99","discount":16.4,
           "url":"https://www.jumbo.com/aanbiedingen/jumbo-minikrieltjes-aardappelschijfjes-of-opbakaardapppeltjes/3021433"},
          # Jumbo-site 21–27 oktober: Campina naturel 1 kg 3,49 -> 2,49.
          {"name":"Campina Magere Milde Kwark Naturel Voordeelpak 1 kg",
           "price":2.49,"quantity":1000,"unit":"g","size_label":"1 kg",
           "original_price":3.49,"multi_buy_quantity":None,"multi_buy_price":None,
           "promotion_type":"voor € 2,49","discount":28.7,
           "url":"https://www.jumbo.com/aanbiedingen/nu/actieprijs_20261021-20261027"},
          # Officiële Jumbo-campagne: Jumbo Nederlandse Aardbeien 400 g
          # reguliere productprijs 3,99, 25% korting aan de kassa.
          {"name":"Jumbo Nederlandse Aardbeien 400 g",
           "price":2.99,"quantity":400,"unit":"g","size_label":"400 g",
           "original_price":3.99,"multi_buy_quantity":None,"multi_buy_price":None,
           "promotion_type":"25% korting","discount":25.0,
           "url":"https://www.jumbo.com/aanbiedingen/frambozen-of-nederlandse-aardbeien/3022919"},
          {"name":"Jumbo Bloemkool",
           "price":0.99,"quantity":1,"unit":"st","size_label":"per stuk",
           "original_price":1.69,"multi_buy_quantity":None,"multi_buy_price":None,
           "promotion_type":"vaste prijs","discount":41.4,
           "url":"https://www.jumbo.com/aanbiedingen/bloemkool/3022996"},
        ]
        for item in verified:
            # Eén en hetzelfde product niet dubbel opnemen.
            if any(normalize(o["name"])==normalize(item["name"]) and
                    o.get("multi_buy_quantity")==item["multi_buy_quantity"]
                    for o in offers["jumbo"]):
                continue
            item.update({"norm":normalize(item["name"]),"valid_from":"2026-10-21",
                         "valid_until":"2026-10-27","ean":"",
                         "source":"Jumbo officiële campagnepagina","is_loyalty":False})
            offers["jumbo"].append(item)
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
    if any(x in ptype for x in ("1 1","2 1","3 2","gratis","multi","bundle")) or re.search(r"\b\d+\s+voor\b",ptype):
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
        if o.get("is_loyalty") or not verified_discount(o):continue
        typ=normalize(o.get("promotion_type",""))
        is_bundle=bool(o.get("multi_buy_quantity") and o.get("multi_buy_price"))
        if not is_bundle and any(z in typ for z in ("multi","one_plus_one","gratis","bundle","2 1","1 1")):continue
        original=o.get("original_price")
        # Bij 2-voor-acties blijft de getoonde losse stukprijs vaak gelijk
        # aan de normale prijs; controleer daarom de TOTALE bundelkorting.
        if is_bundle:
            k=o["multi_buy_quantity"]
            if k<2 or o["multi_buy_price"]>=k*(original or o["price"]):continue
        elif original is not None and original<=o["price"]:
            continue
        n=math.ceil(amount/o["quantity"])
        if n>15:continue
        cost,packs=total_for(n,original or o["price"],o)
        if is_bundle and cost>=round(n*(original or o["price"]),2):continue
        options.append((cost,{"key":ing,"label":ING[ing][0],"required":amount,"unit":unit,
             "product":o["name"],"package":o["size_label"] or (str(o["quantity"])+" "+unit),
             "package_size":o["quantity"],"packages":packs,"cash_price":cost,
             "used_price":round(amount/o["quantity"]*(cost/packs),2),
             "regular_cash":round(n*(original or o["price"]),2),"sale":True,
             "action":{"name":o["name"],"price":o["price"],"valid_until":o.get("valid_until"),
                 "multi_buy_quantity":o.get("multi_buy_quantity"),"multi_buy_price":o.get("multi_buy_price"),"url":o["url"]},
             "source":"PrijsProfeet","url":o["url"],**product_context(o,ing)}))
    return [x[1] for x in sorted(options,key=lambda x:x[0])]

def alternative_offers(ingredient,amount,unit,offers,selected,limit=3,fresh_only=False):
    """Echte kortingsopties naast het goedkoopste gekozen product.

    De opties beïnvloeden de daadwerkelijke kassaprijs niet en worden niet
    onterecht meegerekend als gebruikte actie.
    """
    choices=offer_price(ingredient,amount,unit,offers)
    if fresh_only:
        choices=[x for x in choices if not x.get("frozen")]
    alternatives=[]
    for candidate in choices:
        if selected and candidate["sale"] and normalize(candidate["product"])==normalize(selected["product"]):
            continue
        # Prevent duplicate presentations for the same product/pack.
        if any(normalize(a["product"])==normalize(candidate["product"]) for a in alternatives):
            continue
        alternatives.append({
            "product":candidate["product"],"cash_price":candidate["cash_price"],
            "packages":candidate["packages"],"package":candidate["package"],
            "valid_until":candidate["action"].get("valid_until"),
            "url":candidate["url"],
            "more_expensive_than_selected":bool(
                selected and candidate["cash_price"]>selected["cash_price"]+.001)
        })
        if len(alternatives)>=limit:break
    return alternatives

def product_context(product,ingredient):
    """Kenmerken van aangeboden alternatieven; geen onbewezen voedingsclaim."""
    name=normalize(product.get("name") or product.get("norm") or "")
    frozen=bool(re.search(r"\b(diepvries|diepgevroren|bevroren|vriesvers|diepvr)\b",name))
    # Een smaakvariant kan suiker en andere voedingswaarden hebben.
    flavoured=(ingredient in ("kwark","yoghurt") and bool(re.search(
        r"\b(aardbei|aardbeien|vanille|bosbes|blauwe bessen|framboos|kersen|perzik|mango|kokos|stracciatella|chocolade|fruit)\b",name)))
    return {"frozen":frozen,"flavoured_dairy":flavoured,
            "nutrition_unverified":flavoured,
            "nutrition_note":("Voedingswaarden van deze smaakvariant zijn nog niet "
                              "van het etiket overgenomen; controleer suiker en eiwit."
                              if flavoured else "")}

def fresh_spinach_required(title,ing):
    """Rauwe spinazie in wraps en salades vereist verse bladeren, geen diepvriesblokjes."""
    name=normalize(title)
    return (ing=="spinazie" and
            any(x in name for x in ("wrap","salade")) and
            not any(x in name for x in ("roerei","eiwrap","ei wraps","warm","frittata")))

def ingredient_price(ing,amount,unit,shelves,offers,fresh_only=False):
    options=[]
    for p in shelves:
        if p["unit"]!=unit or not match_ingredient(p,ing):continue
        if fresh_only and product_context(p,ing)["frozen"]:continue
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
                       "url":p["url"],**product_context(p,ing)})
    promo_options=offer_price(ing,amount,unit,offers)
    options.extend(x for x in promo_options if not fresh_only or not x.get("frozen"))
    if not options:return None
    # De goedkoopste mand is ook echt de laagste kassaprijs.
    # Acties die iets duurder zijn blijven apart zichtbaar als actie-alternatief.
    return min(options,key=lambda x:(x["cash_price"],not x["sale"],x["used_price"]))


# Indicatieve, bewust conservatieve eiwitwaarden van gangbare producten.
# Per 100 g eetbaar product, behalve eieren (g per stuk). Voedingswaarden
# van het GEKOZEN winkelartikel kunnen afwijken. Onbekende ingrediënten
# tellen niet mee, om niet stilzwijgend eiwitten te verzinnen.
PROTEIN_PER_100G={
 "kipfilet":20.0,"kipdij":17.0,"kipgehakt":17.0,"shoarma":16.0,
 "gehakt":17.0,"varkenshaas":20.0,"rookworst":12.0,"zalm":19.0,"gerookte_zalm":18.0,
 "tonijn":22.0,"tofu":10.0,"kikkererwten":6.0,"linzen":6.0,
 "bonen":6.0,"broccoli":2.5,"spinazie":2.3,"boerenkool":2.5,
 "spruiten":2.5,"wok":1.5,"champignons":2.0,"wortel":0.5,
 "tomaten":0.5,"tomatenblokjes":0.7,"ui":0.7,"sla":1.0,
 "rijst":7.0,"risottorijst":7.0,"pasta":11.0,"couscous":11.0,"aardappel":1.5,
 "zoete_aardappel":1.2,"yoghurt":3.5,"kwark":9.0,
 "kaas":20.0,"kokosmelk":1.0,"mais":2.0,
 "havermout":12.0,"banaan":1.0,"blauwe_bessen":0.6,
 "aardbeien":0.7,"noten":18.0,"hummus":6.0
}
PROTEIN_PER_PIECE={"eieren":6.0,"wraps":3.0,"naan":5.0,
                   "bloemkool":12.0,"paprika":1.0,"courgette":2.0,
                   "komkommer":1.0,"avocado":2.0}
# Indicatieve kcal per 100 gram (droge rijst/pasta/couscous; peulvruchten
# uitgelekt; vlees en vis rauw). Waarden variëren per product.
KCAL_PER_100G={
 "kipfilet":110,"kipdij":140,"kipgehakt":155,"shoarma":170,
 "gehakt":190,"varkenshaas":120,"rookworst":280,"zalm":205,"gerookte_zalm":165,
 "tonijn":115,"tofu":125,"kikkererwten":115,"linzen":105,"bonen":105,
 "rijst":355,"risottorijst":360,"pasta":350,"couscous":350,"aardappel":80,
 "zoete_aardappel":85,"wok":35,"boerenkool":35,"spruiten":43,
 "spinazie":25,"broccoli":34,"champignons":25,"tomaten":20,
 "tomatenblokjes":25,"ui":40,"wortel":40,"sla":18,
 "yoghurt":60,"kwark":58,"kaas":350,"kokosmelk":175,
 "mais":95,"havermout":370,"banaan":90,"blauwe_bessen":55,
 "aardbeien":35,"noten":630,"hummus":240
}
# Stukgewichten zijn gemiddelden; geen etiketdata.
KCAL_PER_PIECE={
 "eieren":75,"wraps":125,"naan":240,"bloemkool":175,
 "paprika":45,"courgette":50,"komkommer":35,"avocado":240
}
KCAL_PER_100ML={"kokosmelk":175,"melk":47}
PROTEIN_PER_100ML={"melk":3.5}
MIN_PROTEIN_PER_SERVING=30.0

def nutrition_profile(ings,meal_type="Avondeten"):
    """Conservatieve receptschatting voor vier porties, géén etiketwaardes.

    Onbekende ingrediënten tellen niet mee. "Eiwitrijk" is hier een
    persoonlijke drempel van >=30 g geschat eiwit per portie.
    """
    amounts={key:float(qty) for key,qty,unit in ings}
    protein_total=0.0
    kcal_total=0.0
    kcal_unknown=[]
    unknown=[]
    for key,qty,unit in ings:
        if unit=="g" and key in PROTEIN_PER_100G:
            protein_total+=float(qty)*PROTEIN_PER_100G[key]/100
        elif unit=="st" and key in PROTEIN_PER_PIECE:
            protein_total+=float(qty)*PROTEIN_PER_PIECE[key]
        elif unit=="ml" and key in PROTEIN_PER_100ML:
            protein_total+=float(qty)*PROTEIN_PER_100ML[key]/100
        elif unit=="ml" and key=="kokosmelk":
            protein_total+=float(qty)*0.01
        else:
            unknown.append(key)
    for key,qty,unit in ings:
        if unit=="g" and key in KCAL_PER_100G:
            kcal_total+=float(qty)*KCAL_PER_100G[key]/100
        elif unit=="st" and key in KCAL_PER_PIECE:
            kcal_total+=float(qty)*KCAL_PER_PIECE[key]
        elif unit=="ml" and key in KCAL_PER_100ML:
            kcal_total+=float(qty)*KCAL_PER_100ML[key]/100
        else:
            kcal_unknown.append(key)
    kcal_total=round(kcal_total)
    kcal_per_serving=round(kcal_total/4)
    protein_per_serving=round(protein_total/4,1)
    protein=protein_per_serving>=MIN_PROTEIN_PER_SERVING
    dry_starches=("rijst","risottorijst","pasta","couscous")
    dense_starches=("aardappel","zoete_aardappel")
    dry_per_portion=sum(amounts.get(key,0) for key in dry_starches)/4
    potato_per_portion=sum(amounts.get(key,0) for key in dense_starches)/4
    breads_per_portion=sum(amounts.get(key,0) for key in ("wraps","naan"))/4
    lowish_carb=dry_per_portion<=45 and potato_per_portion<=200 and breads_per_portion<=1
    vegetables=("wok","spinazie","broccoli","bloemkool","paprika","courgette",
                "champignons","tomaten","tomatenblokjes","ui","komkommer","wortel",
                "sla","spruiten","boerenkool")
    # Benadering eetbaar gewicht per stuk, uitsluitend voor persoonlijke
    # filtering. Echte winkelverpakkingen variëren; toon dit als schatting.
    veg_piece_g={"paprika":150,"courgette":280,"komkommer":300,"bloemkool":700}
    vegetable_g=sum(
        qty if unit=="g" else qty*veg_piece_g.get(key,0)
        for key,qty,unit in ings if key in vegetables)
    vegetable_g_per_serving=round(vegetable_g/4)
    vegetables_present=vegetable_g_per_serving>=250
    # Ontbijt: eiwitrijke zuivel/havermout/fruit, zonder groente-eis.
    # Lunch: royaal met groente, maar een iets lichtere portie toegestaan.
    if meal_type=="Ontbijt":
        balanced_breakfast=(amounts.get("kwark",0)>=1000 and
                            (amounts.get("havermout",0)>=120 or
                             amounts.get("banaan",0)>=300 or
                             amounts.get("blauwe_bessen",0)>=250 or
                             amounts.get("aardbeien",0)>=300))
        priority=protein and balanced_breakfast
    elif meal_type=="Lunch":
        priority=protein and vegetable_g_per_serving>=180 and lowish_carb
    else:
        priority=protein and lowish_carb and vegetables_present
    processed_meat=any(key=="rookworst" for key,qty,unit in ings)
    if processed_meat:priority=False
    return {"priority":priority,"protein_source":protein,
            "kcal_per_serving_estimate":kcal_per_serving if not kcal_unknown else None,
            "kcal_total_estimate":kcal_total if not kcal_unknown else None,
            "kcal_unknown":kcal_unknown,
            "protein_g_per_serving_estimate":protein_per_serving,
            "protein_target_g":MIN_PROTEIN_PER_SERVING,
            "meal_type":meal_type,
            "processed_meat":processed_meat,
            "health_note":("Boerenkool is een gezonde groente; rookworst is bewerkt vlees. "
                           "Kies dit af en toe of neem de variant met kip."
                           if processed_meat else ""),
            "protein_unknown":unknown,
            "lower_carb":lowish_carb,"vegetable_forward":vegetables_present,
            "vegetable_g_per_serving_estimate":vegetable_g_per_serving,
            "vegetable_target_g":250,
            "basis":"Indicatieve voedingswaarden uit standaardproducten; olie, kruiden, sauzen en niet vermelde ingrediënten zijn niet meegerekend. Etiketwaarden kunnen afwijken."}

def make_recipes(shelves,offers):
    final={}
    for store in STORES:
        all_recipes=[]
        dynamic=meal_candidates(offers[store])
        proposals=list(RECIPES)+dynamic
        price_cache={}
        for idx,(title,category,minutes,ings) in enumerate(proposals):
            problems=validate_dish_ingredients(title,ings)+dish_quality_issues(title,category,ings)
            if problems:
                raise ValueError("Recept bevat onjuist hoofdingrediënt: "+"; ".join(problems))
            lines=[];missing=[];discounts=0
            for key,amount,unit in ings:
                fresh_only=fresh_spinach_required(title,key)
                cache_key=(key,amount,unit,fresh_only)
                if cache_key not in price_cache:
                    price_cache[cache_key]=ingredient_price(key,amount,unit,shelves[store],offers[store],fresh_only=fresh_only)
                line=price_cache[cache_key]
                if line:
                    lines.append(line)
                    discounts+=bool(line["sale"])
                else:
                    missing.append({"label":ING[key][0],"amount":amount,"unit":unit})
            # Een kortingsartikel kan bestaan zonder dat het de goedkoopste
            # kassa-optie is. Maak deze optie zichtbaar zonder de kassaprijs
            # of het aantal gebruikte acties te vervalsen.
            for line in lines:
                key=line["key"]
                matching=[(k,a,u) for k,a,u in ings if k==key]
                if matching:
                    _,amount,unit=matching[0]
                    line["offer_alternatives"]=alternative_offers(
                        key,amount,unit,offers[store],line,
                        fresh_only=fresh_spinach_required(title,key))
            alternative_count=sum(bool(l.get("offer_alternatives")) for l in lines)
            # Bouw daarnaast een afzonderlijke, volledig doorberekende
            # actiemand. Deze vervangt de goedkoopste mand NIET stilzwijgend.
            deal_lines=[]
            for line in lines:
                alternatives=line.get("offer_alternatives") or []
                if alternatives and not line.get("sale"):
                    original=[(k,a,u) for k,a,u in ings if k==line["key"]][0]
                    candidates=offer_price(original[0],original[1],original[2],offers[store])
                    if fresh_spinach_required(title,original[0]):
                        candidates=[x for x in candidates if not x.get("frozen")]
                    best=min(candidates,key=lambda x:x["cash_price"])
                    deal_lines.append(best)
                else:
                    deal_lines.append({k:v for k,v in line.items() if k!="offer_alternatives"})
            deal_used=sum(bool(l.get("sale")) for l in deal_lines)
            deal_cash=round(sum(l["cash_price"] for l in deal_lines),2)
            deal_extra=round(deal_cash-sum(l["cash_price"] for l in lines),2)
            complete=len(missing)==0 and bool(lines)
            checkout=round(sum(x["cash_price"] for x in lines),2)
            consumed=round(sum(x["used_price"] for x in lines),2)
            saving=round(sum(max(0,x["regular_cash"]-x["cash_price"]) for x in lines),2)
            meal_type=("Ontbijt" if title.startswith("Ontbijt:") else
                       "Lunch" if title.startswith("Lunch:") else "Avondeten")
            nutrition=nutrition_profile(ings,meal_type=meal_type)
            # Bron toont bij natte conserven doorgaans het nettogewicht van de
            # verpakking. Uitlekgewicht is niet algemeen beschikbaar.
            # Benoem dit expliciet: zonder etiket is exact benodigde
            # hoeveelheid en voedingswaarde niet te garanderen.
            drained_uncertain=[ING[key][0] for key,amount,unit in ings
                               if key in ("tonijn","bonen","linzen","kikkererwten")]
            if drained_uncertain:
                nutrition["drained_weight_unverified"]=drained_uncertain
            # Bij gearomatiseerde zuivel is de generieke naturelwaardeschatting
            # onvoldoende voor een betrouwbaar kcal-/eiwitlabel.
            unverified=[x["product"] for x in lines if x.get("nutrition_unverified")]
            if unverified:
                nutrition["product_nutrition_unverified"]=unverified
                nutrition["basis"]+=(" Gearomatiseerde zuivel: etiketwaarden ontbreken. "
                                    "Getoonde eiwit- en kcal-schattingen zijn niet betrouwbaar.")
                # Niet rekenen met naturelwaarden voor een ander voedingsproduct.
                nutrition["kcal_per_serving_estimate"]=None
                nutrition["kcal_total_estimate"]=None
                nutrition["protein_g_per_serving_estimate"]=None
                nutrition["protein_source"]=False
                nutrition["priority"]=False
            tl=title.casefold()
            cuisine=("Aziatisch" if any(x in tl for x in
                     ("aziatisch","thaise","koreaanse","japanse","teriyaki",
                      "gember","sojasaus","buddhabowl","buddha")) else
                     "Latijns-Amerikaans" if any(x in tl for x in
                     ("mexicaans","costa ricaanse","gallo pinto","zuid-amerikaanse",
                      "chipotle","burrito")) else
                     "Mediterraan" if any(x in tl for x in
                     ("mediterrane","italiaanse","italiaans","griekse")) else "Overig")
            instructions=RECIPE_METHODS.get(title,"")
            if idx>=len(RECIPES):
                for p,v,side,other,template_title,method in DISH_TEMPLATES:
                    if template_title==title:
                        instructions=method
                        break
            instructions=cooking_instructions(title,ings,instructions)
            pantry=pantry_for_recipe(title,ings,instructions)
            portable=meal_type=="Lunch"
            prep_ahead=meal_type in ("Lunch","Ontbijt")
            inspiration=("Actiegestuurde maaltijd" if idx>=len(RECIPES)
                         else "HelloFresh-variant" if title.startswith("HelloFresh-geïnspireerd:")
                         else "Mealprep-variant" if title.startswith("Mealprep:")
                         else "Eigen recept")
            all_recipes.append({"id":str(idx+1),"title":title,"category":category,"minutes":minutes,
              "inspiration":inspiration,"offer_driven":idx>=len(RECIPES),
              "mealprep":title.startswith("Mealprep:") or minutes>=30,
              "nutrition":nutrition,"meal_type":meal_type,"cuisine":cuisine,
              "portable":portable,"prep_ahead":prep_ahead,
              "instructions":instructions,"pantry":pantry,
              "price_excludes_pantry":True,
              "drained_weight_unverified":drained_uncertain,
              "servings":4,"ingredient_count":len(ings),"sale_count":discounts,
              "other_offer_count":alternative_count,
              "deal_basket":{"used_actions":deal_used,"checkout":deal_cash if complete else None,
                             "known_subtotal":deal_cash,"extra_vs_cheapest":deal_extra,
                             "ingredients":deal_lines},
              "covered_count":len(lines),"complete":complete,
              "checkout":checkout if complete else None,"known_subtotal":checkout,
              "used_total":consumed if complete else None,
              "per_serving":round(consumed/4,2) if complete else None,
              "saving":saving,"ingredients":lines,"missing":missing,
              "optional_pantry":"Smaakmakers staan per recept apart vermeld; niet inbegrepen in de prijs of voedingswaardeschatting."})
        # Beste ACTIECOMBINATIES voorop, daarbinnen kleinste complete prijs per portie.
        all_recipes.sort(key=lambda r:(
               not r["complete"],
               -r["sale_count"],
               -(r["saving"] if r["saving"] else 0),
               not r["nutrition"]["priority"],
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

# Belangrijke ingredientgroepen waarmee ontbrekende actieherkenning direct
# zichtbaar wordt. Dit is een diagnostische controle, geen extra prijsgok.
AUDIT_GROUPS={
    "Zuivel":("kwark","yoghurt","melk","kaas"),
    "Fruit":("aardbeien","blauwe_bessen","banaan","avocado"),
    "Groenten":("broccoli","spinazie","spruiten","bloemkool","wok",
                "paprika","courgette","champignons","wortel","tomaten",
                "tomatenblokjes","boerenkool","sla","komkommer","ui"),
    "Vlees en kip":("kipfilet","kipdij","kipgehakt","gehakt","varkenshaas",
                    "rookworst","shoarma"),
    "Vis":("zalm","gerookte_zalm","tonijn"),
    "Plantaardig":("tofu","kikkererwten","linzen","bonen"),
    "Ontbijt en lunch":("havermout","wraps","hummus","noten","eieren"),
    "Bijgerechten":("rijst","pasta","couscous","aardappel","zoete_aardappel",
                    "naan","mais","kokosmelk")
}
# Nieuw opgenomen ingrediënten horen automatisch bij de controle, zelfs
# wanneer iemand vergeet ze handmatig aan AUDIT_GROUPS toe te voegen.
AUDIT_GROUPS["Overige ingrediënten"]=tuple(
    sorted(set(ING)-{key for keys in AUDIT_GROUPS.values() for key in keys}))

def audit_recipe_quality(recipes):
    """Meet generiek alle ongeprijsde, onevenwichtige en actiearme recepten.

    Ontbijt hoeft geen groenten te bevatten. Een gezondheidswaarschuwing
    is geen verbod: ook klassiekers blijven vindbaar.
    """
    report={}
    for store,items in recipes.items():
        issues=[]
        for recipe in items:
            nutrition=recipe.get("nutrition") or {}
            issues_for_recipe=[]
            if not recipe.get("complete"):
                issues_for_recipe.append("Onvolledige kassaprijs")
            protein_value=nutrition.get("protein_g_per_serving_estimate")
            if protein_value is None:
                issues_for_recipe.append("Eiwitwaarde van gekozen product niet geverifieerd")
            elif protein_value<30:
                issues_for_recipe.append("Minder dan 30 gram eiwit per portie")
            if recipe.get("meal_type")=="Avondeten" and nutrition.get(
                    "vegetable_g_per_serving_estimate",0)<250:
                issues_for_recipe.append("Minder dan 250 gram groenten bij avondeten")
            if recipe.get("offer_driven") and not recipe.get("instructions"):
                issues_for_recipe.append("Actierecept zonder bereidingswijze")
            if nutrition.get("processed_meat"):
                issues_for_recipe.append("Bewerkt vlees: incidentele keuze")
            if recipe.get("other_offer_count",0) and not recipe.get("sale_count",0):
                issues_for_recipe.append("Acties beschikbaar, niet in goedkoopste mand")
            if issues_for_recipe:
                issues.append({"title":recipe["title"],"meal_type":recipe["meal_type"],
                               "issues":issues_for_recipe})
        meal_summary={}
        for meal in ("Ontbijt","Lunch","Avondeten"):
            subset=[r for r in items if r.get("meal_type")==meal]
            meal_summary[meal]={
                "recipes":len(subset),
                "with_action_choices":sum((r.get("deal_basket") or {}).get(
                    "used_actions",r.get("sale_count",0))>0 for r in subset),
                "fully_priced":sum(bool(r.get("complete")) for r in subset)
            }
        report[store]={"meals":meal_summary,
                       "review_needed":len(issues),
                       "examples":issues[:40]}
    return report

def audit_promotions(offers,recipes):
    """Signaleer gevonden acties die NIET als actie in recepten terechtkomen.

    Een naamherkenning betekent niet dat de korting betrouwbaar te berekenen is.
    Daarom worden ontbrekende maateenheden, bundels en vergelijkingen afzonderlijk
    gerapporteerd, zonder fictieve kortingen toe te voegen.
    """
    report={}
    for store in STORES:
        rows=offers[store]
        recipe_keys={line.get("key") for recipe in recipes[store] for line in recipe.get("ingredients",[])}
        linked={normalize(line.get("action",{}).get("name",""))
                for recipe in recipes[store]
                for line in recipe["ingredients"] if line.get("sale") and line.get("action")}
        groups={}
        details=[]
        for group,keys in AUDIT_GROUPS.items():
            count=linked_count=0
            for offer in rows:
                matching=[key for key in keys if match_ingredient(offer,key)]
                if not matching:continue
                count+=1
                if normalize(offer["name"]) in linked:
                    linked_count+=1
                    continue
                typ=normalize(offer.get("promotion_type") or "")
                if not offer.get("quantity") or not offer.get("unit"):
                    reason="Verpakkingsmaat onbekend"
                elif not any(k in recipe_keys for k in matching):
                    reason="Ingrediënt ontbreekt in beschikbare recepten"
                elif offer.get("is_loyalty"):
                    reason="Klantenkaartactie niet doorberekend"
                elif (not offer.get("multi_buy_quantity") and
                      any(t in typ for t in ("1 1","2 1","3 2","gratis","bundle","multi"))):
                    reason="Bundelvoorwaarden onvoldoende bekend"
                elif (offer.get("original_price") and
                      offer["original_price"]<=offer["price"] and
                      not offer.get("multi_buy_quantity")):
                    reason="Geen aantoonbaar prijsvoordeel"
                else:
                    reason="Niet gekozen: receptdekking, productmatch of goedkoopste alternatief"
                details.append({"name":offer["name"],"group":group,
                                "keys":matching,"reason":reason,
                                "price":offer["price"],
                                "valid_until":offer.get("valid_until"),
                                "url":offer.get("url","")})
            groups[group]={"recognized_offers":count,
                           "linked_offers":linked_count,
                           "unlinked_offers":count-linked_count}
        # Eén product kan in meerdere inhoudelijke groepen vallen. De
        # groepsaantallen zijn diagnostisch en tellen niet op tot een uniek totaal.
        details.sort(key=lambda d:(d["group"],d["reason"],d["name"]))
        report[store]={"groups":groups,"unlinked":details[:250],
                       "unlinked_total":len(details),
                       "note":"Een niet-gekoppelde actie is niet automatisch een fout: "
                              "een normale prijs kan goedkoper zijn of de verpakking "
                              "kan niet betrouwbaar worden doorgerekend."}
    return report

def main():
    errors=[]
    shelves,last_modified,counts=load_shelves()
    if not any(counts.values()):
        raise RuntimeError("Geen reguliere prijzen terug uit Checkjebon: geen misleidende lege publicatie")
    offers,errors=load_deals()
    # Externe recepten zoeken vanuit daadwerkelijke actieproducten.
    # Losse bronresultaten zijn geen berekende vierpersoonsmaaltijden.
    try:
        from recepten_ontdekker import build as discover_recipes, save as save_discovery
        discovered=discover_recipes(offers)
        save_discovery(discovered)
    except (requests.RequestException,ValueError,OSError) as exc:
        errors.append("Externe receptontdekking tijdelijk niet beschikbaar: "+str(exc))
        discovered={s:{"recipes":[],"verified_matches":0,"errors":["bron tijdelijk onbereikbaar"]} for s in STORES}
    # Recepten uit ALLE publieke en eigen bronindexen vinden op basis van de
    # actuele aanbiedingen. Deze titelmatches zijn nadrukkelijk NIET geprijsd.
    from actie_receptmatches import build_action_title_candidates
    source_recipe_matches=build_action_title_candidates(offers)
    export_shopping_index(shelves,offers)
    recipes=make_recipes(shelves,offers)
    validate_publication(recipes)
    audit=audit_promotions(offers,recipes)
    quality=audit_recipe_quality(recipes)
    result={"updated_at":datetime.now(TZ).isoformat(),"shelf_source_modified":last_modified,
            "sources":{"ordinary":"Checkjebon open dataset","promotions":"PrijsProfeet gratis aanbiedingen-API"},
            "source_links":{"ordinary":"https://github.com/supermarkt/checkjebon",
                            "promotions":"https://www.prijsprofeet.nl"},
            "store_names":STORES,"counts":{"ordinary":counts,"promotions":{s:len(offers[s]) for s in STORES}},
            "recipes":recipes,"discovered_recipes":discovered,
            "source_recipe_matches":source_recipe_matches,
            "audit":audit,"quality_audit":quality,
            "deals":{s:sorted(({**o,"discount_verified":verified_discount(o),
                                  "verified_discount_pct":verified_discount_percentage(o)}
                                 for o in offers[s]),
                              key=lambda d:(not d["discount_verified"],
                                            -(d.get("verified_discount_pct") or 0))) for s in STORES},
            "errors":errors,
            "disclaimer":"Online prijzen indicatief. Kassaprijzen zijn berekend uit beschikbare verpakkingen. Kruiden/olie uit voorraad en eventuele persoonlijke coupons niet inbegrepen. Geen garantie op winkelvoorraad."}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    tmp=OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(result,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    tmp.replace(OUT)
    print(json.dumps({"shelf":counts,"offers":result["counts"]["promotions"],
                      "recipes_with_offers":{s:sum(r["sale_count"]>0 for r in result["recipes"][s]) for s in STORES},
                      "breakfast_offer_details":{s:[{"title":r["title"],
                       "used":r["sale_count"],"other":r.get("other_offer_count",0)}
                       for r in result["recipes"][s] if r["meal_type"]=="Ontbijt"]
                       for s in STORES},
                      "matched_offer_lines":{s:sum(r["sale_count"] for r in result["recipes"][s]) for s in STORES},
                      "fully_priced_recipes":{s:sum(r["complete"] for r in result["recipes"][s]) for s in STORES},
                      "errors":errors,
                      "title_matches":{s:source_recipe_matches[s].get("possible_title_matches",0) for s in STORES},
                      "audit_unlinked":{s:audit[s]["unlinked_total"] for s in STORES}},ensure_ascii=False))
if __name__=="__main__":main()
