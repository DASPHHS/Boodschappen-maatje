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
from bronrecept_controle import verify_source_urls
from receptenradar_catalog import ING

ROOT = Path(__file__).resolve().parents[1]
PRICES = ROOT / "recepten" / "data.json"
INDEX = ROOT / "recepten" / "inspiratie.json"
OUTPUT = ROOT / "recepten" / "alternatieven.json"

# Dynamische dekking: alle ingrediënten die de echte recept- en prijsmotor kent
# krijgen een zoekcategorie. Dit is niet beperkt tot één voorbeeld (tonijn).
# Niet-herkende ingrediënten blijven via titel-/vrije-tekstzoekopdrachten vindbaar.
FOCUS = tuple(dict.fromkeys((*ING.keys(), "kip", "vis", "groenten")))
SYNONYMS = {
 "tonijn": ("tonijn", "tuna"),
 "kip": ("kip", "chicken", "pollo", "ayam"),
 "kipfilet": ("kipfilet", "chicken breast"),
 "kipdij": ("kipdij", "chicken thighs", "chicken thigh"),
 "kipgehakt": ("kipgehakt", "ground chicken"),
 "shoarma": ("shoarma", "shawarma"),
 "zalm": ("zalm", "salmon"),
 "gerookte_zalm": ("gerookte zalm", "smoked salmon"),
 "vis": ("vis", "fish", "seafood", "tonijn", "tuna", "zalm", "salmon",
         "kabeljauw", "cod", "garnalen", "shrimp", "prawns", "tilapia"),
 "gehakt": ("gehakt", "minced beef", "ground beef", "mince"),
 "varkenshaas": ("varkenshaas", "pork tenderloin"),
 "rookworst": ("rookworst",),
 "broccoli": ("broccoli",),
 "boerenkool": ("boerenkool", "kale"),
 "bloemkool": ("bloemkool", "cauliflower"),
 "spinazie": ("spinazie", "spinach"),
 "spruiten": ("spruitjes", "spruiten", "brussels sprouts"),
 "paprika": ("paprika", "bell pepper", "bell peppers"),
 "courgette": ("courgette", "zucchini"),
 "champignons": ("champignons", "mushroom", "mushrooms"),
 "tomaten": ("tomaat", "tomaten", "tomato", "tomatoes"),
 "tomatenblokjes": ("tomatenblokjes", "diced tomatoes", "chopped tomatoes"),
 "ui": ("uien", "rode ui", "onion", "onions", "sjalot"),
 "wortel": ("wortel", "wortelen", "carrot", "carrots"),
 "komkommer": ("komkommer", "cucumber"),
 "sla": ("sla", "lettuce", "rucola", "salad leaves"),
 "wok": ("wokgroenten", "roerbakgroenten", "stir fry vegetables"),
 "zoete_aardappel": ("zoete aardappel", "sweet potato", "sweet potatoes"),
 "aardappel": ("aardappel", "aardappelen", "potato", "potatoes", "krieltjes"),
 "bonen": ("bonen", "beans", "kidney beans", "black beans"),
 "kikkererwten": ("kikkererwten", "chickpea", "chickpeas"),
 "linzen": ("linzen", "lentils", "lentil"),
 "tofu": ("tofu",),
 "rijst": ("rijst", "rice", "brown rice"),
 "risottorijst": ("risotto", "arborio", "carnaroli"),
 "pasta": ("pasta", "spaghetti", "penne", "fusilli", "macaroni"),
 "couscous": ("couscous",),
 "wraps": ("wrap", "wraps", "tortilla", "tortillas"),
 "naan": ("naan", "naanbrood"),
 "eieren": ("ei", "eieren", "eggs", "egg", "omelet", "frittata"),
 "mais": ("maïs", "mais", "corn", "sweetcorn"),
 "kaas": ("kaas", "cheese", "parmesan"),
 "yoghurt": ("yoghurt", "yogurt"),
 "kwark": ("kwark", "quark", "skyr"),
 "melk": ("melk", "milk"),
 "kokosmelk": ("kokosmelk", "coconut milk"),
 "hummus": ("hummus",),
 "havermout": ("havermout", "oats", "oatmeal"),
 "noten": ("noten", "nuts", "walnuts", "almonds"),
 "banaan": ("banaan", "bananen", "banana", "bananas"),
 "aardbeien": ("aardbei", "aardbeien", "strawberry", "strawberries"),
 "blauwe_bessen": ("blauwe bessen", "bosbessen", "blueberries"),
 "avocado": ("avocado", "avocados"),
 "groenten": ("groenten", "vegetables", "vegetable", "salad",
              "broccoli", "spinazie", "courgette", "wokgroenten", "bloemkool",
              "paprika", "tomaten", "wortel"),
}

