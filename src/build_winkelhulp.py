"""Build the small shopping view from sourced recipes and dated price evidence.

Never download or publish cookbook text. Unknown units, product forms and drained
weights stay open. A partial subtotal is never a full meal price.
"""
import argparse
import copy
import json
import math
import shutil
import re
import unicodedata
from functools import lru_cache
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from zoneinfo import ZoneInfo

from receptenradar_catalog import ING
from product_compatibiliteit import compatible

ROOT = Path(__file__).resolve().parents[1]
STORES = {"ah": "AH", "jumbo": "Jumbo", "lidl": "Lidl"}
TZ = ZoneInfo("Europe/Amsterdam")
ALIASES = {"kip": "kipfilet", "ei": "eieren", "bonen": "sperziebonen",
           "paprikavers": "paprika", "tomaat": "tomatenblokjes",
           "tomaatvers": "tomaten", "haver": "havermout", "linzen": "linzen_rood"}
EXTRA = {
    "kip": (r"\bkipfilet(?:blokjes|haasjes)?\b", r"vegetar|vegan|plantaardig|beleg|gerookt|gebakken|gebraden|gegrild|voorgegaard|krokant|gepaneerd|nuggets|tuinkruiden|saus"),
    "broccoli": (r"\b(broccoli|broccoliroosjes)\b", r"soep|saus|mix|maaltijd"),
    "cottage": (r"\b(cottage cheese|huttenkase)\b", r"salade|saus|spread"),
    "olie": (r"\bzonnebloemolie\b", r"tonijn|frituur|bakolie|olijfolie"),
    "paprika": (r"\b(paprikapoeder|paprika mild gemalen|milde paprika|paprika gemalen)\b", r"chips|saus|snack|mix"),
    "kerrie": (r"\b(kerriepoeder|kerrie gemalen|kerrie kruidig|milde kerrie)\b", r"saus|pasta|maaltijd"),
    "ham": (r"\bhamlappen\b", r"gekruid|gemarineerd|maaltijd"),
    "biefstuk": (r"\b(biefstuk|kogelbiefstuk|runderbiefstuk)\b", r"reepjes|saus|maaltijd|burger|tartaar|varken|duitse"),
    "witvis": (r"\b(koolvisfilet|kabeljauwfilet|heekfilet|pangasiusfilet|tilapiafilet)\b", r"gepaneerd|saus|maaltijd|met huid|krokant|burger|sticks"),
    "prei": (r"\bprei\b", r"mix|soep|saus|maaltijd"),
    "spitskool": (r"\bspitskool\b", r"mix|salade|saus|maaltijd"),
    "mosterd": (r"\bmosterd\b", r"saus|honing|vlees|kaas|worst|chips|mayonaise"),
    "sojasaus": (r"\b(sojasaus|soja saus)\b", r"ketjap|teriyaki|vlees|maaltijd"),
    "knoflook": (r"\bknoflook\b", r"poeder|saus|pasta|boter|olie|mix|worst|brood"),
    "gember": (r"\bgember\b", r"poeder|siroop|saus|thee|drank|koek|bier|pasta|bolletjes"),
    "citroen": (r"\bcitroenen?\b", r"sap|saus|smaak|rasp|drank|kwark|yoghurt|cake|thee|limoen"),
    "limoen": (r"\blimoenen?\b", r"sap|saus|smaak|rasp|drank|thee|citroen"),
    "pindakaas": (r"\b(100 pindakaas|pindakaas 100|100 pinda)\b", r"reep|koek|chocola|saus|suiker"),
    "rozemarijn": (r"\brozemarijn\b", r"aardappel|chips|kaas|mix|olie|vlees"),
    "dille": (r"\bdille\b", r"saus|zalm|mosterd|mix|kaas|yoghurt"),
    "komijn": (r"\b(komijn|komijnzaad|djinten)\b", r"kaas|mix|brood"),
    "italiaans": (r"\bitaliaanse kruiden\b", r"maaltijd|saus|brood|kip|gehakt"),
    "orzo": (r"\borzo\b", r"saus|maaltijd|salade"),
    "currypasta": (r"\bgroene curry\b", r"maaltijd|soep|kip|vis|garnalen"),
    "harissa": (r"\bharissa\b", r"kip|maaltijd|saus met|blend|kruiden|specerij|poeder"),
    "venkel": (r"\bvenkel\b", r"thee|zaad|poeder|worst|salami|mix"),
    "tahin": (r"\b(tahin|tahini)\b", r"saus|hummus|dip|koek"),
    "zaatar": (r"\b(za atar|zaatar)\b", r"hummus|brood|vlees"),
    "miso": (r"\b(witte miso|miso wit|shiro miso)\b", r"soep|maaltijd"),
    "sesam": (r"\bsesamzaad\b", r"olie|brood|koek|reep|cracker"),
    "chipotle": (r"\b(chipotlepasta|chipotle pasta|chipotle chilipasta|chipotle paste)\b", r"mayonaise|mayo|maaltijd|burger|chips|kip"),
    "edamame": (r"\b(edamame|sojabonen)\b", r"peul|snack|geroosterd|salade|maaltijd"),
    "sambal": (r"\bsambal oelek\b", r"maaltijd|kip|vlees"),
    "appel": (r"\b(appels|elstar|jonagold|gala appels|pink lady)\b", r"sap|moes|saus|gedroogd|chips|taart|koek|smaak|stroop"),
    "raselhanout": (r"\bras el hanout\b", r"maaltijd|kip|vlees"),
    "kaneel": (r"\bkaneel\b", r"koek|brood|suiker|appel|smaak|drank|muesli|reep"),
    "beefsurinam": (r"\bbeef surinam\b", r"maaltijd"),
    # Pesto's rennet/vegetarian status is not proven by the price feed.
}


