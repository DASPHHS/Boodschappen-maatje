"""Maak uitsluitend controleerbare bronrecepten geschikt voor de bestaande prijsengine.

Titelmatches of een gedeeltelijke ingrediëntenlijst krijgen nooit een kassaprijs.
Alle niet-voorraad-ingrediënten vereisen naam, hoeveelheid, eenheid en porties.
"""
import json, math, re, unicodedata
from pathlib import Path
from receptenradar_catalog import ING

ROOT=Path(__file__).resolve().parents[1]
ARCHIVES=("geverifieerde_bronrecepten.json","hello-fresh-kaarten.json","hello-fresh-maart-archief.json",
          "eigen-archief.json","surinaams-archief.json","inspiratie.json")

def norm(text):
    text=unicodedata.normalize("NFKD",str(text or "").casefold())
    return re.sub(r"\s+"," ",re.sub(r"[^a-z0-9 ]"," ","".join(c for c in text if not unicodedata.combining(c)))).strip()

ALIASES={
 "aardappelen":"aardappel","aardappels":"aardappel",
 "kastanjechampignons":"champignons","champignon":"champignons",
 "kippendijfilet":"kipdij","kipdijreepjes":"kipdij",
 "kipfiletblokjes":"kipfilet","zilvervliesrijst":"rijst",
 "basmati rijst":"rijst","witte rijst":"rijst",
 "bruine bonen":"bruine_bonen","bruinebonen":"bruine_bonen",
 "sperziebonen":"sperziebonen","sperzieboontjes":"sperziebonen",
}
for key,metadata in ING.items():
    ALIASES.setdefault(norm(key.replace("_"," ")),key)
    ALIASES.setdefault(norm(metadata[0]),key)

def convert(item):
    if not isinstance(item,dict) or item.get("kind")=="collection":return None,"not_recipe"
    title=str(item.get("title") or "").strip()
    ingredients=item.get("ingredients")
    portions=item.get("servings")
    if not title or not isinstance(ingredients,list) or not ingredients:
        return None,"no_complete_ingredient_list"
    try:
        portions=float(portions)
        if not math.isfinite(portions) or portions<=0:return None,"invalid_servings"
    except (TypeError,ValueError):return None,"invalid_servings"
    lines={}
    for ingredient in ingredients:
        if not isinstance(ingredient,dict):return None,"unstructured_ingredient"
        key=ALIASES.get(norm(ingredient.get("name")))
        unit=norm(ingredient.get("unit"))
        try:amount=float(ingredient.get("quantity"))
        except (TypeError,ValueError):return None,"missing_quantity"
        if key not in ING or unit not in ("g","ml","st") or not math.isfinite(amount) or amount<=0:
            return None,"unmapped_ingredient"
        if key in lines:
            if lines[key][1]!=unit:return None,"mixed_units"
            lines[key]=(lines[key][0]+amount,unit)
        else:lines[key]=(amount,unit)
    if len(lines)<3:return None,"too_few_ingredients"
    quantities=[(k,round(q*4/portions,3),unit) for k,(q,unit) in lines.items()]
    return {"title":title,"category":item.get("category") or "Vegetarisch",
            "minutes":item.get("minutes"),"ingredients":quantities,
            "source":item.get("source"),"url":item.get("url"),
            "cuisine":item.get("cuisine"),"source_servings":portions},None

def load(root=ROOT):
    accepted=[];rejected={};seen=set()
    for archive in ARCHIVES:
        path=Path(root)/"recepten"/archive
        if not path.exists():continue
        try:items=json.loads(path.read_text(encoding="utf-8")).get("items",[])
        except (ValueError,OSError,AttributeError):rejected["broken_archive"]=rejected.get("broken_archive",0)+1;continue
        for item in items:
            recipe,reason=convert(item)
            if reason:
                rejected[reason]=rejected.get(reason,0)+1;continue
            id=(norm(recipe["title"]),tuple(recipe["ingredients"]))
            if id in seen:continue
            seen.add(id);accepted.append(recipe)
    return accepted,rejected
