#!/usr/bin/env python3
"""Conservative weekly discovery using publisher's public recipe sitemap.
Only canonical links, titles and factual metadata are retained, never full
publisher instructions, text, photos, or raw copyrighted recipes.
A failed source request keeps the previously curated collection intact.
"""
import datetime as dt
import json
import os
import re
import time
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parent.parent
TARGET=ROOT/"docs/data/publisher-recipes.json"
SITEMAP="https://www.ah.nl/sitemaps/entities/allerhande/recipes.xml"
FAMILIES={
 "riblappen":r"\b(?:riblappen|riblap|sukadelappen|sukadelap|stooflappen)\b",
 "gehakt":r"\b(?:gehakt|gehaktballen|rundergehakt|varkensgehakt)\b",
 "kip":r"\b(?:kip|kipfilet|kipdij|kippen|kipcurry|kipkerrie|kipstoof|kipschotel|kipwok|kipovenschotel)\b",
 "zalm":r"\b(?:zalm|zalmfilet)\b",
 "witvis":r"\b(?:kabeljauw|koolvis|scholfilet|pangasius|witvis|heek)\b",
 "garnalen":r"\b(?:garnalen|scampi)\b",
 "tofu":r"\b(?:tofu|tempeh)\b",
 "kikkererwten":r"\b(?:kikkererwten|kikkererwt)\b",
 "linzen":r"\b(?:linzen|linzenstoof|dahl)\b",
 "broccoli":r"\b(?:broccoli|broccoliroosjes)\b",
 "bloemkool":r"\b(?:bloemkool|bloemkoolroosjes)\b",
 "spinazie":r"\b(?:spinazie|bladspinazie)\b",
 "pompoen":r"\b(?:pompoen|flespompoen)\b",
 "paprika":r"\b(?:paprika|paprikas)\b",
 "courgette":r"\b(?:courgette|courgettes)\b",
 "aubergine":r"\b(?:aubergine|aubergines)\b",
 "sperziebonen":r"\b(?:sperziebonen|sperzieboontjes)\b",
 "tomaten":r"\b(?:tomaten|tomaat|trostomaten|cherrytomaten)\b",
 "aardappelen":r"\b(?:aardappelen|aardappel|krieltjes)\b",
 "eieren":r"\b(?:eieren|ei|scharrelei)\b",
 "pindakaas":r"\bpindakaas\b",
 "champignons":r"\b(?:champignons|paddenstoelen|kastanjechampignons)\b",
 "wortel":r"\b(?:wortel|wortels|winterpeen|bospeen)\b",
 "paksoi":r"\bpaksoi\b",
 "prei":r"\bprei\b",
 "spitskool":r"\bspitskool\b",
 "boerenkool":r"\bboerenkool\b",
 "bonen":r"\b(?:kidneybonen|witte bonen|zwarte bonen|bruine bonen)\b",
 "venkel":r"\bvenkel\b"
}
VEG={"broccoli","bloemkool","spinazie","pompoen","paprika","courgette",
     "aubergine","sperziebonen","tomaten","champignons","wortel","paksoi",
     "prei","spitskool","boerenkool","venkel"}
LEGUMES={"kikkererwten","linzen","bonen"}
MEAT={"riblappen","gehakt","kip","zalm","witvis","garnalen"}
EXCLUDE=re.compile(r"(?:baby|peuter|advertorial|advertentie|verspakket|ovenmaaltijd|kindervoeding|voorgerecht|nagerecht|dessert)",re.I)
USER_AGENT="Boodschappenmaatje/1.0 (limited publisher recipe metadata verification)"
def fetch(url,max_bytes=17_000_000):
    if urlparse(url).netloc not in ("www.ah.nl","ah.nl"):
        raise ValueError("Untrusted recipe domain")
    with urlopen(Request(url,headers={"User-Agent":USER_AGENT,"Accept":"text/html,application/xml"}),timeout=18) as res:
        if res.status!=200:raise OSError("Recipe source not OK")
        raw=res.read(max_bytes+1)
        if len(raw)>max_bytes:raise ValueError("Publisher response too large")
        return raw.decode("utf-8",errors="replace")
def schema_recipes(html):
    # structured metadata, not original instructional text
    result=[]
    for blob in re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script\s*>',html,re.I|re.S):
        try:data=json.loads(blob)
        except (ValueError,TypeError):continue
        stack=[data]
        while stack:
            entry=stack.pop()
            if isinstance(entry,list):stack.extend(entry);continue
            if not isinstance(entry,dict):continue
            for child in ("@graph","mainEntity","itemListElement"):
                if child in entry:stack.append(entry[child])
            types=entry.get("@type",[])
            if isinstance(types,str):types=[types]
            if "Recipe" in types:result.append(entry)
    return result
def minutes(text):
    if isinstance(text,list):text=text[0] if text else ""
    value=str(text or "")
    match=re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?",value)
    if match:
        days,hours,mins=(int(x or 0) for x in match.groups())
        return days*1440+hours*60+mins
    return None
def families_of(*strings):
    description=" ".join(str(x) for x in strings).lower()
    return sorted(key for key,expr in FAMILIES.items() if re.search(expr,description))
