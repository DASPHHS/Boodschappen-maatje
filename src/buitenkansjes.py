"""Personal bargain scan: full promotion catalogue and conservative cross-shop checks."""
import datetime as dt
import html
import json
import os
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo
import requests

BASE="https://www.prijsprofeet.nl/api/v1"
ROOT=Path(__file__).resolve().parents[1]
STORES=["albert_heijn","jumbo","lidl","aldi","dirk","hoogvliet","plus","dekamarkt","vomar"]
NAMES={"albert_heijn":"AH","jumbo":"Jumbo","lidl":"Lidl","aldi":"Aldi","dirk":"Dirk","hoogvliet":"Hoogvliet","plus":"PLUS","dekamarkt":"DekaMarkt","vomar":"Vomar"}
WATCH={
"Volle melk":[r"\bvolle melk\b",r"\bvolle houdbare melk\b"],
"Kwark, skyr en yoghurt":[r"\\b(skyr|magere yoghurt|magere kwark|high protein|highprotein|proteine kwark|proteïne kwark|protein kwark|knijpkwark|fitquark|fitkwark|xxl nutrition|kvarg|protein yoghurt)\\b"],
"Maaltijdpakketten":[r"\\b(knorr|wereldgerechten|wereldgerecht|maaltijdpakket|maaltijdmix|risotteria|spaghetteria|foodtrips)\\b"],
"Cola zero":[r"\b(coca.cola zero|pepsi max|pepsi zero|cola zero)\b"],
"Texels en bier":[r"\b(texels|texelse|bier|pils|alcoholvrij)\b"],
"Diepvriesfruit":[r"(diepvries|bevroren).*(fruit|bessen|bosvruchten|aardbei|mango|framboos)",r"diepvriesfruit"],
"Diepvriesgroenten":[r"(diepvries|bevroren).*(groent|spinazie|broccoli|erwten|wok)"],
"Vochtig toiletpapier":[r"(vochtig toiletpapier|toiletpapier vochtig|vochtige toiletdoekjes)"],
"Schoonmaakmiddelen":[r"(allesreiniger|schoonmaakmiddel|ontkalker|wc.reiniger|afwasmiddel|schoonmaakspray)"],
"Wasmiddel":[r"(wasmiddel|waspoeder|wascapsules|wascaps|wasverzachter)"],
"Vaatwastabletten":[r"(vaatwastabletten|vaatwascapsules|finish quantum|sun all.in.one)"],
"Koffie":[r"(giraffe|koffiebonen|espresso bonen|koffiecups|koffiepads)"],
"Tandpasta":[r"(elmex|tandpasta)"],
"Chocolade en snoep":[r"(chocolade|snoep|winegums|m&m|maltesers|haribo)"],
"IJs en pizza":[r"(roomijs|ristorante|diepvriespizza|pizza)"],
"Maaltijden":[r"(kipfilet|kipdij|zalm|makreel|tonijn|broccoli|spinazie|volkorenrijst|wokgroenten)"],
"Overig":[r"(ginger beer|texels 0.0|0[.,]0)"]}
PATTERNS={key:[re.compile(x,re.I) for x in values] for key,values in WATCH.items()}
HEADERS={"User-Agent":"KoopkrachtPersonal/2.0 (+https://github.com/DASPHHS/Boodschappen-maatje)","Accept":"application/json"}
if os.getenv("PRIJS_PROFEET_KEY"): HEADERS["X-API-Key"]=os.environ["PRIJS_PROFEET_KEY"]

def api(params):
    for n in range(4):
        r=requests.get(BASE+"/products/promotional/all",params=params,headers=HEADERS,timeout=25)
        if r.status_code in (429,502,503,504):
            h=r.headers.get("Retry-After","")
            time.sleep(min(25,int(h) if h.isdigit() else 2**(n+1)))
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError("Upstream API geeft herhaaldelijk een fout.")

