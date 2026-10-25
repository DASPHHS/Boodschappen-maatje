"""Actiegestuurde receptontdekking via de publieke TheMealDB API.

Alleen verifieerbare, expliciet vermelde ingrediënten worden gekoppeld.
Externe recepten blijven externe bronnen; we publiceren geen overgenomen
bereidingsteksten of foto's. Niet-geprijsde hoofdcomponenten blokkeren de match.
"""
import json,re,time
from collections import Counter
from pathlib import Path
from urllib.parse import quote
import requests
from receptenradar_catalog import ING
from receptenradar_v2 import match_ingredient, normalize, verified_discount
from recept_keukens import infer_cuisine,dutch_title

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/"recepten"/"ontdekte_recepten.json"
API="https://www.themealdb.com/api/json/v1/1"
ALIASES={
 "chicken breast":"kipfilet","chicken thighs":"kipdij","chicken thigh":"kipdij",
 "minced beef":"gehakt","ground beef":"gehakt","salmon":"zalm",
 "tuna":"tonijn","eggs":"eieren","egg":"eieren","tofu":"tofu",
 "broccoli":"broccoli","spinach":"spinazie","kale":"boerenkool",
 "cauliflower":"bloemkool","bell pepper":"paprika","red pepper":"paprika",
 "green pepper":"paprika","courgette":"courgette","zucchini":"courgette",
 "mushrooms":"champignons","mushroom":"champignons",
 "carrot":"wortel","carrots":"wortel","onion":"ui","onions":"ui",
 "potatoes":"aardappel","potato":"aardappel","sweet potatoes":"zoete_aardappel",
 "tomatoes":"tomaten","tomato":"tomaten","cherry tomatoes":"tomaten",
 "cucumber":"komkommer","avocado":"avocado","sweetcorn":"mais",
 "corn":"mais","rice":"rijst","brown rice":"rijst",
 "risotto rice":"risottorijst","arborio rice":"risottorijst",
 "whole wheat pasta":"pasta","wholemeal pasta":"pasta",
 "pasta":"pasta","spaghetti":"pasta","couscous":"couscous",
 "wraps":"wraps","tortillas":"wraps","chickpeas":"kikkererwten",
 "kidney beans":"bonen","black beans":"bonen","lentils":"linzen",
 "greek yogurt":"yoghurt","yogurt":"yoghurt","milk":"melk",
 "coconut milk":"kokosmelk","cheese":"kaas","oats":"havermout",
 "banana":"banaan","strawberries":"aardbeien","blueberries":"blauwe_bessen"
}
PANTRY_TERMS=("salt","pepper","oil","garlic","ginger","paprika powder","cumin",
 "coriander","turmeric","chilli","chili","vinegar","lemon juice","lime juice",
 "soy sauce","stock","water","parsley","basil","thyme","oregano","cinnamon",
 "sugar","honey","bay leaf","rosemary","flour","butter")
# Onbekende substantiele ingrediënten mogen niet stilzwijgend verdwijnen.
def ingredient_key(name):
    name=normalize(name).strip()
    # Broningrediënt en supermarktproduct moeten dezelfde culinaire vorm
    # hebben: "rice noodles" is GEEN rijst, "egg noodles" geen eieren,
    # "tomato paste" geen tomaten en "onion powder" geen verse ui.
    incompatible=(
      r"\\b(rice (noodles?|paper|flour|vinegar|wine|syrup|cakes?|crackers?)|"
      r"egg (noodles?|whites?|powder|rolls?|plant|substitute)|"
      r"tomato (paste|puree|sauce|ketchup|powder|soup)|"
      r"onion (powder|soup|seasoning)|"
      r"cheese (sauce|powder|spread)|"
      r"mushroom (soup|sauce|powder)|"
      r"milk (powder|chocolate)|"
      r"salmon (roe|oil|paste))\\b"
    )
    if re.search("".join(incompatible),name):return None
    # Noem pas de productgroep als de bronvermelding werkelijk op het
    # ingrediënt of een eenvoudige bewerkingsvorm daarvan slaat.
    safe_modifiers=("chopped","sliced","diced","fresh","frozen","canned",
                    "tinned","drained","cooked","raw","peeled","fillets",
                    "fillet","cut","pieces")
    for term,key in sorted(ALIASES.items(),key=lambda x:-len(x[0])):
        if name==term:return key
        if name.startswith(term+" "):
            extra=name[len(term)+1:]
            if extra in safe_modifiers or (
                extra and all(word in safe_modifiers for word in extra.split())):
                return key
    return None