def to_record(url,meta,stamp):
    title=str(meta.get("name") or "").strip()
    raw=meta.get("recipeIngredient") or []
    if isinstance(raw,str):raw=[raw]
    if (len(title)<9 or len(title)>150 or EXCLUDE.search(title)
        or not isinstance(raw,list) or len(raw)<5):return None
    tags=families_of(*[i for i in raw if isinstance(i,str)])
    if not tags:return None
    has_veg=len(VEG.intersection(tags))
    has_legume=bool(LEGUMES.intersection(tags))
    if not(has_veg or has_legume):return None  # vegetable / legume present
    category=str(meta.get("recipeCategory") or "").lower()
    if category and not any(k in category for k in ("hoofd","main","dinner","avond","maaltijd")):return None
    total=minutes(meta.get("totalTime")) or minutes(meta.get("cookTime"))
    if total is not None and not 10<=total<=240:return None
    recipe_yield=meta.get("recipeYield")
    servings=None
    match=re.search(r"\b([2-8])\b",str(recipe_yield or ""))
    if match:servings=int(match.group(1))
    if servings is not None and servings not in (2,3,4,5,6):return None
    method=next((m for m in ("curry","stoof","wok","oven","soep","salade","pasta","rijst","stamppot","noedel","tajine")
       if m in title.lower()),"anders")
    return {"id":"ah-auto-"+re.search(r"/(R-R\d+)/",url).group(1).lower() if re.search(r"/(R-R\d+)/",url) else "ah-auto-"+str(abs(hash(url))),
       "title":title,"source":"Allerhande","url":url.split("?")[0],"families":tags,
       "minutes":total,"servings":servings,"course":"hoofdgerecht",
       "method":method,"vegetable_families":has_veg,"has_legumes":has_legume,
       "review_status":"publisher_metadata_verified","last_checked":stamp}
def candidates(sitemap,existing,today):
    root=ET.fromstring(sitemap)
    urls=[]
    for item in root.iter():
        if not item.tag.endswith("loc") or not item.text:continue
        url=item.text.strip()
        if not re.fullmatch(r"https://www\.ah\.nl/allerhande/recept/R-R\d+/[a-z0-9-]+",url):continue
        if url in existing or EXCLUDE.search(url):continue
        slug=url.rsplit("/",1)[-1].replace("-"," ")
        groups=families_of(slug)
        if not groups:continue
        urls.append((url,groups))
    # Deterministic per week; prioritize undercovered families without a fixed category bias
    existing_counts=Counter(key for r in existing.values() for key in r.get("families",[]))
    week=int(today.isocalendar().week)
    return sorted(urls,key=lambda pair:(min(existing_counts[f] for f in pair[1]),(sum(ord(c) for c in pair[0])+week*137)%10007))
def sitemap_record(url,stamp):
    """Title-only discovery. URL is from AH's official sitemap, not a verified recipe."""
    match=re.fullmatch(r"https://www\.ah\.nl/allerhande/recept/(R-R\d+)/([a-z0-9-]+)",url)
    if not match:return None
    words=match.group(2).replace("-"," ")
    tags=families_of(words)
    veg=VEG.intersection(tags)
    pulse=LEGUMES.intersection(tags)
    # Title must describe a meaningful meal with a vegetable/legume
    # and at least one more known ingredient. No dessert / marketing / baby food.
    if len(tags)<2 or not (veg or pulse) or EXCLUDE.search(words):return None
    preparation=("curry","stoof","wok","roerbak","oven","pasta","rijst",
       "dahl","tajine","risotto","stamppot","noedels","gevulde","schotel",
       "gegrilde","gebakken","salade","bowl")
    method=next((m for m in preparation if m in words),None)
    if not method:return None
    title=" ".join(w.capitalize() if i==0 else w for i,w in enumerate(words.split()))
    return {"id":"ah-sitemap-"+match.group(1).lower(),"title":title,
       "source":"Allerhande","url":url,"families":tags,
       "minutes":None,"servings":None,"course":"niet_gecontroleerd",
       "method":method,"vegetable_families":len(veg),
       "has_legumes":bool(pulse),
       "review_status":"publisher_sitemap_title_only","last_checked":stamp}

def sync(today=None,max_pages=28):
    today=today or dt.date.today()
    data=json.loads(TARGET.read_text(encoding="utf-8"))
    existing={r["url"]:r for r in data["recipes"] if isinstance(r.get("url"),str)}
    try:items=candidates(fetch(SITEMAP),existing,today)
    except (OSError,ValueError,ET.ParseError) as exc:
        print("Sitemap unavailable, keeping reviewed recipes:",str(exc)[:220]);return 0
    added=0;checked=0;methods=Counter()
    for url,_ in items:
        if checked>=max_pages or len(existing)>=225:break
        try:
            page=fetch(url,1_100_000)
            records=schema_recipes(page)
        except (OSError,ValueError) as exc:
            # AH blocks automated recipe pages with HTTP 403, even though the
            # official sitemap is public. Never pretend we saw Recipe JSON-LD.
            records=[]
        checked+=1
        record=next((x for meta in records
            if (x:=to_record(url,meta,today.isoformat()))),None)
        if not record:
            record=sitemap_record(url,today.isoformat())
        if record and url not in existing and methods[record["method"]]<(5 if record["review_status"]=="publisher_sitemap_title_only" else 7):
            existing[url]=record
            methods[record["method"]]+=1
            added+=1
        time.sleep(.22)
    if added:
        data["recipes"]=list(existing.values())
        data["generated_at"]=today.isoformat()
        TARGET.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Recipe metadata sync: inspected {checked}, published {added}, total {len(existing)}")
    return added
if __name__=="__main__":
    import sys
    if "--check" in sys.argv:
        assert len(json.loads(TARGET.read_text())["recipes"])>=30
        print("Publisher recipe index format OK")
    else:
        sync()