@lru_cache(maxsize=50000)
def norm(s):
    s = unicodedata.normalize("NFKD", str(s).lower())
    return re.sub(r"[^a-z0-9]+", " ", "".join(c for c in s if not unicodedata.combining(c))).strip()


def money(n):
    return float(Decimal(str(n)).quantize(Decimal(".01"), rounding=ROUND_HALF_UP))


COMPOSITE = re.compile(r"\b(?:salade|slaverrijker|saladeverrijker|rauwkost|dressing|"
    r"maaltijd|stoommaaltijd|ovenschotel|ovengroente|oven|airfryer|pokebowl|pizzas?|"
    r"grillworst|worst|worstjes|saucijs|tapena\w*|broodbeleg|vleeswaren|beleg|"
    r"girasoli|ravioli|lasagne|stamppotje|stamppot|puree|wok|roerbakmix|roerbakgroente|"
    r"chips|wavy|tijgernootjes|pinda|pindas|biscuits?|koek|sultana|klene|drop|"
    r"hummus|hoemoes|humus|mayo|mayonaise|jam|spread|v\s+spread|"
    r"gebakken|gegrild|gerookt|geroosterd|gebraden|gekruid|gemarineerd|sticky|"
    r"americanos|halfgedroogd|gedroogd|zongedroogd|creme|room|cream|"
    r"bonduelle|hak)\b")
FOODS = {
    "aardappel": r"\b(?:aardappels?|aardappelen|aardappeltjes|bakaardappeltjes|potatoes)\b",
    "brood": r"\b(?:brood|broodjes|naan|pita|pitas|wraps|tortilla|sandwich|toast)\b",
    "pasta": r"\b(?:pasta|macaroni|penne|spaghetti|fusilli|girasoli|ravioli|speltpasta)\b",
    "broccoli": r"\bbroccoli\b", "bloemkool": r"\bbloemkool\b",
    "wortel": r"\b(?:wortel|wortelen|worteltjes|winterpeen|waspeen)\b",
    "tomaatvers": r"\b(?:tomaat|tomaten|cherrytomaten|trostomaten)\b",
    "paprikavers": r"\b(?:paprika|paprikas|puntpaprika)\b",
    "knoflook": r"\b(?:knoflook|knoflooktenen)\b", "ui": r"\b(?:ui|uien)\b",
    "courgette": r"\bcourgette\b", "spinazie": r"\bspinazie\b",
    "venkel": r"\bvenkel\b", "pastinaak": r"\bpastinaak\b",
    "kaas": r"\b(?:kaas|cheese|parmezaan|plakken)\b",
    "vlees": r"\b(?:kip|rund|rundvlees|varken|vlees|ham|vis|zalm|garnalen)\b",
    "fruit": r"\b(?:appel|appels|peer|peren|peertjes|stoofpeertjes|banaan)\b",
}
WHOLE_KEYS = {"kip", "gehakt", "ham", "biefstuk", "varkenshaas", "witvis", "zalm", "garnalen",
              "broccoli", "bloemkool", "paprikavers", "tomaatvers", "courgette", "champignons",
              "wortel", "bonen", "prei", "spitskool", "spinazie", "paksoi", "aubergine", "venkel",
              "appel", "knoflook", "gember", "rozemarijn", "dille", "komijn", "italiaans",
              "raselhanout", "kaneel", "tofu", "tempeh", "komkommer", "edamame", "ei"}
