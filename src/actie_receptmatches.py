"""Eerlijke actiegesteunde titelverkenning over duizenden echte bronrecepten.

BELANGRIJK: dit is kandidaatselectie, geen geverifieerde ingrediëntlijst.
Een recept met 'kip' in de titel kan bijvoorbeeld een andere kipsnede
vereisen dan het afgeprijsde product. Nooit als prijsberekende maaltijd
of '2 daadwerkelijk gebruikte acties' presenteren.
"""
import json,re,unicodedata
from pathlib import Path
from receptenradar_catalog import ING
from recept_keukens import infer_cuisine,dutch_title

ROOT=Path(__file__).resolve().parents[1]
RECIPE_INDEX=ROOT/"recepten"/"inspiratie.json"

def normalized(value):
    s=unicodedata.normalize("NFKD",str(value or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))

# Groepen die in een receptenTITEL culinair herkenbaar zijn.
# Productvarianten en deelstukken tellen NIET als bewezen substituut.
TITLE_KEYS={
 "kip":(r"\b(kip|kipfilet\w*|kippendij\w*|kipgehakt\w*|chicken|ajam|ayam|murgie|pollo|poulet)\b",
        ("kipfilet","kipdij","kipgehakt")),
 "gehakt":(r"\b(gehakt|meatballs?|minced|gehaktballetjes|rundergehakt)\b",
           ("gehakt","kipgehakt")),
 "zalm":(r"\b(zalm|salmon)\b",("zalm","gerookte_zalm")),
 "tonijn":(r"\b(tonijn|tuna)\b",("tonijn",)),
 "tofu":(r"\b(tofu|tahoe)\b",("tofu",)),
 "eieren":(r"\b(ei|eieren|egg|eggs|omelet|frittata)\b",("eieren",)),
 "kikkererwten":(r"\b(kikkererwt(en)?|chickpeas?|chana)\b",("kikkererwten",)),
 "linzen":(r"\b(linzen|lentils?|dal|dahl)\b",("linzen",)),
 "bonen":(r"\b(bonen|beans|kidneybonen|zwarte bonen)\b",("bonen",)),
 "rijst":(r"\b(rijst|rice|nasi|alesi|alesie)\b",("rijst",)),
 "pasta":(r"\b(pasta|spaghetti|macaroni|penne|fusilli|rigatoni|farfalle)\b",("pasta",)),
 "aardappel":(r"(?<!zoete )\b(aardappelen|aardappels|aardappel|krieltjes)\b|(?<!sweet )\b(potatoes|potato)\b",("aardappel",)),
 "zoete_aardappel":(r"\b(zoete aardappel|bataat|sweet potato)\b",("zoete_aardappel",)),
 "boerenkool":(r"\b(boerenkool|kale)\b",("boerenkool",)),
 "spinazie":(r"\b(spinazie|spinach)\b",("spinazie",)),
 "broccoli":(r"\bbroccoli\b",("broccoli",)),
 "bloemkool":(r"\b(bloemkool|cauliflower)\b",("bloemkool",)),
 "paprika":(r"\bpaprika\b",("paprika",)),
 "courgette":(r"\b(courgette|zucchini)\b",("courgette",)),
 "aubergine":(r"\b(aubergine|eggplant)\b",("aubergine",)),
 "champignons":(r"\b(champignon|champignons|paddenstoelen|mushrooms?)\b",("champignons",)),
 "kokosmelk":(r"\bkokosmelk\b",("kokosmelk",)),
 "kwark":(r"\b(kwark|skyr)\b",("kwark",)),
 "avocado":(r"\bavocado\b",("avocado",)),
 "banaan":(r"\b(banaan|bananen|banana)\b",("banaan",)),
 "aardbeien":(r"\b(aardbeien|aardbei|strawberries)\b",("aardbeien",)),
 "tomaten":(r"\b(tomaten|tomaat|tomato|tomatoes)\b",("tomaten","tomatenblokjes")),
}
PATTERNS={key:(re.compile(pattern,re.I),keys) for key,(pattern,keys) in TITLE_KEYS.items()}

def matched_keys(title,promotion_keys):
    name=normalized(title)
    matches={}
    for group,(pattern,keys) in PATTERNS.items():
        if not pattern.search(name):continue
        available=sorted(set(keys).intersection(promotion_keys))
        if available:matches[group]=available
    return matches

