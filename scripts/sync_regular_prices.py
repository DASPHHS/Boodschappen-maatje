#!/usr/bin/env python3
"""Conservative daily refresh of known retailer product URLs.
Only an exact official product-detail URL with a matching product title can
replace a stored observation; sources without a price are never guessed.
"""
from __future__ import annotations
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo
import json
import os
import re
import time

DATA = Path(__file__).resolve().parents[1] / "docs/data/personal-prices.json"
HOSTS = {"ah": "ah.nl", "jumbo": "jumbo.com", "lidl": "lidl.nl"}

class ProductPage(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1 = []
        self.text = []
        self.jsonld = []
        self._in_h1 = False
        self._in_json = False
        self._buffer = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "h1":
            self._in_h1 = True
        if tag == "script" and "ld+json" in a.get("type", ""):
            self._in_json = True
            self._buffer = []
    def handle_endtag(self, tag):
        if tag == "h1": self._in_h1 = False
        if tag == "script" and self._in_json:
            self.jsonld.append("".join(self._buffer))
            self._in_json = False
    def handle_data(self, data):
        s = data.strip()
        if self._in_json: self._buffer.append(data)
        if s and not self._in_json:
            self.text.append(s)
            if self._in_h1: self.h1.append(s)

def direct_url(record):
    url = record.get("url", "")
    store = record.get("store")
    try:
        u = urlparse(url)
        host = (u.hostname or "").lower().removeprefix("www.")
        domain = HOSTS[store]
        if u.scheme != "https" or not (host == domain or host.endswith("." + domain)):
            return False
        path = u.path.lower()
        if store == "ah": return bool(re.search(r"/producten/product/wi\d+", path))
        if store == "jumbo": return bool(re.search(r"/producten/[^?#]*[-/]\d{5,}[a-z0-9]*$", path))
        return bool(re.search(r"/p/[^/]+", path))
    except (KeyError, ValueError, TypeError):
        return False

def clean(value):
    value = str(value or "").lower()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()

def title_match(expected, actual):
    wanted = clean(expected).split()
    found = set(clean(actual).split())
    filler = {"ah", "jumbo", "lidl", "verse", "stuks", "stuk", "per", "g",
              "kg", "ml", "l", "pp", "ca", "circa"}
    significant = [w for w in wanted if w not in filler and not w.isdigit()]
    # Fail closed: one distinctive product token can be enough for an exact
    # retailer product-ID URL, but all meaningful tokens must still match.
    if not significant: return False
    # Sereh/citroengras are synonyms; the retailer names the specific item AH Sereh.
    if set(significant) == {"sereh", "citroengras"} and "sereh" in found:
        return True
    matched = sum(w in found for w in significant)
    return matched == len(significant) or (matched >= 2 and matched >= len(significant) - 1)

def jsonld_prices(page):
    prices = []
    def walk(obj):
        if isinstance(obj, list):
            for el in obj: walk(el)
        elif isinstance(obj, dict):
            kind = str(obj.get("@type", ""))
            if kind in ("Offer", "AggregateOffer"):
                val = obj.get("price") or obj.get("lowPrice")
                try:
                    value = float(str(val).replace(",", "."))
                    if 0 < value < 2000 and obj.get("priceCurrency", "EUR") == "EUR":
                        prices.append(round(value, 2))
                except (TypeError, ValueError): pass
            for v in obj.values():
                if isinstance(v, (dict, list)): walk(v)
    for raw in page.jsonld:
        try: walk(json.loads(raw))
        except ValueError: continue
    return sorted(set(prices))

def observed(html, record):
    page = ProductPage()
    page.feed(html)
    title = " ".join(page.h1)
    if not title_match(record["name"], title):
        return None
    flat = " ".join(page.text)
    near = flat.split(title, 1)[-1][:450] if title in flat else flat[:600]
    if re.search(r"uit het assortiment|niet meer verkrijgbaar|niet langer verkrijgbaar", near, re.I):
        return {"availability_status": "discontinued"}
    if re.search(r"tijdelijk niet leverbaar|uitverkocht", near, re.I):
        return {"availability_status": "unavailable"}
    amounts = jsonld_prices(page)
    # Single structured price is acceptable only with the matching title.
    # Never fall back to scraping all euro amounts (recommendations and bundles).
    if len(amounts) != 1:
        # A tightly scoped single visible Product price is a second safe source.
        matches = re.findall(r"Prijs:\s*€\s*(\d{1,3}[,.]\d{2})", near, re.I)
        amounts = sorted({round(float(v.replace(",", ".")), 2) for v in matches})
    if not amounts:
        # AH sometimes exposes only a price per KG/LT after the exact product H1.
        # Only convert with explicitly stored grams/ml for this exact product ID.
        matches = re.findall(r"Prijs per\s+(KG|LT)\s*€\s*(\d{1,3}[,.]\d{2})", near, re.I)
        quantity, unit = record.get("quantity"), record.get("unit")
        if len(matches) == 1 and isinstance(quantity, (int, float)) and quantity > 0 and (
            (matches[0][0].upper() == "KG" and unit == "g") or
            (matches[0][0].upper() == "LT" and unit == "ml")
        ):
            amounts = [round(float(matches[0][1].replace(",", ".")) * quantity / 1000, 2)]
    if len(amounts) != 1:return None
    return {"price": amounts[0], "availability_status": "unknown"}

def fetch(url):
    req = Request(url, headers={
        "User-Agent": "BoodschappenMaatje/1.0 (+https://github.com/DASPHHS/Boodschappen-maatje)",
        "Accept": "text/html,application/xhtml+xml",
    })
    with urlopen(req, timeout=20) as response:
        if response.status != 200 or "html" not in response.headers.get("Content-Type", ""):
            return None
        # Never accept a redirected third-party domain as direct retailer evidence.
        if urlparse(response.geturl()).hostname != urlparse(url).hostname:
            return None
        return response.read(2_000_000).decode("utf-8", errors="replace")

def refresh(data, day, get_html=fetch):
    checked = updated = 0
    for item in data.get("products", []):
        if item.get("status") not in ("official_regular_observed", "official_discount_undated"):
            continue
        if not direct_url(item): continue
        checked += 1
        try: html = get_html(item["url"])
        except Exception as e:
            print("price page unavailable", item.get("store"), item.get("name"), type(e).__name__)
            continue
        if not html: continue
        result = observed(html, item)
        if result is None: continue
        if result["availability_status"] in ("discontinued", "unavailable"):
            if item.get("availability_status") != result["availability_status"] or item.get("availability_checked_date") != day:
                item["availability_status"] = result["availability_status"]
                item["availability_checked_date"] = day
                updated += 1
            continue
        # A matched product page without a price must leave the old timestamp unchanged.
        if "price" in result:
            item["price"] = result["price"]
            item["checked_date"] = day
            item["availability_status"] = "unknown"
            item["availability_checked_date"] = day
            updated += 1
        time.sleep(0.7)
    return checked, updated

def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    today = datetime.now(ZoneInfo("Europe/Amsterdam")).date().isoformat()
    checked, updated = refresh(data, today)
    print("Retailer detail pages considered:", checked, "price/availability records updated:", updated)
    if updated and not os.environ.get("DRY_RUN"):
        DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