SPICE_KEYS = {"rozemarijn", "dille", "komijn", "italiaans", "raselhanout", "kaneel", "paprika", "kerrie"}
RAW_WORDS = set("ah jumbo lidl terra vivera iglo blue planet basic biologisch biologische bio scharrel "
    "vers verse vriesvers vriesverse diepvries bevroren gesneden gewassen grootverpakking voordeelverpakking "
    "kleinverpakking voordeel voordeelpak xxl xl extra fijn fijne hele halve mini witte wit hollandse nederlandse "
    "rode rood geel gele groene groen los zak bak doos net voordeelverp stuk stuks st gram gr g kilo kg ml l "
    "naturel naturelverse rauw rauwe mild malse mager magere gemengd gemengde stevig stevige blok blokjes scharrelkip halal ca circa lezziz "
    "roosjes schijfjes reepjes gehakte gehakt bonen boontjes gepeld gepelde wild wilde noorse alaska "
    "kogel schotse ierse rund runder duitse klasse a a b c uitloop vrije vrijeuitloop grote klein groteklein "
    "in mand tas pak fto dv van goede aarde igt diepgevroren versgesneden".split())
SPICE_WORDS = RAW_WORDS | set("verstegen silvo euroma jonnie boer by world spice blend smaakje smaak "
    "vermeulen green gypsy onoff spices simply organic gedroogd gedroogde gemalen grof kruidenzaad "
    "kruidig delicaat zaad specerij specerijen zakje bus potje".split())


def simple_name(key, name, positive):
    """Only known raw-product qualifiers may remain around the ingredient name.

    A negative-word list alone cannot distinguish all prepared meals and snacks.
    Unknown words are therefore a missing product match, never a guessed match.
    """
    if key not in WHOLE_KEYS and key not in SPICE_KEYS:
        return True
    rest = re.sub(positive, " ", name)
    rest = re.sub(r"\b\d+\b", " ", rest)
    allowed = SPICE_WORDS if key in SPICE_KEYS else RAW_WORDS
    return all(word in allowed for word in rest.split())


def product_form_safe(key, name):
    if key in WHOLE_KEYS or key in {"paprika", "kerrie", "harissa", "chipotle"}:
        if COMPOSITE.search(name):
            return False
    if key in WHOLE_KEYS:
        allowed = {key}
        if key in {"kip", "gehakt", "ham", "biefstuk", "varkenshaas", "witvis", "zalm", "garnalen"}:
            allowed.add("vlees")
        if key == "appel":
            allowed.add("fruit")
        if any(group not in allowed and re.search(pattern, name) for group, pattern in FOODS.items()):
            return False
    if key == "tempeh" and "curry" in name:
        return False
    if key == "tofu" and re.search(r"\b(zacht|zachte|silken|zijde)\b", name):
        return False
    return True


def matches(key, name):
    n = norm(name)
    if key == "edamame" and ("gepeld" not in n or "bonduelle" in n):
        return False
    if key in EXTRA:
        positive, negative = EXTRA[key]
        return bool(re.search(positive, n)) and not re.search(negative, n) and product_form_safe(key, n) and simple_name(key, n, positive)
    original_key = key
    key = ALIASES.get(key, key)
    if key not in ING:
        return False
    _, positive, negative = ING[key]
    if not re.search(positive, n) or re.search(negative, n) or not product_form_safe(original_key, n) or not compatible(name, key) or not simple_name(original_key, n, positive):
        return False
    if key == "kwark" and not re.search(r"\b(mager|magere)\b", n):
        return False
    if key == "kwark" and re.search(r"aardbei|vanille|perzik|stracciatella|framboos|bosbes|mango|kersen", n):
        return False
    if key == "gehakt" and "mager" not in n:
        return False
    if key in ("pasta", "noedels", "couscous") and "volkoren" not in n:
        return False
    if key == "tofu" and re.search(r"gerookt|gekruid|gemarineerd", n):
        return False
    if key == "zalm" and re.search(r"\b(met huid|blik|conserven)\b", n):
        return False
    if key == "bloemkool" and "brocc" in n:
        return False
    if key == "garnalen" and not re.search(r"\b(gepeld|gepelde|cocktailgarnalen|cocktail garnalen)\b", n):
        return False
    # Neither ordinary net package weight nor total canned weight proves drained weight.
    if key in ("tonijn", "kidneybonen", "kikkererwten") and "uitgelekt" not in n:
        return False
    if key == "linzen_rood" and re.search(r"blik|pot|gekookt|uitgelekt", n):
        return False
    if key == "edamame" and ("gepeld" not in n or "bonduelle" in n):
        return False
    return True