def is_pantry(name):
    n=normalize(name)
    return any(n==p or n.startswith(p+" ") for p in PANTRY_TERMS)

def parse_amount(value):
    """Conservatieve conversie; niet omrekenbare porties worden afgewezen."""
    s=str(value or "").strip().lower().replace(",",".")
    s=re.sub(r"\([^)]*\)","",s).strip()
    m=re.match(r"^(\d+(?:\.\d+)?)(?:\s+)?(kg|g|grams?|ml|l|litres?|tbsp|tsp|cups?|oz|lb|pieces?|pcs?)\b",s)
    if not m:return None
    q=float(m.group(1));u=m.group(2)
    if u=="kg":return q*1000,"g"
    if u in ("g","gram","grams"):return q,"g"
    if u in ("ml",):return q,"ml"
    if u in ("l","litre","litres"):return q*1000,"ml"
    if u in ("piece","pieces","pc","pcs"):return q,"st"
    return None

def fetch_discovered(offers,session=None,max_queries=10):
    """Zoek op afgeprijsde hoofdproducten, niet op een vaste receptenlijst."""
    http=session or requests.Session()
    candidates=Counter()
    for offer in offers:
        if not offer.get("quantity") or not offer.get("unit"):continue
        if not verified_discount(offer):continue
        for key in ING:
            if match_ingredient(offer,key):
                candidates[key]+=1
    found={}
    errors=[]
    for key,_ in candidates.most_common(max_queries):
        query=next((alias for alias,mapped in ALIASES.items() if mapped==key),None)
        if not query:continue
        try:
            resp=http.get(API+"/filter.php",params={"i":query},timeout=15)
            resp.raise_for_status()
            ids=[x["idMeal"] for x in (resp.json().get("meals") or [])][:12]
            for meal_id in ids:
                if meal_id in found:continue
                detail=http.get(API+"/lookup.php",params={"i":meal_id},timeout=15)
                detail.raise_for_status()
                meal=(detail.json().get("meals") or [None])[0]
                if meal:found[meal_id]=meal
        except (requests.RequestException,ValueError,KeyError) as exc:
            errors.append(f"{key}: {type(exc).__name__}")
    return list(found.values()),errors

def verify_meal(meal,offered_keys):
    """Accepteer uitsluitend bronrecepten met controleerbare kernhoeveelheden."""
    if not meal.get("idMeal") or not meal.get("strMeal") or not meal.get("strInstructions"):
        return None
    source=meal.get("strSource") or ("https://www.themealdb.com/meal/"+str(meal["idMeal"]))
    if not source.startswith(("https://","http://")):return None
    items=[];pantry=[];unmapped=[]
    for i in range(1,21):
        name=(meal.get(f"strIngredient{i}") or "").strip()
        if not name:continue
        amount=(meal.get(f"strMeasure{i}") or "").strip()
        key=ingredient_key(name)
        if key:
            quantity=parse_amount(amount)
            if quantity is None:
                unmapped.append(name+" (hoeveelheid niet controleerbaar)")
            else:
                items.append((key,quantity[0],quantity[1]))
        elif is_pantry(name):
            pantry.append(name)
        else:
            unmapped.append(name)
    keys={x[0] for x in items}
    matched=keys.intersection(offered_keys)
    if len(matched)<2 or len(keys)<3 or unmapped:
        return None
    # De bron bevat vaak 2 of 6 porties zonder expliciet portieaantal.
    # Zonder betrouwbare porties geen misleidende 4-porties prijs.
    return {"source_id":str(meal["idMeal"]),"title":meal["strMeal"],
            "source_url":source,"source_name":"TheMealDB",
            "ingredient_keys":sorted(keys),"matched_offer_keys":sorted(matched),
            "source_ingredients":[{"key":k,"quantity":q,"unit":u} for k,q,u in items],
            "pantry":pantry,"servings_verified":False,
            "pricing_status":"Bronporties niet bevestigd; geen kassaprijs",
            "instructions_status":"Bereidingswijze bij de originele bron"}