def pull(store,max_pages=120):
    """Pagina's volledig doorlopen voordat een dagrapport wordt gepubliceerd.

    De AH-API bevat momenteel ruim 5000 promotievermeldingen: 50 pagina's
    van 100 zijn dus niet voldoende. Geen onvolledige dekking als volledig
    verklaren; limiet blijft bestaan voor onbegrensde bronnen.
    """
    rows=[]
    for page in range(1,max_pages+1):
        d=api({"retailer":store,"page":page,"page_size":100})
        if d.get("retailer_filter"): raise RuntimeError("Winkelfilter genegeerd: "+store)
        batch=d.get("products")
        if not isinstance(batch,list): raise RuntimeError("Onverwachte API-respons: "+store)
        rows.extend(batch)
        total=int(d.get("total") or 0)
        if len(rows)>=total or not batch:
            return rows,{"received":len(rows),"total":total,"complete":True}
        time.sleep(2.1)
    return rows,{"received":len(rows),"total":total,"complete":len(rows)>=total}

def number(value):
    try: return float(value) if value is not None else None
    except (TypeError,ValueError): return None

def normalize(p,today):
    name=str(p.get("name") or "")
    price=number(p.get("price"))
    if not name or price is None or price<=0 or not p.get("is_promotional",True): return None
    try:
        start=dt.date.fromisoformat(str(p.get("valid_from")))
        end=dt.date.fromisoformat(str(p.get("valid_until")))
    except ValueError: return None
    if end<today or start>today+dt.timedelta(days=14) or p.get("promotion_status")=="historical": return None
    tags=[k for k,patterns in PATTERNS.items() if any(pt.search(name) for pt in patterns)]
    if not tags: return None
    normal=number(p.get("original_price"))
    discount=round((1-price/normal)*100,1) if normal and normal>price else None
    return {"name":name,"retailer":str(p.get("retailer") or ""), "price":round(price,2),
      "normal":normal,"discount_pct":discount,"ean":str(p.get("ean") or ""),
      "quantity":str(p.get("quantity") or ""), "unit":p.get("unit"),
      "unit_price":number(p.get("unit_price")),"loyalty_price":p.get("loyalty_price"),
      "multi_buy_quantity":p.get("multi_buy_quantity"),"multi_buy_price":p.get("multi_buy_price"),
      "promotion_type":str(p.get("promotion_type") or ""),
      "status":"upcoming" if start>today else "active","valid_from":str(start),"valid_until":str(end),
      "tags":tags,"url":p.get("product_url") or "https://www.prijsprofeet.nl"}

def compare(rows,today):
    selected=[q for p in rows if (q:=normalize(p,today))]
    by_ean=defaultdict(list)
    for p in selected:
        if p["status"]=="active" and p["ean"] and p["quantity"]:
            by_ean[(p["ean"],p["quantity"].casefold())].append(p)
    confirmed,candidates,upcoming=[],[],[]
    for p in selected:
        if p["status"]=="upcoming":
            upcoming.append(p)
            continue
        matches=by_ean.get((p["ean"],p["quantity"].casefold()),[]) if p["ean"] and p["quantity"] else []
        other=min((x for x in matches if x["retailer"]!=p["retailer"]),key=lambda x:x["price"],default=None)
        p["other"]={"store":NAMES.get(other["retailer"],other["retailer"]),"price":other["price"]} if other else None
        if p["discount_pct"] is not None and p["discount_pct"]>=25 and other and not p["multi_buy_quantity"] and not other["multi_buy_quantity"] and p["price"]<=other["price"]*.90:
            p["market_advantage_pct"]=round((1-p["price"]/other["price"])*100,1)
            p["proof"]="ECHT KOOPJE: zelfde EAN/verpakking bij concurrent"
            confirmed.append(p)
        elif p["discount_pct"] is not None and p["discount_pct"]>=30:
            p["proof"]="Nog niet bewezen (geen gunstig geverifieerde concurrent)"
            candidates.append(p)
    priorities=("Volle melk","Cola zero","Texels en bier","Diepvriesfruit","Diepvriesgroenten","Vochtig toiletpapier","Schoonmaakmiddelen","Wasmiddel","Vaatwastabletten")
    def rank(p):
        return (int(any(t in priorities for t in p["tags"])),p.get("market_advantage_pct",0),p.get("discount_pct") or 0)
    for group in (confirmed,candidates,upcoming): group.sort(key=rank,reverse=True)
    return {"date":str(today),"scanned":len(rows),"confirmed":confirmed[:20],
      "candidates":candidates[:25],"next_week":upcoming[:25]}

