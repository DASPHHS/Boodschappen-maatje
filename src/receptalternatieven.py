"""Halfuurlijkse receptkansen: controleer bronlinks en publiceer eerlijke keuzes.

Een bronrecept is slechts inspiratie zolang ingrediënten, porties en kassaprijzen
niet zijn bevestigd. Alleen de bestaande prijsengine levert 'volledig geprijsd'.
Bij bronuitval worden eerdere resultaten hoogstens 14 dagen bewaard.
"""
from __future__ import annotations
import json
import re
import sys
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse
import requests

from wereldkeuken_bronnen import (
    WORLD_SOURCES, USER_AGENT, parse_links, robots_allowed
)
from recept_keukens import infer_cuisine, dutch_title

ROOT = Path(__file__).resolve().parents[1]
PRICES = ROOT / "recepten" / "data.json"
INDEX = ROOT / "recepten" / "inspiratie.json"
OUTPUT = ROOT / "recepten" / "alternatieven.json"

# Bezoek per run slechts twee collecties; alle geregistreerde collecties komen
# cyclisch aan bod. Geen zware, dagelijkse API- of prijsimport elk halfuur.
FOCUS = (
    "tonijn", "kip", "zalm", "gehakt", "broccoli", "boerenkool",
    "tofu", "kikkererwten", "eieren", "rijst", "pasta", "spinazie"
)
SYNONYMS = {
    "tonijn": ("tonijn", "tuna"),
    "kip": ("kip", "chicken", "pollo", "ayam"),
    "zalm": ("zalm", "salmon"),
    "gehakt": ("gehakt", "minced beef", "ground beef"),
    "broccoli": ("broccoli",),
    "boerenkool": ("boerenkool", "kale"),
    "tofu": ("tofu",),
    "kikkererwten": ("kikkererwten", "chickpea"),
    "eieren": ("eieren", "egg", "omelet", "frittata"),
    "rijst": ("rijst", "rice"),
    "pasta": ("pasta", "spaghetti", "penne", "fusilli"),
    "spinazie": ("spinazie", "spinach"),
}

def normalized(value):
    s = unicodedata.normalize("NFKD", str(value or "").casefold())
    return re.sub(r"\s+", " ", "".join(c if c.isalnum() else " " for c in s
                                    if not unicodedata.combining(c))).strip()

def matching_focus(title):
    value = " " + normalized(title) + " "
    return [key for key, aliases in SYNONYMS.items()
            if any(re.search(r"\b" + re.escape(normalized(alias)) + r"\b", value)
                   for alias in aliases)]

def price_number(value):
    try:
        x = float(value)
        return round(x, 2) if 0 < x < 10000 else None
    except (ValueError, TypeError):
        return None

def load_json(path, required=False):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as exc:
        if required:
            raise RuntimeError(f"Benodigde bron ongeldig: {path.name}: {type(exc).__name__}") from exc
        return {}

def priced_suggestions(data):
    results = []
    for store in ("ah", "jumbo", "lidl"):
        for recipe in data.get("recipes", {}).get(store, []):
            title = str(recipe.get("title") or "")
            keys = [str(line.get("key", "")) for line in recipe.get("ingredients", [])]
            focus = sorted(set(matching_focus(title) + [k for k in FOCUS if k in keys]))
            if not focus:
                continue
            price = price_number(recipe.get("checkout")) if recipe.get("complete") else None
            amount_used = int((recipe.get("deal_basket") or {}).get("used_actions") or recipe.get("sale_count") or 0)
            result = {
                "title": title, "store": store, "focus": focus,
                "cuisine": recipe.get("cuisine") or "Internationaal",
                "category": recipe.get("category") or "Onbekend",
                "minutes": recipe.get("minutes"),
                "complete": price is not None, "checkout": price,
                "per_serving": price_number(recipe.get("per_serving")),
                "used_actions": amount_used,
                "health_priority": bool((recipe.get("nutrition") or {}).get("priority")),
                "protein_per_serving": (recipe.get("nutrition") or {}).get("protein_g_per_serving_estimate"),
                "vegetables_per_serving": (recipe.get("nutrition") or {}).get("vegetable_g_per_serving_estimate"),
                "id": recipe.get("id"),
                "missing_count": len(recipe.get("missing") or []),
                "origin": recipe.get("inspiration") or "Eigen recept",
                "status": "volledig geprijsd" if price is not None else "niet volledig geprijsd",
            }
            results.append(result)
    # Geldigheid/cash van acties wordt al door de prijsengine gecontroleerd.
    # Niet-geprijsde suggesties krijgen NOOIT een prijs uit de brontitel.
    return sorted(results, key=lambda r:(
        not r["complete"], not r["health_priority"],
        r["checkout"] if r["checkout"] is not None else float("inf"),
        -r["used_actions"], normalized(r["title"]), r["store"]
    ))

