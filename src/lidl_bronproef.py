"""Meetbare bronproef voor Lidl: controleer API-structuur en pagina's.

Deze proef importeert GEEN prijzen in productie. Hij maakt zichtbaar of
een alternatief werkelijk meer bruikbare Lidl-aanbiedingen teruggeeft.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
import requests
from feed_paginering import page_fingerprint

ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/"docs"/"recepten"/"lidl-bronproef.json"
BASE="https://www.prijsprofeet.nl/api/v1"
ENDPOINTS=("/products/promotional/all","/products")
PARAMS={"retailer":"lidl","page_size":100}
HEADERS={"User-Agent":"BoodschappenMaatje/4.0 (source health check)",
         "Accept":"application/json"}

def evaluate_pages(pages):
    ids=set()
    fingerprints=set()
    products=0
    errors=[]
    for number,payload in enumerate(pages,1):
        if not isinstance(payload,dict):
            errors.append("niet-json-object");continue
        rows=next((payload[k] for k in ("results","products","items")
                  if isinstance(payload.get(k),list)),None)
        if rows is None:
            errors.append("geen-productlijst");continue
        signature=page_fingerprint(rows)
        if signature in fingerprints and rows:
            errors.append("herhaalde-pagina")
        fingerprints.add(signature)
        products+=len(rows)
        for row in rows:
            if not isinstance(row,dict):continue
            retailer=str(row.get("retailer") or "").casefold().replace("_","")
            if retailer and retailer not in ("lidl",):
                errors.append("ander-winkellabel")
            identity=str(row.get("id") or row.get("product_id") or "")
            if identity:
                if identity in ids:errors.append("dubbel-product-id")
                ids.add(identity)
    return {"rows":products,"unique_product_ids":len(ids),
            "page_count":len(pages),"issues":sorted(set(errors)),
            "proven_full_coverage":False}

def probe(session=None):
    http=session or requests.Session()
    result={"updated_at":datetime.now(timezone.utc).isoformat(),"retailer":"lidl",
            "purpose":"connector_validation_only","endpoints":{}}
    for endpoint in ENDPOINTS:
        pages=[]
        failures=[]
        totals=[]
        for n in (1,2):
            try:
                r=http.get(BASE+endpoint,params={**PARAMS,"page":n},
                           headers=HEADERS,timeout=20)
                if not r.ok:
                    failures.append(f"http_{r.status_code}");break
                obj=r.json()
                if not isinstance(obj,dict):failures.append("bad_payload");break
                totals.append(obj.get("total"))
                pages.append(obj)
                rows=next((obj[k] for k in ("results","products","items")
                            if isinstance(obj.get(k),list)),[])
                if len(rows)<100:break
            except (requests.RequestException,ValueError,TypeError) as exc:
                failures.append(type(exc).__name__);break
        measurement=evaluate_pages(pages)
        measurement["errors"]=failures
        measurement["reported_total"]=totals[0] if totals else None
        measurement["status"]="measured" if pages and not failures and not measurement["issues"] else "failed_or_incomplete"
        result["endpoints"][endpoint]=measurement
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    tmp=TARGET.with_suffix(".tmp")
    tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    tmp.replace(TARGET)
    return result

if __name__=="__main__":
    print(json.dumps(probe(),ensure_ascii=False))