def meal_offer_export(rows,today,coverage,max_per_store=350):
    """Extra-supermarktacties zichtbaar maken zonder kassaprijzen te verzinnen.

    De scan bevat alleen producten uit de actieve catalogus met geldige
    datums. Aanbiedingen van andere winkels zijn géén complete receptmandjes.
    Bundels: toon de losse prijs en de voorwaarden, zonder een foutief
    gemiddeld stuksbedrag bij één aankoop te claimen.
    """
    store_map={"albert_heijn":"ah","jumbo":"jumbo","lidl":"lidl",
               "aldi":"aldi","dirk":"dirk","hoogvliet":"hoogvliet",
               "plus":"plus","dekamarkt":"dekamarkt","vomar":"vomar"}
    by_store={name:[] for name in store_map.values()}
    selected=[item for row in rows if (item:=normalize(row,today)) is not None]
    for item in selected:
        store=store_map.get(item["retailer"])
        if store is None:continue
        name=item["name"].casefold()
        kit=bool(re.search(r"\\b(knorr|wereldgerechten|wereldgerecht|maaltijdpakket|maaltijdmix)\\b",name))
        protein=bool(re.search(r"\\b(fitquark|fitkwark|xxl nutrition|high protein|highprotein|protein kwark|skyr|kvarg|knijpkwark|proteine kwark|proteïne kwark)\\b",name))
        healthy=any(k in item["tags"] for k in ("Maaltijden","Kwark, skyr en yoghurt","Diepvriesfruit","Diepvriesgroenten","Maaltijdpakketten")) 
        has_deal=item["discount_pct"] is not None and item["discount_pct"]>=20
        if not (kit or protein or healthy or has_deal):continue
        multi=item.get("multi_buy_quantity")
        multi_price=item.get("multi_buy_price")
        # Een gepubliceerde actieprijs kan de losse kassaprijs zijn.
        # Markeer als controleerbare korting uitsluitend simpele, individuele acties.
        promotion=item.get("promotion_type") or ""
        needs_bundle=bool(multi or re.search(r"(?:[1-9]\s*\+\s*[1-9]\s*gratis|[2-9]\s*voor|gratis|multibuy|bundle|meer\s*voor)",promotion,re.I))
        verified=bool(not needs_bundle and item["normal"] is not None and item["discount_pct"] is not None and
                      item["normal"]>item["price"] and item["status"]=="active")
        relevance=(110 if kit else 105 if protein else 65 if healthy else 15)+min(35,item["discount_pct"] or 0)
        by_store[store].append({
            "name":item["name"],"retailer":store,"price":item["price"],
            "normal_price":item["normal"],"verified_discount_pct":item["discount_pct"] if verified else None,
            "discount_verified":verified,"size_label":item["quantity"] or "Verpakkingsinhoud niet bevestigd",
            "quantity_label":item["quantity"],"unit":item["unit"],
            "valid_from":item["valid_from"],"valid_until":item["valid_until"],
            "status":item["status"],"multi_buy_quantity":multi,
            "multi_buy_price":multi_price,"promotion_type":promotion or ("Meerverpakkingen" if multi else "Actie"),
            "url":item["url"],"category_hint":"maaltijdpakket" if kit else "eiwitrijk" if protein else "overig",
            "relevance":round(relevance,1),"price_source":"PrijsProfeet",
            "retailer_coverage_complete":bool(coverage.get(item["retailer"],{}).get("complete"))
        })
    for store,items in by_store.items():
        items.sort(key=lambda x:(-x["relevance"],x["status"]!="active",x["name"].casefold()))
        seen=set()
        by_store[store]=[x for x in items if not (x["name"].casefold(),x["valid_until"]) in seen
                         and not seen.add((x["name"].casefold(),x["valid_until"]))][:max_per_store]
    return {"updated_at":dt.datetime.now(ZoneInfo("Europe/Amsterdam")).isoformat(),
            "note":"Per winkel geselecteerde actieproducten; reguliere prijzen en volledige receptmandjes alleen waar afzonderlijk bevestigd. Bundels niet per stuk afgeprijsd bij losse aankoop.",
            "coverage":coverage,"stores":by_store}


def euros(price): return ("€ %.2f"%price).replace(".",",")
def safe(s): return html.escape(str(s),quote=True)