def active_offer(row, today):
    if len(row) < 12 or not row[8] or not row[11]:
        return False
    if re.search(r"persoonlijk|bonus box|coupon|activeren", str(row[0]) + " " + str(row[7]), re.I):
        return False
    try:
        return date.fromisoformat(row[11]) <= today <= date.fromisoformat(row[8])
    except (ValueError, TypeError):
        return False


def option(ingredient, row, promo=False):
    """Exact units only. Do not silently shrink portions or invent piece weights."""
    key, amount, unit = ingredient["key"], ingredient["quantity"], ingredient["unit"]
    if len(row) < 5 or not matches(key, row[0]) or row[3] != unit:
        return None
    price, size = row[1:3]
    if key == "kip" and isinstance(size, (int, float)) and size < 250:
        return None  # small charcuterie packs are not proven raw chicken portions
    if key in ("tonijn", "kidneybonen", "kikkererwten"):
        drained = re.search(r"uitgelekt\s*(\d+(?:[.,]\d+)?)\s*g|(?<![\d.])(\d+(?:[.,]\d+)?)\s*g\s*uitgelekt", str(row[0]), re.I)
        if not drained:
            return None
        size = float((drained.group(1) or drained.group(2)).replace(",", "."))
    if key == "bonen" and ("pot" in str(row[4]).lower() or size in (660, 680, 720)):
        return None
    if not isinstance(price, (int, float)) or not isinstance(size, (int, float)):
        return None
    if not math.isfinite(price) or not math.isfinite(size) or price <= 0 or size <= 0:
        return None
    n = math.ceil(amount / size)
    if n > 20:
        return None
    packs, cash, sale = n, money(n * price), False
    condition = None
    if promo:
        regular, bundle_n, bundle_price, kind = row[4:8]
        if bundle_n and bundle_price and bundle_n >= 2 and float(bundle_n).is_integer():
            if not regular or bundle_price >= bundle_n * regular:
                return None
            bn = int(bundle_n)
            choices = [(money((qty // bn) * bundle_price + (qty % bn) * regular), qty)
                       for qty in (n, math.ceil(n / bn) * bn)]
            cash, packs = min(choices)
            if cash >= money(n * regular):
                return None
            sale = True
            condition = f"{bn} voor €{bundle_price:.2f}".replace(".", ",")
        elif regular and regular > price:
            if re.search(r"multi|gratis|bundle|plus|voor", str(kind), re.I):
                return None
            sale = True
            condition = "Actieprijs"
        else:
            # A promotion mention without a verifiable discount is not an action.
            return None
    skin = key in ("zalm", "witvis") and not re.search(r"zonder huid|huidloos", norm(row[0]))
    return {"product": row[0], "package_quantity": size, "unit": unit, "packages": packs,
            "checkout": cash, "used": money(amount / (packs * size) * cash),
            "leftover": round(packs * size - amount, 3), "sale": sale,
            "condition": condition, "valid_from": row[11] if promo else None,
            "valid_until": row[8] if promo else None,
            "loyalty": bool(row[10]) if promo else False,
            "url": row[9] if promo else row[4],
            "source": "PrijsProfeet" if promo else "Checkjebon",
            "form_note": "Controleer: zonder huid en graten" if skin else None,
            "form_verified": not skin}


def price_line(ingredient, products, today):
    ordinary = [x for row in products.get("ordinary", []) if (x := option(ingredient, row))]
    promos = [x for row in products.get("promotions", [])
              if active_offer(row, today) and (x := option(ingredient, row, True))]
    # User preference: actual action products first. A cheaper regular alternative
    # is still displayed to make the extra spending visible.
    candidates = promos or ordinary
    if not candidates:
        return {**ingredient, "price": None}
    chosen = min(candidates, key=lambda x: (x["used"], x["checkout"]))
    cheapest = min(ordinary, key=lambda x: (x["used"], x["checkout"])) if ordinary else None
    cheaper = cheapest if chosen["sale"] and cheapest and cheapest["used"] < chosen["used"] else None
    return {**ingredient, "price": {**chosen, "cheaper_regular": cheaper, "ordinary_alternative": cheapest}}


def rank(recipe):
    return (-recipe["sale_count"], not recipe["complete"],
            recipe["per_serving"] if recipe["complete"] else math.inf, recipe["title"])


def build(catalog, snapshot, today=None):
    today = today or datetime.now(TZ).date()
    stores = {}
    for code in STORES:
        products = snapshot.get("stores", {}).get(code, {})
        cache = {}
        recipes = []
        for original in catalog["recipes"]:
            recipe = copy.deepcopy(original)
            lines = []
            for ing in original["ingredients"]:
                key = (ing["key"], ing["quantity"], ing["unit"])
                if key not in cache:
                    cache[key] = price_line(ing, products, today)
                lines.append(copy.deepcopy(cache[key]))
            complete = all(x["price"] and x["price"]["form_verified"] for x in lines)
            known_used = money(sum(x["price"]["used"] for x in lines if x["price"]))
            known_checkout = money(sum(x["price"]["checkout"] for x in lines if x["price"]))
            recipe.update(ingredients=lines, complete=complete,
                          sale_count=sum(bool(x["price"] and x["price"]["sale"]) for x in lines),
                          known_used=known_used, known_checkout=known_checkout,
                          per_serving=money(known_used / 4) if complete else None,
                          checkout=known_checkout if complete else None,
                          used_total=known_used if complete else None)
            recipes.append(recipe)
        stores[code] = sorted(recipes, key=rank)
    return {"schema_version": 1, "generated_at": datetime.now(TZ).isoformat(),
            "prices_observed_at": snapshot.get("updated_at"), "priced_for": today.isoformat(),
            "store_names": STORES, "stores": stores, "source_files": catalog["source_files"],
            "coverage_note": catalog["coverage_note"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", type=date.fromisoformat)
    parser.add_argument("--refresh", action="store_true", help="Fetch current price evidence; fail without shelf data")
    args = parser.parse_args()
    catalog = json.loads((ROOT / "winkelhulp/recipes.json").read_text())
    if args.refresh:
        # Reuse only the mature feed readers; the new shopping view has its own
        # conservative ingredient/product matching and never uses title-only hits.
        from receptenradar_v2 import load_shelves, load_deals
        shelves, modified, counts = load_shelves()
        offers, errors = load_deals()
        if not all(counts.get(s, 0) for s in STORES) or not any(offers.values()):
            raise RuntimeError("Incomplete price feeds; previous shopping publication preserved")
        stores = {}
        for s in STORES:
            ordinary = [[p["name"], p["price"], p["quantity"], p["unit"], p.get("url", "")]
                        for p in shelves[s]]
            promotions = [[p["name"], p["price"], p["quantity"], p["unit"],
                           p.get("original_price"), p.get("multi_buy_quantity"),
                           p.get("multi_buy_price"), p.get("promotion_type", ""),
                           p.get("valid_until"), p.get("url", ""), p.get("is_loyalty", False),
                           p.get("valid_from")] for p in offers[s] if p.get("quantity") and p.get("unit")]
            stores[s] = {"ordinary": ordinary, "promotions": promotions}
        snapshot = {"updated_at": datetime.now(TZ).isoformat(), "stores": stores}
    else:
        snapshot = json.loads((ROOT / "recepten/winkelprijzen.json").read_text())
    result = build(catalog, snapshot, args.as_of)
    for folder in (ROOT / "winkelhulp", ROOT / "docs/winkelhulp"):
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "data.json").write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n")
    for asset in ("index.html", "style.css", "engine.js", "app.js"):
        shutil.copyfile(ROOT / "winkelhulp" / asset, ROOT / "docs/winkelhulp" / asset)
    print(json.dumps({s: {"recipes": len(rows), "complete": sum(r["complete"] for r in rows),
                         "with_actions": sum(r["sale_count"] > 0 for r in rows)}
                      for s, rows in result["stores"].items()}))


if __name__ == "__main__":
    main()
