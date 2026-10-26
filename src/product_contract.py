"""Uniform productcontract voor bronvergelijking; geen nieuwe prijzen verzinnen."""
from datetime import date
from math import isfinite
import re, unicodedata

def normal(text):
    s=unicodedata.normalize("NFKD",str(text or "").casefold())
    return re.sub(r"\s+"," ",re.sub(r"[^\w\s]"," ","".join(c for c in s if not unicodedata.combining(c)))).strip()

def product_identity(row):
    ean=re.sub(r"\D","",str(row.get("ean") or ""))
    if len(ean) in (8,12,13,14):return "ean:"+ean
    return "variant:"+normal(row.get("name"))+"|"+str(row.get("quantity") or "")+"|"+str(row.get("unit") or "")

def normalized_offer(row,retailer,source,observed_at):
    name=str(row.get("name") or "").strip()
    price=row.get("price")
    try:price=float(price)
    except (TypeError,ValueError):return None
    if not name or not isfinite(price) or price<=0:return None
    start=str(row.get("valid_from") or "")[:10]
    end=str(row.get("valid_until") or "")[:10]
    try:
        if start and end and date.fromisoformat(start)>date.fromisoformat(end):return None
        if start:date.fromisoformat(start)
        if end:date.fromisoformat(end)
    except ValueError:return None
    return {"retailer":retailer,"identity":product_identity(row),"name":name,
        "price":round(price,2),"quantity":row.get("quantity"),"unit":row.get("unit"),
        "valid_from":start or None,"valid_until":end or None,
        "source":source,"observed_at":observed_at,
        "url":row.get("url"),"original_price":row.get("original_price"),
        "multi_buy_quantity":row.get("multi_buy_quantity"),
        "multi_buy_price":row.get("multi_buy_price"),
        "is_loyalty":bool(row.get("is_loyalty")),
        "discount_verified":bool(row.get("discount_verified"))}

def compare_sources(rows):
    """Conservatief: conflict of ontbrekende tweede bron wordt geen bevestiging."""
    grouped={}
    for row in rows:grouped.setdefault((row["retailer"],row["identity"]),[]).append(row)
    output=[]
    for (retailer,identity),items in grouped.items():
        independent={x["source"] for x in items}
        prices={x["price"] for x in items}
        status=("confirmed_by_two_sources" if len(independent)>=2 and len(prices)==1
                else "conflicting_sources" if len(independent)>=2 and len(prices)>1
                else "single_source")
        output.append({"retailer":retailer,"identity":identity,"status":status,
            "observations":items,"source_count":len(independent)})
    return output