def render(data):
    def item(p):
        discount=("%s%% korting vs van-prijs"%p["discount_pct"]) if p["discount_pct"] is not None else "van-prijs onbekend"
        if p.get("multi_buy_quantity"): discount += f' · bundel van {p["multi_buy_quantity"]} stuks (totaal {euros(float(p["multi_buy_price"])) if p.get("multi_buy_price") else "controleer bundelprijs"})'
        other=p.get("other")
        competitor=(f' · Concurrent {safe(other["store"])}: {euros(other["price"])}' if other else ' · Marktvergelijking ontbreekt')
        per_unit=f' · {euros(p["unit_price"])}/{safe(p["unit"])}' if p["unit"] and p["unit_price"] is not None else ''
        return f'<article><strong>{safe(p["name"])}</strong><b class="price">{euros(p["price"])}</b><p>{safe(NAMES.get(p["retailer"],p["retailer"]))} · {discount}{per_unit}{competitor}</p><p>{safe(p["valid_from"])} tot {safe(p["valid_until"])} · {safe(p.get("proof","volgende week, nog niet actief"))}</p><a href="{safe(p["url"])}">Bekijk aanbieding</a></article>'
    def section(title,rows,empty):
        return f'<section><h2>{title}</h2>'+("".join(item(p) for p in rows) if rows else f'<p>{empty}</p>')+'</section>'
    body=f'<h1>Boodschappen Maatje</h1><p>Persoonlijke buitenkansjes · Bleiswijk · {safe(data["date"])}</p>'
    body+=section("Echt bewezen buitenkansjes",data["confirmed"][:8],"Vandaag geen aanbiedingen die én 25% onder de van-prijs én minstens 10% onder identieke actuele concurrentieprijs liggen.")
    body+=section("Interessant, maar nog controleren",data["candidates"][:12],"Geen kandidaten gevonden.")
    body+=section("Volgende week, nog niet kopen",data["next_week"][:12],"Nog geen toekomstige aanbiedingen gevonden.")
    body+='<p class="foot">Bron: <a href="https://www.prijsprofeet.nl">PrijsProfeet</a>. Productprijzen blijven indicatief. Kruidvat, Action, Trekpleister, Joybuy, Amazon en Picnic vallen niet onder deze automatische scanner. Gewone schapprijzen zijn in de gratis gegevens niet volledig beschikbaar.</p>'
    style='<style>body{margin:0 auto;padding:24px 16px;max-width:680px;background:#f7faf8;color:#20342d;font:15px/1.5 Arial,sans-serif}h1{font-size:28px}h2{font-size:19px}section{background:white;padding:18px;margin:15px 0;border-radius:14px;border:1px solid #dfe9e3}article{border-top:1px solid #e9eeea;padding:11px 0}article p,.foot{font-size:12px;color:#5c6962}.price{float:right;color:#216b52}a{color:#216b52}</style>'
    return '<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'+style+'</head><body>'+body+'</body></html>'

def main():
    today=dt.datetime.now(ZoneInfo("Europe/Amsterdam")).date()
    data,quality=[],{}
    for store in STORES:
        try:
            rows,quality[store]=pull(store)
            data.extend(rows)
            print(store,quality[store],flush=True)
        except Exception as e:
            quality[store]={"complete":False,"error":str(e)}
            print("FOUT",store,str(e),file=sys.stderr,flush=True)
    if any(not quality.get(k,{}).get("complete") for k in ("albert_heijn","jumbo","lidl")):
        raise SystemExit("Basisscan onvolledig; geen e-mail met misleidende data: "+json.dumps(quality))
    result=compare(data,today)
    result["coverage"]=quality
    retailer_offers=meal_offer_export(data,today,quality)
    ROOT.joinpath("data").mkdir(exist_ok=True)
    ROOT.joinpath("docs").mkdir(exist_ok=True)
    ROOT.joinpath("docs/recepten").mkdir(parents=True,exist_ok=True)
    ROOT.joinpath("docs/recepten/extra-supermarkt-deals.json").write_text(
        json.dumps(retailer_offers,ensure_ascii=False,separators=(",",":"))+"\\n",encoding="utf8")
    ROOT.joinpath("data/buitenkansjes.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    ROOT.joinpath("docs/buitenkansjes.html").write_text(render(result),encoding="utf8")
    print("ECHTE",len(result["confirmed"]),"TE CONTROLEREN",len(result["candidates"]),"VOLGENDE WEEK",len(result["next_week"]))

if __name__=="__main__": main()
