#!/usr/bin/env python3
"""Full public promotion catalogue; never treats these as full shelf prices."""
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import json, os, re, sys, time
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

OUT=Path(__file__).resolve().parents[1]/"docs/data/offers-catalog.json"
BASE="https://www.prijsprofeet.nl/api/v1/products/promotional/all"
RETAILERS={"lidl":"lidl","jumbo":"jumbo","ah":"albert_heijn"}
REGEX={
"kip":r"\b(kip|kalkoen|kipfilet|kipdij|kiphaas|kipgehakt)[a-z]*\b",
"vis":r"\b(zalm|makreel|haring|forel|sardine|koolvis|kabeljauw|witvis|heek|schol|pangasius|schelvis|tonijn|visfilet)[a-z]*\b",
"vlees":r"\b(rund|runder|biefstuk|varken|varkens|hamlap|riblappen|entrecote|rosbief|ossenhaas|gehakt)[a-z]*\b",
"vega":r"\b(tofu|tempeh|seitan|edamame|eieren|kikkererwten|linzen|sojabrokken|vegan spek|plantaardige kip)[a-z]*\b",
"groente":r"\b(broccoli|bloemkool|courgette|paprika|champignon|prei|wortel|waspeen|spinazie|spruit|paksoi|boerenkool|spitskool|witte kool|rode kool|aubergine|tomaat|tomaten|uien|komkommer|venkel|sperziebonen|witlof|andijvie|wokgroente)[a-z]*\b"}
BLOCK=r"\b(spekreepjes|bacon|rookworst|salami|kroket|frikandel|nugget|schnitzel|hamburger|runderburger|kipburger|kruidenmix|kipkruiden|gepaneerd|visstick|fishstick|dierenvoer|kattenvoer|bier|wijn|chips|snoep|olvarit|baby|dreumes|peuter|maaltijdmix|kruiden|kruidenmix|basis voor|noedels|noodles|bouillon|saus|soep|wraphapje|wrap|rolletje|borrel|gevulde eieren|salade|pesto|spread|dip|grillworst|knaks|donut|rijstcookies|cracker|roti|pokebowl|bowl|kant-en-klaar|maaltijd|pasta|risotto|cordon bleu|voorgegaard|roerbakmix|belegd)\b"

def kind(name):
    t=name.lower()
    if re.search(BLOCK,t):return None
    if re.search(r"\b(100% plantaardig|vegan|vegetarisch)\b",t) and re.search(r"\b(kip|rund|varken|zalm|vis)\b",t) and not re.search(REGEX['vega'],t):return None
    if re.search(r"\b(vegan|vegetarisch|plantaardig)\b",t) and re.search(REGEX["vega"],t):return "vega"
    for k in ("kip","vis","vlees","vega","groente"):
        if re.search(REGEX[k],t):return k

def request(params):
    url=BASE+"?"+urlencode(params)
    headers={"User-Agent":"BoodschappenMaatje/1.0 (+https://github.com/DASPHHS/Boodschappen-maatje)"}
    key=os.environ.get("PRIJS_PROFEET_KEY")
    if key:headers["X-API-Key"]=key
    for attempt in range(3):
        try:
            with urlopen(Request(url,headers=headers),timeout=40) as r:return json.load(r)
        except HTTPError as e:
            if e.code==429 and attempt<2:
                time.sleep(min(90,max(3,int(e.headers.get("Retry-After") or "15"))));continue
            raise
        except (URLError,TimeoutError):
            if attempt==2:raise
            time.sleep(5)

def item(p,today):
    name=str(p.get("name") or "")
    k=kind(name)
    if not k or p.get("promotion_status")!="active" or p.get("online_only"):return
    start=str(p.get("valid_from") or "")[:10];end=str(p.get("valid_until") or "")[:10]
    if not(start<=today<=end):return
    price=p.get("price")
    if not isinstance(price,(int,float)) or isinstance(price,bool) or price<=0:return
    oid=p.get("product_id")
    if not oid:return
    orig=p.get("original_price")
    lp=p.get("loyalty_price")
    url=p.get("product_url")
    if not isinstance(url,str) or not url.startswith("https://"):url="https://www.prijsprofeet.nl/"
    return {"id":"pp-"+str(oid),"name":name,"category":k,
      "price":round(price,2),"regular_price":orig if isinstance(orig,(int,float)) else None,
      "loyalty_price":lp if isinstance(lp,(int,float)) else None,
      "loyalty_program":p.get("loyalty_program"),
      "pack_label":p.get("quantity") or "inhoud onbekend","unit":p.get("unit"),
      "unit_price":p.get("unit_price"),"start_date":start,"end_date":end,
      "date_estimated":bool(p.get("valid_until_estimated")),
      "multi_buy_quantity":p.get("multi_buy_quantity"),
      "multi_buy_price":p.get("multi_buy_price"),"promotion_type":p.get("promotion_type"),
      "source":{"label":"PrijsProfeet API (niet onafhankelijk bevestigd)","url":url},
      "source_provider":"PrijsProfeet","observed_at":p.get("extracted_at"),
      "promotion_status":"active","verified":False,
      "member_required":False,"brand":p.get("brand"),"ean":p.get("ean")}

def main():
    timestamp=datetime.now(ZoneInfo("Europe/Amsterdam"));today=timestamp.date().isoformat()
    previous={}
    if OUT.exists():
        try:previous=json.loads(OUT.read_text()).get("stores",{})
        except (ValueError,OSError):pass
    output={"schema_version":1,"generated_at":timestamp.isoformat(),"source":"PrijsProfeet public API",
      "notice":"API-gemelde promoties: geen onafhankelijke winkelcontrole of volledige reguliere assortimentprijzen.",
      "stores":{}}
    failures=0
    for store,retailer in RETAILERS.items():
        try:
            page=1;found={};total=None
            while True:
                data=request({"retailer":retailer,"page":page,"page_size":100})
                if data.get("retailer_filter"):raise ValueError("retailer filter not applied")
                rows=data.get("products")
                if not isinstance(rows,list):raise ValueError("products missing")
                if total is None:total=int(data.get("total") or 0)
                for row in rows:
                    x=item(row,today)
                    if x:found[x["id"]]=x
                if len(rows)<100 or page*100>=total:break
                page+=1
                if page>90:raise RuntimeError("pagination exceeded")
                time.sleep(2.2 if not os.environ.get("PRIJS_PROFEET_KEY") else 0.45)
            output["stores"][store]={"offers":list(found.values()),"reported_total":total,"status":"ok","checked_at":timestamp.isoformat()}
            print(store,total,"total,",len(found),"nutrition-relevant",flush=True)
        except Exception as e:
            failures+=1
            old=previous.get(store,{})
            output["stores"][store]={"offers":old.get("offers",[]),"reported_total":old.get("reported_total"),
              "status":"stale","checked_at":old.get("checked_at"),"error":str(e)[:200]}
            print(store,"FAILED",e,file=sys.stderr,flush=True)
    if failures==3:return 1
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n")
    return 2 if failures else 0

if __name__=="__main__":raise SystemExit(main())
