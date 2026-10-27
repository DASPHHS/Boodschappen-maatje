"""Extract verifiable recipe details from embedded Schema.org/Recipe JSON-LD.

No copied instructions, no guessed recipe ingredients. For sites without
valid JSON-LD fields this extractor returns a clear rejection reason.
"""
import json,re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from gestructureerde_recepten import ALIASES,norm

def walk(obj):
    if isinstance(obj,list):
        for x in obj:yield from walk(x)
    if not isinstance(obj,dict):return
    typ=obj.get("@type") or ""
    types=typ if isinstance(typ,list) else [typ]
    if any(str(t).split("/")[-1]=="Recipe" for t in types):yield obj
    for key in ("@graph","mainEntity","itemListElement","item"):
        if key in obj:yield from walk(obj[key])

def amount(line):
    if not isinstance(line,str):return None
    m=re.match(r"^\s*(\d+(?:[,.]\d+)?)\s*(kg|gram|gr|g|ml|l|liter|stuks?|st)\s+(.+?)\s*$",line,re.I)
    if not m:return None
    qty=float(m.group(1).replace(",","."));unit=m.group(2).lower()
    if unit=="kg":qty*=1000;unit="g"
    elif unit in ("gram","gr"):unit="g"
    elif unit in ("liter","l"):qty*=1000;unit="ml"
    elif unit.startswith("st"):unit="st"
    label=norm(m.group(3))
    key=ALIASES.get(label)
    if not key:return None
    return {"name":key,"quantity":qty,"unit":unit}

def count_servings(raw):
    if isinstance(raw,list):raw=raw[0] if raw else None
    if isinstance(raw,dict):raw=raw.get("value") or raw.get("name")
    s=str(raw or "")
    m=re.search(r"\b(\d{1,2})\s*(?:personen|porties|servings|people|personen)?\b",s,re.I)
    return int(m.group(1)) if m and 1<=int(m.group(1))<=24 else None

def minutes(raw):
    m=re.fullmatch(r"P(?:T)?(?:(\d+)H)?(?:(\d+)M)?",str(raw or ""),re.I)
    return int(m.group(1) or 0)*60+int(m.group(2) or 0) if m else None

def extract(html,url):
    if not isinstance(url,str) or urlparse(url).scheme!="https":return None,"unsafe_url"
    soup=BeautifulSoup(html,"html.parser")
    reasons=[]
    for tag in soup.select('script[type="application/ld+json"]'):
        try:data=json.loads(tag.string or tag.get_text())
        except (TypeError,ValueError):continue
        for item in walk(data):
            lines=item.get("recipeIngredient") or item.get("ingredients") or []
            if not isinstance(lines,list) or not lines:reasons.append("no_ingredients");continue
            parsed=[amount(line) for line in lines]
            if any(x is None for x in parsed):reasons.append("incomplete_quantities_or_unknown_ingredient");continue
            servings=count_servings(item.get("recipeYield"))
            duration=minutes(item.get("totalTime"))
            if not servings or duration is None:reasons.append("missing_servings_or_duration");continue
            title=str(item.get("name") or "").strip()
            if not title:reasons.append("missing_title");continue
            return {"title":title,"source":urlparse(url).netloc,
                "url":url,"servings":servings,"minutes":duration,
                "cuisine":item.get("recipeCuisine"),"ingredients":parsed,
                "kind":"recipe","verification":"schema_recipe_complete"},None
    return None,(reasons[0] if reasons else "no_structured_recipe")
