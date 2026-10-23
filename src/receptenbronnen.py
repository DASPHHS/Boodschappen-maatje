"""Open receptenindex voor Koopkracht.

Haalt uitsluitend titels en originele links op uit de Wikibooks Cookbook
via de officiële Wikimedia API. Kopieert geen HelloFresh-instructies/foto's.
"""
import json,time,sys,re
from datetime import datetime,timezone
from pathlib import Path
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"recepten"/"inspiratie.json"
API="https://en.wikibooks.org/w/api.php"
HEADERS={"User-Agent":"Koopkracht-Receptenradar/1.0 (educational recipe-discovery; https://github.com/DASPHHS/koopkracht)"}
HF=[
("Boerenkool met dragonroomsaus en garnalen","Vis",20,"https://www.hellofresh.nl/recipes/boerenkool-met-dragonroomsaus-en-garnalen-68116bbf5917498f8bf2c1c1"),
("Kip met harissa en geroosterde bloemkool","Kip",35,"https://www.hellofresh.nl/recipes/kip-met-harissa-en-geroosterde-bloemkool-63c7d3dd788f6ee4ca33d7d2"),
("Kippendij met harissa en yoghurtsaus","Kip",35,"https://www.hellofresh.nl/recipes/harissa-chicken-and-vegetable-traybake-6936c622dce6a2dc39a735c0"),
("Klassieke boerenkoolstamppot met rookworst","Vlees",30,"https://www.hellofresh.nl/recipes/klassieke-boerenkoolstamppot-met-rookworst-566f10164dab71d3128b4567"),
("Boerenkoolsalade met rookworst en spekjes","Vlees",40,"https://www.hellofresh.nl/recipes/boerenkoolsalade-met-rookworst-en-spekjes-5f86f35777bcc819dd39faa0"),
("Boerenkoolstamppot met spekreepjes en uienjus","Vlees",35,"https://www.hellofresh.nl/recipes/boerenkoolstamppot-met-rookworst-63d3aefcdd4a18d65316aeaf"),
("Stamppot met rookworst en krokante boerenkool","Vlees",35,"https://www.hellofresh.nl/recipes/stamppot-met-rookworst-en-krokante-boerenkool-6391e9724bdbc9204b08aa7f"),
]
def category(name):
    s=name.casefold()
    if any(w in s for w in ["salmon","fish","tuna","cod","shrimp","prawn","seafood","herring","tilapia","trout","sardine"]):return "Vis"
    if any(w in s for w in ["chicken","poultry","turkey"]):return "Kip"
    if any(w in s for w in ["beef","pork","lamb","meatball","sausage","bacon","ham ","steak"]):return "Vlees"
    return "Overig/onbekend"
SOURCES=([
  ("The Meal Prep Manual","https://mealprepmanual.com/recipes/","mealprepmanual.com"),
  ("Budget Bytes mealprep","https://www.budgetbytes.com/category/extra-bytes/budget-friendly-meal-prep/","www.budgetbytes.com"),
  ("FitMenCook mealprep","https://fitmencook.com/recipes/category/meal-prep/","fitmencook.com"),
] +
  [("The Meal Prep Manual", "https://mealprepmanual.com/recipes/?_page="+str(i), "mealprepmanual.com") for i in range(2,9)] +
  [("Budget Bytes mealprep", "https://www.budgetbytes.com/category/extra-bytes/budget-friendly-meal-prep/page/"+str(i)+"/", "www.budgetbytes.com") for i in range(2,4)] +
  [("FitMenCook mealprep", "https://fitmencook.com/recipes/category/meal-prep/page/"+str(i)+"/", "fitmencook.com") for i in range(2,4)])
