"""Conservatieve indicatieve vierpersoonsvarianten voor titel-only recepten.

De titel levert uitsluitend expliciet genoemde ingrediënten. Ontbrekende
categorieën worden als aannames voor een NIEUWE variant toegevoegd, niet als
ingrediënten van het oorspronkelijke bronrecept voorgesteld.
"""
import re
from gestructureerde_recepten import norm, ALIASES
from receptenradar_catalog import ING

# Vier personen; bewust persoonlijke maaltijdvoorkeur, geen norm voor iedereen.
PORTION={"vegetables":(1200,"g"),"protein":(700,"g"),"beans":(600,"g"),
         "rice":(300,"g"),"pasta":(320,"g"),"potato":(800,"g")}
VEG={"sperziebonen","spinazie","broccoli","bloemkool","wortel","paprika",
     "courgette","boerenkool","champignons","tomaten","ui","wok","paksoi","aubergine","sperziebonen"}
PROTEIN={"kipfilet","kipdij","kipgehakt","shoarma","gehakt","zalm",
         "tonijn","tofu","tempeh","garnalen","varkenshaas","rookworst"}
BEANS={"bruine_bonen","bonen","kikkererwten","linzen"}
STARCH={"rijst","pasta","noedels","bulgur","parelcouscous","aardappel","zoete_aardappel","risottorijst","couscous"}

def mentioned(title):
    name=" "+norm(title)+" "
    matches={}
    # Voorkom "bonen" als "bruine bonen" wordt bedoeld.
    for label,key in sorted(ALIASES.items(),key=lambda pair:-len(pair[0])):
        if key not in ING or not label or len(label)<3:continue
        if re.search(r"(?<![a-z0-9])"+re.escape(label)+r"(?![a-z0-9])",name):
            if key=="bonen" and "bruine_bonen" in matches:continue
            matches[key]=label
    return list(matches)

def estimate(item):
    title=str(item.get("title") or "").strip()
    if not title or item.get("kind")=="collection":return None
    keys=mentioned(title)
    # Geen volledig maaltijdmodel bij onduidelijke titel.
    if len(keys)<2:return None
    groups={"vegetables":[k for k in keys if k in VEG],
            "protein":[k for k in keys if k in PROTEIN],
            "beans":[k for k in keys if k in BEANS],
            "starch":[k for k in keys if k in STARCH]}
    if not (groups["protein"] or groups["beans"]):return None
    if not (groups["vegetables"] or groups["starch"]):return None
    # Voor herkenbaar genoemde groepen alleen, niet gokken op ontbrekende
    # verplichte ingrediënten van het originele recept.
    lines=[]
    for group,selected in groups.items():
        if not selected:continue
        grams={"vegetables":1200,"protein":700,"beans":600,"starch":300}[group]
        if group=="starch":
            grams=800 if selected[0] in ("aardappel","zoete_aardappel") else 320 if selected[0]=="pasta" else 300
        for key in selected:
            lines.append((key,round(grams/len(selected),2),"g"))
    if len(lines)<2:return None
    return {"title":title+" (geschatte basisvariant)",
            "original_title":title,
            "source":item.get("source"),
            "url":item.get("url"),
            "cuisine":item.get("cuisine"),
            "ingredients":lines,"portions":4,
            "price_type":"estimated_variant",
            "assumptions":["Hoeveelheden volgens persoonlijke richtwaarden",
                           "Alleen expliciet genoemde ingrediënten uit de titel",
                           "Niet genoemde saus, kruiden en bijgerechten ontbreken",
                           "Geen volledig bronrecept of nutritionele garantie"]}

def candidates(items,limit=500):
    out=[];seen=set()
    for item in items:
        recipe=estimate(item)
        if recipe and (recipe["original_title"],recipe.get("source")) not in seen:
            seen.add((recipe["original_title"],recipe.get("source")))
            out.append(recipe)
        if len(out)>=limit:break
    return out
