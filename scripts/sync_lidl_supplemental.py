#!/usr/bin/env python3
"""Fail-closed supplemental promotion fetcher; never calls a third-party price verified."""
from datetime import date,datetime
from zoneinfo import ZoneInfo
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request,urlopen
import json,re,sys
ROOT=Path(__file__).resolve().parents[1]
REG=ROOT/"docs/data/lidl-source-registry.json"
OUT=ROOT/"docs/data/supplemental-offers.json"
MONTHS=dict(zip("januari februari maart april mei juni juli augustus september oktober november december".split(),range(1,13)))
class Plain(HTMLParser):
    def __init__(self):super().__init__();self.words=[]
    def handle_data(self,data):self.words.append(data)
def flatten(html):
    doc=Plain();doc.feed(html)
    return re.sub(r"\s+"," "," ".join(doc.words)).strip()
def price(text,label):
    m=re.search(re.escape(label)+r"\s*€\s*(\d+(?:[.,]\d{1,2})?)",text,re.I)
    if not m:raise ValueError(label+" not found")
    return round(float(m.group(1).replace(",",".")),2)
def date_label(text,label):
    m=re.search(re.escape(label)+r"\s*(?:(?:maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag)\s+)?(\d{1,2})\s+(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+(\d{4})",text,re.I)
    if not m:raise ValueError(label+" date not found")
    return date(int(m.group(3)),MONTHS[m.group(2).lower()],int(m.group(1)))
def parse(html,source,today):
    text=flatten(html)
    # Do not copy a historical discount on a product page.
    if "deze bier aanbieding is niet meer geldig" in text.lower():return None
    start=date_label(text,"Geldig vanaf");end=date_label(text,"Geldig t/m")
    if not start<=today<=end:return None
    p=price(text,"Aanbieding prijs");regular=price(text,"Normale Prijs")
    if not(0<p<=regular):raise ValueError("Suspicious values")
    liters=source["liters"]
    return dict(id=source["id"],name=source["name"],category=source["category"],price=p,
        regular_price=regular,pack_label=source["pack_label"],unit="L",unit_price=round(p/liters,2),
        start_date=start.isoformat(),end_date=end.isoformat(),source_provider=source["provider"],
        source={"label":"Externe productdetailbron (niet Lidl-kassa)","url":source["url"]},
        promotion_status="active",verified=False,checked_at=today.isoformat(),
        status="third_party_price_observation",note="Exacte verpakking en actieperiode uit onafhankelijke derdepartijdetailpagina; geen officiële Lidl-kassacontrole.")
def read_source(source):
    req=Request(source["url"],headers={"User-Agent":"BoodschappenMaatje/1.0 (daily independent source check)"})
    with urlopen(req,timeout=25) as r:return r.read(2000000).decode("utf-8","replace")
def main():
    now=datetime.now(ZoneInfo("Europe/Amsterdam"))
    reg=json.loads(REG.read_text())
    offers=[];errors={}
    for source in reg["sources"]:
        try:
            o=parse(read_source(source),source,now.date())
            if o:offers.append(o)
        except Exception as e:errors[source["id"]]=str(e)[:140]
    result={"schema_version":1,"generated_at":now.isoformat(),
      "source":"Lidl supplemental third-party product page checks",
      "status":"partial" if errors else "ok",
      "errors":errors,
      "stores":{"lidl":{"checked_at":now.isoformat(),"status":"partial" if errors else "ok","offers":offers},
        "jumbo":{"offers":[],"status":"not_configured"},"ah":{"offers":[],"status":"not_configured"}}}
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("Lidl supplemental: ",len(offers),"current offers,",len(errors),"errors")
    return 0 if not errors else 2
if __name__=="__main__":sys.exit(main())
