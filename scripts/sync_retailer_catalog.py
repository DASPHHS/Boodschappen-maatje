#!/usr/bin/env python3
"""Import reusable publicly published supermarket shelf-price observations.

Source: supermarket/checkjebon/data/supermarkets.json (MIT repository, README
explicitly allows reusing price data). All prices remain external observations:
never label these retailer-verified and never infer a promotional discount.
"""
from __future__ import annotations
import datetime as dt
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.request import Request, urlopen
from urllib.error import URLError

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data"
SOURCE = "https://raw.githubusercontent.com/supermarkt/checkjebon/main/data/supermarkets.json"
COMMITS = "https://api.github.com/repos/supermarkt/checkjebon/commits?path=data/supermarkets.json&per_page=1"
STORES = ("ah", "jumbo", "lidl")
MAX_AGE_DAYS = 3


def fetch_json(url):
    req = Request(url, headers={"User-Agent": "Boodschappenmaatje/1.0 price-source-audit",
                                "Accept": "application/json"})
    with urlopen(req, timeout=65) as response:
        if response.status != 200: raise ValueError("Source HTTP response not OK")
        return json.load(response)


def source_date(commits):
    item = (commits or [{}])[0]
    stamp = item.get("commit", {}).get("committer", {}).get("date", "")
    day = stamp[:10]
    try: return dt.date.fromisoformat(day), item.get("sha", "")
    except ValueError: raise ValueError("Missing source date")


def normalize(raw, store):
    name = str(raw.get("n") or "").strip()
    pack = str(raw.get("s") or "").strip()
    link = str(raw.get("l") or "").strip()
    price = raw.get("p")
    if not isinstance(price, (float, int)) or isinstance(price, bool) or not 0 < price < 1000:
        return None
    if not name or not link or len(name) > 180 or len(pack) > 50:
        return None
    if store == "ah":
        if not link.startswith("wi") or "/" not in link: return None
        url = "https://www.ah.nl/producten/product/" + link
    elif store == "jumbo":
        if "/" in link or not link.rsplit("-", 1)[-1].isalnum(): return None
        url = "https://www.jumbo.com/producten/" + link
    else:
        # Checkjebon Lidl records contain only numeric retailer identifiers.
        # Do not synthesize a product link without a verified URL pattern.
        if not link.isdecimal(): return None
        url = None
    return [name, round(float(price), 2), pack, url, link]


def build(dataset, commits, today):
    day, sha = source_date(commits)
    if day > today or (today - day).days > MAX_AGE_DAYS:
        raise ValueError(f"Supplier snapshot too old or future: {day}; preserved existing catalogue")
    source = {s.get("n"): s.get("d", []) for s in dataset if isinstance(s, dict)}
    if any(not isinstance(source.get(s), list) or len(source[s]) < 1000 for s in STORES):
        raise ValueError("Incomplete store source, refusing to overwrite cached prices")
    stores={}
    for store in STORES:
        seen=set()
        rows=[]
        for raw in source[store]:
            if not isinstance(raw, dict): continue
            row=normalize(raw, store)
            if not row: continue
            uid=(row[0].lower(),row[2].lower(),row[4])
            if uid in seen: continue
            seen.add(uid);rows.append(row)
        if len(rows) < 1000: raise ValueError("Unreasonable normalized catalog size")
        stores[store]=rows
    return {
        "schema_version":1,
        "source":"checkjebon-public-dataset",
        "source_url":"https://github.com/supermarkt/checkjebon/blob/main/data/supermarkets.json",
        "source_commit":sha,
        "source_date":day.isoformat(),
        "generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),
        "fields":["name","price","pack_label","retailer_url","product_id"],
        "stores":stores,
    }


def main():
    today=dt.datetime.now(ZoneInfo('Europe/Amsterdam')).date()
    if os.getenv("DATE_OVERRIDE"): today=dt.date.fromisoformat(os.environ["DATE_OVERRIDE"])
    try:
        dataset=fetch_json(SOURCE)
        commits=fetch_json(COMMITS)
        result=build(dataset,commits,today)
    except (URLError, TimeoutError, ValueError, OSError, json.JSONDecodeError) as exc:
        print("Catalog import failed safely; keeping previous prices:", str(exc))
        if not (DATA / "retailer-catalog.json").exists(): raise
        return
    target=DATA / "retailer-catalog.json"
    tmp=target.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(result, ensure_ascii=False, separators=(",",":"))+"\n", encoding="utf-8")
    tmp.replace(target)
    print("Published real product records", {s:len(v) for s,v in result["stores"].items()},
          "source date",result["source_date"])


if __name__ == "__main__":
    main()