def source_suggestions(index, new_links, previous, now):
    collected = []
    previous_candidates = previous.get("inspiration", [])
    cutoff = (now - timedelta(days=14)).date().isoformat()
    for item in index.get("items", []):
        if item.get("kind") == "collection" or item.get("category") == "Broncollectie":
            continue
        collected.append(item)
    collected.extend(new_links)
    # Behoud succesvolle externe bronnen wanneer één website tijdelijk offline is.
    collected.extend(x for x in previous_candidates
                     if x.get("seen_at", "")[:10] >= cutoff)
    unique = {}
    for entry in collected:
        title = (entry.get("title_nl") or entry.get("title") or "").strip()
        href = str(entry.get("url") or "")
        url = urlparse(href)
        if len(title) < 7 or url.scheme != "https" or not url.netloc:
            continue
        focus = matching_focus(title + " " + str(entry.get("title") or ""))
        if not focus:
            continue
        source = str(entry.get("source") or "Onbekende bron")
        key = href.rstrip("/").split("?")[0].casefold()
        if key in unique:
            continue
        title_nl, translated = dutch_title(entry.get("title") or "")
        unique[key] = {
            "title": title, "title_original": entry.get("title") or title,
            "title_nl": title_nl if translated else None,
            "source": source,
            "cuisine": infer_cuisine(title, entry.get("cuisine")),
            "url": href, "focus": focus,
            "status": "inspiratie, ingrediënten en prijs niet gecontroleerd",
            "seen_at": entry.get("discovered_at") or entry.get("seen_at") or now.date().isoformat()
        }
    all_items = list(unique.values())
    # Spreid weergave over bronnen i.p.v. honderden links van één website.
    all_items.sort(key=lambda x:(normalized(x["title"]),x["source"]))
    count = {}
    diversified = []
    for x in all_items:
        for key in x["focus"]:
            pair = (key, x["source"])
            if count.get(pair, 0) >= 16:
                continue
            count[pair] = count.get(pair, 0) + 1
            diversified.append(x)
            break
    return diversified[:1100]

def rotating_sources(now=None, session=None, max_sources=2):
    now = now or datetime.now(timezone.utc)
    # Vast halfuurslot in UTC, ook bij herstart dezelfde bronselectie.
    slot = int(now.timestamp() // 1800)
    sources = [WORLD_SOURCES[(slot * max_sources + offset) % len(WORLD_SOURCES)]
               for offset in range(min(max_sources, len(WORLD_SOURCES)))]
    http = session or requests.Session()
    new = []
    status = []
    for name, cuisine, url in sources:
        if not robots_allowed(url):
            status.append({"source": name, "state": "robots of toegang onbekend", "count": 0})
            continue
        try:
            response = http.get(url, headers={"User-Agent": USER_AGENT,
                                               "Accept": "text/html"}, timeout=9)
            response.raise_for_status()
            links = parse_links(response.text, url, name, cuisine, limit=35)
            new.extend(links)
            status.append({"source": name, "state": "bereikbaar", "count": len(links)})
        except requests.RequestException as exc:
            status.append({"source": name, "state": f"bronfout {type(exc).__name__}", "count": 0})
        time.sleep(0.1)
    return new, status

def generate(prices, index, prior, discovered, source_status, now):
    if not isinstance(prices.get("recipes"), dict):
        raise RuntimeError("Prijsbron zonder recepten: niets publiceren")
    matches = priced_suggestions(prices)
    external = source_suggestions(index, discovered, prior, now)
    complete = {store: len([r for r in matches if r["store"] == store and r["complete"]])
                for store in ("ah", "jumbo", "lidl")}
    focus_counts = {f: {
        "priced": sum(f in r["focus"] and r["complete"] for r in matches),
        "unpriced": sum(f in r["focus"] and not r["complete"] for r in matches),
        "inspiration": sum(f in r["focus"] for r in external)
    } for f in FOCUS}
    return {
        "updated_at": now.isoformat(timespec="seconds"),
        "prices_updated_at": prices.get("updated_at"),
        "inspiration_updated_at": index.get("updated_at"),
        "note": "Elke 30 minuten controle op een deel van geregistreerde bronnen. "
                "Een onvolledig geprijsd of extern recept is nooit een kassaprijsadvies.",
        "source_status": source_status,
        "registered_collections": len(WORLD_SOURCES),
        "checked_collections_this_run": len(source_status),
        "full_prices_by_store": complete,
        "focus_counts": focus_counts,
        "suggestions": matches,
        "inspiration": external
    }

def main():
    now = datetime.now(timezone.utc)
    prices = load_json(PRICES, required=True)
    index = load_json(INDEX)
    old = load_json(OUTPUT)
    new_links, status = rotating_sources(now)
    result = generate(prices, index, old, new_links, status, now)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("Halfuurcontrole", now.isoformat(), "geprijsde", len(result["suggestions"]),
          "inspiratie", len(result["inspiration"]), "tonijn", result["focus_counts"]["tonijn"], "bronnen", status)

if __name__ == "__main__":
    main()
