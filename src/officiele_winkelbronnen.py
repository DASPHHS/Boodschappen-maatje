"""Conservatieve openbare winkelbron-scan voor aanvullende dealontdekking.

Slechts gestructureerde Product/Offer-data uit de officiële winkelpagina wordt
als productprijs genoteerd. Geen folderafbeelding-OCR, geen kortingsclaim zonder
een expliciete van-prijs, geen lokale voorraadgarantie.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"recepten"/"officiele-winkels.json"
USER_AGENT="BoodschappenMaatje/1.0 (public offer discovery)"
SOURCES={
 "lidl":"https://www.lidl.nl/c/aanbiedingen/a10008785",
 "action":"https://www.action.com/nl-nl/weekactie/",
 "xenos":"https://www.xenos.nl/acties",
 "zeeman":"https://www.zeeman.com/nl-nl/weekaanbiedingen",
}
INTEREST=re.compile(r"\b(voeding|food|eten|snack|chocolade|snoep|rijst|pasta|saus|"
    r"noedel|koffie|thee|drink|melk|koek|noten|olie|meel|eiwit|protein|"
    r"keuken|pan|oven|bakvorm|opberg|schoonmaak|wasmiddel|reiniger|"
    r"papier|vaatwas|afwas|zeep|shampoo|tandpasta|servet|handdoek|"
    r"gezicht|douche|verzorging)\b",re.I)

def permitted(url,session):
    parts=urlparse(url)
    robots=f"{parts.scheme}://{parts.netloc}/robots.txt"
    try:
        response=session.get(robots,headers={"User-Agent":USER_AGENT},timeout=12)
        if response.status_code==404:return True
        if response.status_code!=200:return False
        parser=RobotFileParser()
        parser.parse(response.text.splitlines())
        return parser.can_fetch(USER_AGENT,url)
    except requests.RequestException:
        return False

def walk_products(raw):
    if isinstance(raw,list):
        for value in raw:yield from walk_products(value)
    if not isinstance(raw,dict):return
    typ=raw.get("@type",[])
    types=typ if isinstance(typ,list) else [typ]
    if "Product" in types:
        yield raw
    for key in ("@graph","itemListElement","item","mainEntity"):
        if key in raw:yield from walk_products(raw[key])

def parse_official_products(html,base):
    soup=BeautifulSoup(html,"html.parser")
    host=urlparse(base).netloc.casefold()
    rows=[];seen=set()
    for block in soup.select('script[type="application/ld+json"]'):
        try:obj=json.loads(block.string or block.get_text())
        except (ValueError,TypeError):continue
        for product in walk_products(obj):
            title=str(product.get("name") or "").strip()
            if not (3<len(title)<=170) or not INTEREST.search(title):continue
            url=product.get("url") or base
            if isinstance(url,dict):url=url.get("@id") or base
            if not isinstance(url,str) or not url.startswith("https://"):continue
            if urlparse(url).netloc.casefold()!=host:continue
            offers=product.get("offers") or {}
            if isinstance(offers,list):offers=next((v for v in offers if isinstance(v,dict)),{})
            price=offers.get("price") if isinstance(offers,dict) else None
            try:
                price=float(str(price).replace(",","."))
                if not (0<price<10000):price=None
            except (ValueError,TypeError):price=None
            key=(title.casefold(),url)
            if key in seen:continue
            seen.add(key)
            rows.append({"name":title,"url":url,"price":price,
                         "discount_verified":False,
                         "verification":"officiele_productvermelding_geen_korting_bewezen"})
    return rows

def scan(session=None):
    http=session or requests.Session()
    result={"updated_at":datetime.now(timezone.utc).isoformat(),
            "scope":"landelijke online aanbiedingen, lokale filiaalvoorraad onbekend",
            "stores":{},"status":{}}
    for store,url in SOURCES.items():
        rows=[];state="not_checked";detail=""
        if not permitted(url,http):
            state="robots_not_permitted_or_unavailable"
        else:
            try:
                response=http.get(url,headers={"User-Agent":USER_AGENT,
                    "Accept":"text/html"},timeout=22)
                response.raise_for_status()
                rows=parse_official_products(response.text,url)
                state="structured_products_found" if rows else "reachable_no_structured_products"
            except requests.RequestException as ex:
                state="fetch_failed";detail=type(ex).__name__
        result["stores"][store]=rows
        result["status"][store]={"state":state,"products":len(rows),
                                "source_url":url,"error":detail}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    temp=OUT.with_suffix(".tmp")
    temp.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    temp.replace(OUT)
    return result

if __name__=="__main__":
    data=scan()
    print(json.dumps({"source_states":data["status"]},ensure_ascii=False))