def normalized(value):
    s = unicodedata.normalize("NFKD", str(value or "").casefold())
    return re.sub(r"\s+", " ", "".join(c if c.isalnum() else " " for c in s
                                    if not unicodedata.combining(c))).strip()

def matching_focus(title):
    """Bepaal onderwerp, onafhankelijk van de voorbeeldproducten op de startpagina."""
    value = " " + normalized(title) + " "
    found = []
    for key in FOCUS:
        aliases = (*SYNONYMS.get(key, ()), key.replace("_", " "),
                   ING[key][0] if key in ING else key)
        if any(re.search(r"\b" + re.escape(normalized(alias)) + r"\b", value)
               for alias in aliases if alias):
            found.append(key)
    return found

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
            focus = sorted(set(matching_focus(title) + [k for k in keys if k in ING]))
            if recipe.get("category") == "Vis":
                focus = sorted(set((*focus, "vis")))
            if recipe.get("category") == "Kip":
                focus = sorted(set((*focus, "kip")))
            if any(k in keys for k in ("broccoli", "spinazie", "courgette", "paprika", "bloemkool", "wortel", "wok")):
                focus = sorted(set((*focus, "groenten")))
            # Geen recept laten verdwijnen omdat geen specifiek trefwoord in
            # de productnaam staat: 'alle ingrediënten' moet alles tonen.
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
        # Bronrecepten zonder bekende trefwoorden zijn óók receptalternatieven.
        # De titel blijft doorzoekbaar; we claimen geen geverifieerde ingrediënten.
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
            "category": entry.get("category") or "Onbekend",
            "url": href, "focus": focus,
            "status": "inspiratie, ingrediënten en prijs niet gecontroleerd",
            "seen_at": entry.get("discovered_at") or entry.get("seen_at") or now.date().isoformat()
        }
    # Bewaar variatie in bron en wereldkeuken. Eén groot Engelstalig archief
    # mag niet de gehele lijst verdringen; maximaal 90 resultaten per bron.
    from collections import defaultdict, deque
    pools = defaultdict(list)
    for item in unique.values():
        pools[(item["source"], item["cuisine"])].append(item)
    def alternate_topics(items):
        """Spreid ook BINNEN één groot archief over alle bekende onderwerpen."""
        from collections import defaultdict, deque, Counter
        groups = defaultdict(list)
        topic_counts = Counter(tag for item in items for tag in item["focus"]
                               if tag not in ("vis", "kip", "groenten"))
        for item in items:
            tags = [tag for tag in item["focus"] if tag not in ("vis", "kip", "groenten")]
            # Elk recept wordt eenmaal ingedeeld; het blijft vindbaar onder
            # alle eigen filters via het ongewijzigde focus-veld.
            key = min(tags, key=lambda tag: (topic_counts[tag], tag)) if tags else (item["focus"][0] if item["focus"] else "_overig")
            groups[key].append(item)
        pending = {key: deque(sorted(vals, key=lambda x: normalized(x["title"])))
                   for key, vals in groups.items()}
        ordered = []
        while any(pending.values()):
            for key in sorted(pending):
                if pending[key]:
                    ordered.append(pending[key].popleft())
        return ordered

    queues = {}
    for key, items in pools.items():
        queues[key] = deque(alternate_topics(items))
    diversified = []
    source_count = defaultdict(int)
    sorted_keys = sorted(queues, key=lambda key: (key[0], key[1]))
    while len(diversified) < 2500 and any(queues.values()):
        changed = False
        for key in sorted_keys:
            if not queues[key] or source_count[key[0]] >= 90:
                continue
            diversified.append(queues[key].popleft())
            source_count[key[0]] += 1
            changed = True
            if len(diversified) >= 2500:
                break
        if not changed:
            break
    return diversified

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