def extra_mealprep_links():
    """Indexeer uitsluitend publieke titels en artikel-URL's, geen recepten of foto's."""
    result=[]
    for source,landing,host in SOURCES:
        try:
            response=requests.get(landing,headers=HEADERS,timeout=25)
            response.raise_for_status()
            soup=BeautifulSoup(response.text,"html.parser")
            seen=set()
            for a in soup.select("h2 a[href], h3 a[href], h4 a[href], article a[href], .post-summary a[href]"):
                href=a.get("href","").split("#")[0]
                title=a.get_text(" ",strip=True)
                if len(title)<10 or len(title)>130:continue
                if not href.startswith("https://"+host+"/"):continue
                if source=="FitMenCook mealprep" and "/recipes/" not in href:continue
                if any(v in href for v in ["/category/","/tag/","/shop/","/page/","/meal-plans/","/index/"]):continue
                if href.rstrip("/")==landing.rstrip("/") or href in seen:continue
                if re.search(r"sign up|subscribe|see all|home page|learn more|next page|read more|about us|recipe index|start here",title,re.I):continue
                if re.fullmatch(r"(categories|meal plans|surprise me|giveaways|contact|blog|news|search)",title,re.I):continue
                # Amerikaanse dollars op bronpagina zijn geen supermarktprijs.
                title=re.sub(r"\s*\$\d+(?:\.\d+)?(?:\s*(?:recipe|serving|per serving|/))*.*$", "",title).strip()
                if len(title)<10:continue
                seen.add(href)
                result.append({"title":title,"source":source,"category":category(title),
                               "minutes":None,"url":href,"price_status":"Niet doorgerekend"})
                if len(seen)>=100:break
            print(source,"receptlinks gevonden:",len(seen))
        except Exception as exc:
            print(source,"niet beschikbaar:",exc,file=sys.stderr)
    return result

def main():
    items=[{"title":title,"source":"HelloFresh","category":cat,"minutes":minutes,"url":url} for title,cat,minutes,url in HF]
    found=set()
    cursor=None
    try:
        for _ in range(30):
            params={"action":"query","list":"categorymembers","cmtitle":"Category:Recipes",
                    "cmlimit":"500","cmtype":"page","format":"json","formatversion":2}
            if cursor:params["cmcontinue"]=cursor
            r=requests.get(API,params=params,headers=HEADERS,timeout=30)
            r.raise_for_status();body=r.json()
            for page in body.get("query",{}).get("categorymembers",[]):
                title=page.get("title","")
                if not title.startswith("Cookbook:"):continue
                if title in found:continue
                found.add(title)
                label=title.split(":",1)[1]
                url="https://en.wikibooks.org/wiki/"+requests.utils.quote(title.replace(" ","_"),safe="/:")
                items.append({"title":label,"source":"Wikibooks","category":category(label),"minutes":None,"url":url})
            cursor=body.get("continue",{}).get("cmcontinue")
            if not cursor:break
            time.sleep(.15)
    except Exception as exc:
        print("Wikibooks fetch failed:",exc,file=sys.stderr)
        # Geen lege of fictieve dataset publiceren als de bron platligt.
        if OUT.exists():
            old=json.loads(OUT.read_text(encoding="utf-8"))
            if len(old.get("items",[]))>len(HF):return
    # Titels uit eigen archief staan los van de publieke scans en kunnen later
    # veilig door de receptcalculator worden omgezet naar originele varianten.
    own=ROOT/"recepten"/"eigen-archief.json"
    if own.exists():
        items.extend(json.loads(own.read_text(encoding="utf-8")).get("items",[]))
    items.extend(extra_mealprep_links())
    seenkeys=set();unique=[]
    for item in items:
        key=(item.get("source"),item.get("url") or item.get("local_page"))
        if key in seenkeys:continue
        seenkeys.add(key);unique.append(item)
    priorities={"Mijn HelloFresh-archief":0,"HelloFresh":1,"The Meal Prep Manual":2,"FitMenCook mealprep":3,"Budget Bytes mealprep":4,"Wikibooks":5}
    items=sorted(unique,key=lambda v:(priorities.get(v.get("source"),9), v.get("title","").casefold()))
    data={"updated_at":datetime.now(timezone.utc).isoformat(),
          "attribution":"Wikibooks bijdragers, CC BY-SA 4.0: https://en.wikibooks.org/wiki/Cookbook:Recipes",
          "description":"Recepttitels met links naar de originele bron. Geen volledige recepten, geverifieerde ingrediënten of supermarktprijzen.",
          "items":items}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(data,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    print("Receptindex items:",len(items),"Wikibooks:",len(found))
if __name__=="__main__":main()
