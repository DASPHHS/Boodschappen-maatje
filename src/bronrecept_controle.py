"""Lees Recipe JSON-LD van echte bronpagina's, zonder verzonnen recepten of prijzen.

Deze controle is begrensd per halfuurscan, respecteert robots.txt en slaat
uitsluitend feitelijke verificatiemetadata op, geen volledige bereidingsteksten.
"""
import json
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from wereldkeuken_bronnen import robots_allowed, USER_AGENT
from receptenradar_catalog import ING

def recipe_nodes(tree, depth=0):
    if depth>8:return
    if isinstance(tree,list):
        for item in tree:yield from recipe_nodes(item,depth+1)
    elif isinstance(tree,dict):
        kinds=tree.get("@type") or tree.get("type") or []
        if isinstance(kinds,str):kinds=[kinds]
        if any(str(x).rstrip("/").lower().endswith("recipe") for x in kinds):
            yield tree
        for key in ("@graph","mainEntity","mainEntityOfPage","itemListElement","item","subjectOf","about"):
            if key in tree:yield from recipe_nodes(tree[key],depth+1)

def parse_yield(value):
    if isinstance(value,list):
        for item in value:
            result=parse_yield(item)
            if result:return result
        return None
    if isinstance(value,(int,float)) and 1<=value<=40:return int(value)
    text=str(value or "").lower()
    match=re.search(r"(\d{1,2})\s*(?:personen|porties|servings?|people|personen?)?\b",text)
    return int(match.group(1)) if match and 1<=int(match.group(1))<=40 else None

def matched_ingredient_keys(lines):
    keys=[]
    for line in lines:
        candidate=str(line or "").casefold()
        for key,(_,pattern,excluded) in ING.items():
            if re.search(pattern,candidate,re.I) and not re.search(excluded,candidate,re.I):
                keys.append(key)
    return sorted(set(keys))

def parse_recipe_page(html):
    soup=BeautifulSoup(html,"html.parser")
    candidates=[]
    for tag in soup.select('script[type="application/ld+json"]'):
        try:body=json.loads(tag.string or tag.get_text())
        except (ValueError,TypeError):continue
        candidates.extend(recipe_nodes(body))
    candidates.sort(key=lambda r:len(r.get("recipeIngredient") or []),reverse=True)
    for r in candidates:
        ingredients=r.get("recipeIngredient") or []
        if isinstance(ingredients,str):ingredients=[ingredients]
        if not isinstance(ingredients,list) or len(ingredients)<3:continue
        items=[str(x).strip() for x in ingredients if isinstance(x,str) and x.strip()]
        if len(items)<3:continue
        servings=parse_yield(r.get("recipeYield"))
        rating=None
        review=r.get("aggregateRating") or {}
        if isinstance(review,dict):
            try:
                number=float(review.get("ratingValue"))
                votes=float(review.get("ratingCount") or review.get("reviewCount") or 0)
                if 0<number<=5 and votes>=1:rating=round(number,2)
            except (TypeError,ValueError):pass
        return {"ingredient_count":len(items),"recognized_ingredients":matched_ingredient_keys(items),
                "servings":servings,"rating":rating,
                "level":"bronrecept_4_personen" if servings==4 else
                        "broningrediënten_beschikbaar"}
    return None

def verify_source_urls(inspiration,previous,now=None,limit=3,session=None):
    now=now or datetime.now(timezone.utc)
    old=previous or {}
    if not isinstance(old,dict):old={}
    cutoff=(now-timedelta(days=21)).date().isoformat()
    keep={url:x for url,x in old.items()
          if isinstance(x,dict) and x.get("checked_at","")[:10]>=cutoff}
    eligible=[x for x in inspiration if isinstance(x,dict) and
              x.get("url","").startswith("https://") and x.get("title")]
    # Roteer ieder half uur én bezoek een site niet meerdere keren binnen
    # drie dagen. Zo wordt de controle over de hele bibliotheek verdeeld.
    from collections import defaultdict
    pools=defaultdict(list)
    for item in eligible:
        pools[item.get("source") or "Onbekende bron"].append(item)
    for key in pools:pools[key].sort(key=lambda x:x["url"])
    # Verschillende aanbieders per run. Wikibooks gebruikt veel pagina's
    # zonder Recipe-JSON-LD; geef actieve receptenwebsites voorrang.
    sources=sorted(pools,key=lambda x:(x=="Wikibooks",x))
    slot=int(now.timestamp()//1800)
    if sources:
        turn=slot%len(sources)
        sources=sources[turn:]+sources[:turn]
    eligible=[]
    for i in range(max((len(v) for v in pools.values()),default=0)):
        for source in sources:
            candidates=pools[source]
            if not candidates:continue
            eligible.append(candidates[(i+slot//max(len(sources),1))%len(candidates)])
    checked=[]
    http=session or requests.Session()
    for candidate in eligible:
        if len(checked)>=limit:break
        url=candidate["url"].split("#")[0]
        prior=keep.get(url)
        if prior:
            try:
                timestamp=datetime.fromisoformat(prior["checked_at"])
                if timestamp.tzinfo is None:timestamp=timestamp.replace(tzinfo=timezone.utc)
                if now-timestamp<timedelta(days=3):continue
            except (ValueError,TypeError,KeyError):pass
        host=urlparse(url).hostname
        if not host:continue
        outcome={"checked_at":now.isoformat(timespec="seconds"),"level":"niet_gecontroleerd",
                 "source":candidate.get("source")}
        if not robots_allowed(url):
            outcome["reason"]="robots_ontoegankelijk"
        else:
            try:
                response=http.get(url,headers={"User-Agent":USER_AGENT,"Accept":"text/html"},
                                  timeout=9)
                response.raise_for_status()
                parsed=parse_recipe_page(response.text)
                if parsed:outcome.update(parsed)
                else:outcome["reason"]="geen_bruikbare_receptmetadata"
            except requests.RequestException as exc:
                outcome["reason"]="netwerk_"+type(exc).__name__
        keep[url]=outcome
        checked.append({"source":candidate.get("source"),"url":url,
                        "level":outcome["level"],"reason":outcome.get("reason")})
    # Bewaar alleen gespreid recente controles, zonder persoonsgegevens.
    return dict(list(keep.items())[-1200:]),checked