def generate(prices, index, prior, discovered, source_status, now, verifications=None, checked=None):
    if not isinstance(prices.get("recipes"), dict):
        raise RuntimeError("Prijsbron zonder recepten: niets publiceren")
    matches = priced_suggestions(prices)
    external = source_suggestions(index, discovered, prior, now)
    verifications=verifications or {}
    checked=checked or []
    for item in external:
        check=verifications.get(item["url"])
        if not check:continue
        item["verification_level"]=check.get("level","niet_gecontroleerd")
        item["verified_ingredient_count"]=check.get("ingredient_count")
        item["recognized_ingredient_keys"]=check.get("recognized_ingredients") or []
        item["verified_portions"]=check.get("servings")
        item["source_rating"]=check.get("rating")
        item["source_checked_at"]=check.get("checked_at")

    complete = {store: len([r for r in matches if r["store"] == store and r["complete"]])
                for store in ("ah", "jumbo", "lidl")}
    focus_counts = {f: {
        "priced": sum(f in r["focus"] and r["complete"] for r in matches),
        "unpriced": sum(f in r["focus"] and not r["complete"] for r in matches),
        "inspiration": sum(f in r["focus"] for r in external)
    } for f in FOCUS}
    focus_labels = {f: ING[f][0] if f in ING else {"kip":"Kip", "vis":"Vis en zeevruchten", "groenten":"Groenten"}[f]
                    for f in FOCUS}
    return {
        "updated_at": now.isoformat(timespec="seconds"),
        "prices_updated_at": prices.get("updated_at"),
        "inspiration_updated_at": index.get("updated_at"),
        "note": "Elke 30 minuten controle op een deel van geregistreerde bronnen. "
                "Een onvolledig geprijsd of extern recept is nooit een kassaprijsadvies.",
        "source_status": source_status,
        "source_recipe_checks": checked,
        "source_verifications": verifications,
        "source_recipes_with_ingredients": sum(x.get("verification_level") in
            ("bronrecept_4_personen","broningrediënten_beschikbaar") for x in external),

        "registered_collections": len(WORLD_SOURCES),
        "checked_collections_this_run": len(source_status),
        "full_prices_by_store": complete,
        "focus_counts": focus_counts,
        "focus_labels": focus_labels,
        "total_recipes": len(matches),
        "total_source_ideas": len(external),
        "suggestions": matches,
        "inspiration": external
    }

def main():
    now = datetime.now(timezone.utc)
    prices = load_json(PRICES, required=True)
    index = load_json(INDEX)
    old = load_json(OUTPUT)
    new_links, status = rotating_sources(now)
    candidates=source_suggestions(index,new_links,old,now)
    verified,checks=verify_source_urls(candidates,old.get("source_verifications"),now,limit=3)
    result = generate(prices, index, old, new_links, status, now,verified,checks)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("Halfuurcontrole", now.isoformat(), "geprijsde", len(result["suggestions"]),
          "inspiratie", len(result["inspiration"]),
          "categorieen", sum(any(c.values()) for c in result["focus_counts"].values()),
          "bronnen", status,"bronrecepten_controles",checks)

if __name__ == "__main__":
    main()