def ingredient_confirmed_candidate(meal,offered_keys):
    """Selecteer bronrecepten met echte, door de bron genoemde actieproducten.

    De broningrediënten zijn gecontroleerd op NAAM, niet op hoeveelheden,
    vierpersoonsverhoudingen, voedingswaarden of volledige kassaprijzen.
    """
    if not meal.get("idMeal") or not meal.get("strMeal") or not meal.get("strInstructions"):
        return None
    raw=meal.get("strSource") or ("https://www.themealdb.com/meal/"+str(meal["idMeal"]))
    if not isinstance(raw,str) or not raw.startswith(("https://","http://")):
        return None
    original={}
    for i in range(1,21):
        name=(meal.get(f"strIngredient{i}") or "").strip()
        if not name:continue
        key=ingredient_key(name)
        if key:original.setdefault(key,[]).append(name)
    matches=sorted(set(original).intersection(offered_keys))
    if len(matches)<2:return None
    title=str(meal["strMeal"]).strip()
    dutch,_=dutch_title(title)
    area=str(meal.get("strArea") or "").strip()
    cuisine=infer_cuisine(title,area or None)
    keys=set(original)
    nutrient_meal=bool(keys.intersection({"kipfilet","kipdij","gehakt","tofu","zalm",
                   "tonijn","eieren","linzen","bonen","kikkererwten","kwark"}))
    produce=bool(keys.intersection({"broccoli","spinazie","boerenkool","bloemkool",
                   "paprika","courgette","champignons","wortel","tomaten",
                   "tomatenblokjes","ui","sla"}))
    return {"title":title,"title_nl":dutch,"source":"TheMealDB",
            "cuisine":cuisine,"url":raw,
            "match_terms":matches,"matched_title_terms":len(matches),
            "ingredient_keys":sorted(keys),
            "source_ingredient_names":{k:original[k] for k in matches},
            "health_priority":"kansrijk voor controle" if nutrient_meal and produce
                else "nader beoordelen",
            "verification_level":"ingredient_names_only",
            "verification":"Actieproducten daadwerkelijk genoemd in ingrediëntenlijst van bron",
            "servings_verified":False,"price_verified":False,
            "health_review":"Nog geen controle op hoeveelheden, kcal of eiwit per portie"}


def build(offers_by_store,session=None):
    result={}
    for store,offers in offers_by_store.items():
        offered_keys=set()
        for o in offers:
            if not verified_discount(o):continue
            for key in ING:
                if match_ingredient(o,key):offered_keys.add(key)
        meals,errors=fetch_discovered(offers,session=session)
        verified=[v for meal in meals if (v:=verify_meal(meal,offered_keys))]
        candidates=[v for meal in meals if
                    (v:=ingredient_confirmed_candidate(meal,offered_keys))]
        candidates.sort(key=lambda x:(-x["matched_title_terms"],
                                x["source"],x["title"]))
        result[store]={"recipes":verified[:80],
                       "ingredient_confirmed_candidates":candidates[:60],
                       "ingredient_confirmed_count":len(candidates),
                       "source_results":len(meals),
                       "verified_matches":len(verified),
                       "errors":errors}
    return result

def save(result):
    CACHE.parent.mkdir(parents=True,exist_ok=True)
    tmp=CACHE.with_suffix(".tmp")
    tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    tmp.replace(CACHE)