def select_candidates(index_items,promotion_keys,limit=80):
    candidates=[];seen=set()
    if not promotion_keys:return []
    for item in index_items:
        if item.get("kind")=="collection":continue
        title=str(item.get("title") or "").strip()
        if not title or len(title)>140:continue
        matched=matched_keys(title,promotion_keys)
        if not matched:continue
        source=item.get("source") or "Bron niet vermeld"
        unique=(source,normalized(title))
        if unique in seen:continue
        seen.add(unique)
        url=item.get("url")
        if url is not None and not str(url).startswith(("https://","http://")):
            continue
        candidates.append({
          "title":title,"title_nl":item.get("title_nl") or dutch_title(title)[0],
          "source":source,"cuisine":infer_cuisine(title,item.get("cuisine")),
          "category":item.get("category") or "Onbekend",
          "url":url,"match_terms":list(matched),"possible_offer_keys":
              sorted({x for keys in matched.values() for x in keys}),
          "matched_title_terms":len(matched),
          "verification":"ALLEEN TITELMATCH — broningrediënten niet gecontroleerd",
          "servings_verified":False,"price_verified":False
        })
    # Gezondheid kun je niet vaststellen zonder de volledige ingrediënten.
    # De titel levert alleen zwakke signalen voor welke recepten éérst
    # inhoudelijk gecontroleerd moeten worden.
    heavy=re.compile(
        r"\b(bacon|spek|alfredo|carbonara|roomsaus|deep.fried|gefrituurd|"
        r"frituur|bakabana|cake|dessert|milkshake|koek|snoep|ijs|"
        r"chocolate|chocolade|spareribs|varkenspoot|slagroom|kroket|loempia)\b",
        re.I)
    vegetable=re.compile(
        r"\b(broccoli|spinazie|groent\w*|vegetabl\w*|salad|salade|"
        r"lentil\w*|linzen|kikkererwt\w*|chickpea\w*|bonen|beans|"
        r"paprika|courgette|zucchini|tomaten|tomato\w*|aubergine|"
        r"eggplant|kale|bloemkool|cauliflower|avocado|carrots?)\b",re.I)
    protein=re.compile(
        r"\b(chicken|kip|kipfilet\w*|kippendij\w*|tofu|tahoe|beef|"
        r"gehakt|zalm|salmon|tuna|tonijn|vis|fish|shrimp|garnalen|"
        r"lentil\w*|linzen|beans|bonen|chickpeas|kikkererwten|"
        r"egg|eieren)\b",re.I)
    starches=(
        re.compile(r"\b(rice|rijst|nasi|alesi)\b",re.I),
        re.compile(r"\b(potato\w*|aardappel\w*)\b",re.I),
        re.compile(r"\b(pasta|spaghetti|noodles|bami)\b",re.I),
    )
    for x in candidates:
        name=normalized(x["title"])
        x["health_review"]="Niet geverifieerd: volledige ingrediënten, hoeveelheden en voedingswaarden ontbreken"
        n_starches=sum(bool(p.search(name)) for p in starches)
        x["health_priority"]=(
            "lage prioriteit" if heavy.search(name)
            else "kansrijk voor controle" if vegetable.search(name)
                 and protein.search(name) and n_starches<2
            else "nader beoordelen"
        )
        x["_rank"]={
            "kansrijk voor controle":0,
            "nader beoordelen":1,
            "lage prioriteit":3,
        }[x["health_priority"]]
    candidates.sort(key=lambda x:(x["_rank"],-x["matched_title_terms"],
       0 if x["source"].startswith(("AH ","Jumbo ","Faja Lobi","SurinamCooking",
                                    "Sandhia","Mijn HelloFresh")) else 1,
       x["title"].casefold()))
    # Diversifieer op bron en keuken in een ronde selectie. Anders domineert
    # Wikibooks het eerste scherm, ook met duizenden andere receptbronnen.
    result=[];counts={};sources={};remaining=list(candidates)
    while remaining and len(result)<limit:
        eligible=[x for x in remaining if counts.get(x["cuisine"],0)<12]
        if not eligible:break
        choice=min(eligible,key=lambda x:(
            x["_rank"],
            counts.get(x["cuisine"],0)*2,
            sources.get(x["source"],0)*2,
            -x["matched_title_terms"],
            x["title"].casefold()))
        remaining.remove(choice)
        choice.pop("_rank",None)
        result.append(choice)
        counts[choice["cuisine"]]=counts.get(choice["cuisine"],0)+1
        sources[choice["source"]]=sources.get(choice["source"],0)+1
    return result

def build_action_title_candidates(offers_by_store,index_path=RECIPE_INDEX,limit=80,shelves_by_store=None):
    from receptenradar_v2 import match_ingredient,verified_discount
    try:
        index=json.loads(Path(index_path).read_text(encoding="utf-8"))
        items=index.get("items",[])
        if not isinstance(items,list):raise ValueError("Bronindex bevat geen receptenlijst")
    except (OSError,ValueError,TypeError) as exc:
        return {store:{"candidates":[],"reason":"Bronindex niet beschikbaar: "+str(exc)}
                for store in offers_by_store}
    result={}
    for store,offers in offers_by_store.items():
        keys=set()
        for offer in offers:
            if not verified_discount(offer):continue
            if not offer.get("quantity") or not offer.get("unit"):continue
            for ingredient in ING:
                if match_ingredient(offer,ingredient):keys.add(ingredient)
        candidates=select_candidates(items,keys,limit)
        # Ook reguliere goedkope ingrediënten geven nuttige receptenideeën.
        # Vergelijkbare verpakkingen worden uitsluitend binnen hetzelfde ingrediënt
        # op bekende hoeveelheid en eenheid gerangschikt; geen fictieve korting.
        budget_keys=set()
        if shelves_by_store:
            from receptenradar_v2 import match_ingredient
            for ingredient in ING:
                matches=[]
                for product in shelves_by_store.get(store,[]):
                    quantity=product.get("quantity")
                    price=product.get("price")
                    if not quantity or not price or quantity<=0 or price<=0:
                        continue
                    if product.get("unit") not in ("g","ml"):
                        continue
                    if match_ingredient(product,ingredient):
                        matches.append(price*1000/quantity)
                if matches and min(matches)<=8:
                    budget_keys.add(ingredient)
        budget_candidates=select_candidates(items,budget_keys,limit)
        for item in budget_candidates:
            item["possible_budget_keys"]=item.pop("possible_offer_keys",[])
            item["verification"]="Alleen titelmatch met betaalbare reguliere producten; geen bevestigde receptprijs"
            item["match_type"]="budget_inspiration"
        result[store]={"candidates":candidates,"budget_candidates":budget_candidates,
                       "budget_ingredient_keys":len(budget_keys),
                       "possible_title_matches":len(candidates),
                       "verified_promotion_keys":len(keys),
                       "disclaimer":"Titelmatch is GEEN gecontroleerde recept- of kortingscombinatie; zonder broningrediënten en porties wordt geen kassaprijs berekend."}
    return result
