"""Open receptenindex voor Koopkracht.

Haalt uitsluitend titels en originele links op uit de Wikibooks Cookbook
via de officiële Wikimedia API. Kopieert geen HelloFresh-instructies/foto's.
"""
import json,time,sys
from datetime import datetime,timezone
from pathlib import Path
import requests

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
    data={"updated_at":datetime.now(timezone.utc).isoformat(),
          "attribution":"Wikibooks bijdragers, CC BY-SA 4.0: https://en.wikibooks.org/wiki/Cookbook:Recipes",
          "description":"Recepttitels met links naar de originele bron. Geen volledige recepten, geverifieerde ingrediënten of supermarktprijzen.",
          "items":items}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(data,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    print("Receptindex items:",len(items),"Wikibooks:",len(found))
if __name__=="__main__":main()
