"""Bronregister voor wereldkeukens: openbare receptlinks, geen overname recepten.

Deze pagina's zijn ingangen voor *zoeken*. Een gevonden link betekent niet
dat porties/ingrediënten/prijs al zijn geverifieerd. Per host respecteer
robots.txt en gebruik uitsluitend publiek zichtbare titels + links.
"""
import re
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from functools import lru_cache
from datetime import datetime,timezone
import requests
from bs4 import BeautifulSoup

USER_AGENT="BoodschappenMaatjeRecipeIndex/1.1 (personal recipe discovery; https://github.com/DASPHHS/Boodschappen-maatje)"
# Naam, keuken, inhoudelijke bronpagina. Het register claimt geen automatische
# toegang tot iedere site: foutstatus wordt expliciet bijgehouden.
WORLD_SOURCES=[
 ("AH Allerhande · Surinaams","Surinaams","https://www.ah.nl/allerhande/recepten/surinaamse-recepten"),
 ("Jumbo · Surinaams","Surinaams","https://www.jumbo.com/recepten/zoeken/surinaams"),
 ("Faja Lobi · Sandhia","Surinaams","https://www.fajalobi.nl/recepten"),
 ("SurinamCooking","Surinaams","https://surinamcooking.com/"),
 ("Sranang Kukru","Surinaams","https://sranangkukru.net/recept-with-pic/"),
 ("Francesca Kookt · Surinaams","Surinaams","https://www.francescakookt.nl/surinaamse-recepten/"),
 ("Foodies · Surinaams","Surinaams","https://www.foodiesmagazine.nl/inspiratie/surinaamse-gerechten/"),
 ("delicious. · Surinaams","Surinaams","https://deliciousmagazine.nl/lijstjes/surinaamse-recepten/"),
 ("24Kitchen · Surinaams","Surinaams","https://www.24kitchen.nl/recepten/surinaamse-bami"),
 ("AH Allerhande · Indonesisch","Indonesisch","https://www.ah.nl/allerhande/recepten/indonesische-recepten"),
 ("AH Allerhande · Indiaas","Indiaas","https://www.ah.nl/allerhande/recepten/indiase-recepten"),
 ("AH Allerhande · Thais","Thais","https://www.ah.nl/allerhande/recepten/thaise-recepten"),
 ("AH Allerhande · Vietnamees","Vietnamees","https://www.ah.nl/allerhande/recepten/vietnamese-recepten"),
 ("AH Allerhande · Koreaans","Koreaans","https://www.ah.nl/allerhande/recepten/koreaanse-recepten"),
 ("AH Allerhande · Japans","Japans","https://www.ah.nl/allerhande/recepten/japanse-recepten"),
 ("AH Allerhande · Chinees","Chinees","https://www.ah.nl/allerhande/recepten/chinese-recepten"),
 ("AH Allerhande · Turks","Turks","https://www.ah.nl/allerhande/recepten/turkse-recepten"),
 ("AH Allerhande · Marokkaans","Marokkaans","https://www.ah.nl/allerhande/recepten/marokkaanse-recepten"),
 ("AH Allerhande · Libanees","Libanees","https://www.ah.nl/allerhande/recepten/libanese-recepten"),
 ("AH Allerhande · Grieks","Grieks","https://www.ah.nl/allerhande/recepten/griekse-recepten"),
 ("AH Allerhande · Italiaans","Italiaans","https://www.ah.nl/allerhande/recepten/italiaanse-recepten"),
 ("AH Allerhande · Mexicaans","Mexicaans","https://www.ah.nl/allerhande/recepten/mexicaanse-recepten"),
 ("AH Allerhande · Spaans","Spaans","https://www.ah.nl/allerhande/recepten/spaanse-recepten"),
 ("AH Allerhande · Nederlands","Nederlands","https://www.ah.nl/allerhande/recepten/nederlandse-recepten"),
 ("Jumbo · Wereldkeukens","Wereldkeukens","https://www.jumbo.com/recepten"),
 ("LeukeRecepten · Aziatisch","Aziatisch","https://www.leukerecepten.nl/aziatisch/"),
 ("24Kitchen · Wereldkeukens","Wereldkeukens","https://www.24kitchen.nl/recepten"),
 ("Allerhande · Magazine-archief","Kookmagazines","https://www.ah.nl/allerhande/magazines"),
 ("Jumbo JUMMM · Magazine en weekmenu's","Kookmagazines","https://www.jumbo.com/recepten"),
 ("Lidl · Recepten en seizoensmagazines","Kookmagazines","https://www.lidl.nl/"),
 ("PLUS · Recepten","Wereldkeukens","https://www.plus.nl/recepten"),
 ("Dirk · Recepten","Wereldkeukens","https://www.dirk.nl/meer/recepten"),
 ("BBC Good Food · Caribisch","Caribisch","https://www.bbcgoodfood.com/recipes/collection/caribbean-recipes"),
 ("BBC Good Food · Marokkaans","Marokkaans","https://www.bbcgoodfood.com/recipes/collection/moroccan-recipes"),
 ("24Kitchen · Familierecepten","Wereldkeukens","https://www.24kitchen.nl/thema/zoals-alleen-oma-dat-kan-recepten"),
]
# Bron kan opnieuw toegankelijk worden; een tijdelijke 403/timeout geeft geen
# recht om willekeurig een URL als verifieerbaar recept te behandelen.
LINK_RULES={
 "www.ah.nl":r"^/allerhande/recept/R-[A-Za-z0-9-]+",
 "www.jumbo.com":r"^/recepten/(?!zoeken|surinaams|$)[^?#]+",
 "www.fajalobi.nl":r"^/recepten/[^?#]+",
 "surinamcooking.com":r"^/(?!category|tag|page|feed|wp-)[^?#]+",
 "sranangkukru.net":r"^/(?!category|tag|page|recept-with-pic|wp-)[^?#]+",
 "www.francescakookt.nl":r"^/(?!tag|category|page|surinaamse-recepten)[^?#]+",
 "www.foodiesmagazine.nl":r"^/recepten/[^?#]+",
 "deliciousmagazine.nl":r"^/recepten/[^?#]+",
 "www.24kitchen.nl":r"^/recepten/[^?#]+",
 "www.leukerecepten.nl":r"^/recepten/[^?#]+",
 "www.plus.nl":r"^/recepten/[^?#]+",
 "www.dirk.nl":r"^/meer/recepten/[^?#]+",
 "www.bbcgoodfood.com":r"^/recipes/(?!collection/)[^?#]+",
}
BANNED_TITLE=re.compile(r"^(recepten|naar het recept|bekijk recept|lees meer|read more|bekijk alle|"
                        r"meer informatie|gerelateerde recepten|maak dit recept|toon meer|"
                        r"weekmenu|voorbereiding|bekijk het volledige recept|bekijk volledige recept)$",re.I)

@lru_cache(maxsize=45)
def robots_allowed(url):
    parsed=urlparse(url)
    rp=RobotFileParser()
    try:
        response=requests.get(f"{parsed.scheme}://{parsed.netloc}/robots.txt",
                              headers={"User-Agent":USER_AGENT},timeout=5)
        if response.status_code==404:
            return True
        if response.status_code!=200:
            return False
        rp.parse(response.text.splitlines())
        return rp.can_fetch(USER_AGENT,url)
    except requests.RequestException:
        return False

def parse_links(html,landing,source,cuisine,limit=60):
    """Extraheer alleen originele artikel-URL's met betekenisvolle titel."""
    soup=BeautifulSoup(html,"html.parser")
    seen=set()
    host=urlparse(landing).netloc.casefold()
    pattern=LINK_RULES.get(host)
    if not pattern:return []
    result=[]
    for a in soup.select("article a[href], h2 a[href], h3 a[href], h4 a[href], a[href]"):
        url=urljoin(landing,a.get("href","")).split("#")[0].split("?")[0]
        u=urlparse(url)
        if u.scheme!="https" or u.netloc.casefold()!=host:continue
        if not re.search(pattern,u.path,re.I):continue
        if url.rstrip("/")==landing.rstrip("/") or url in seen:continue
        title=" ".join(a.get_text(" ",strip=True).split())
        if len(title)<8 or len(title)>125 or BANNED_TITLE.search(title):continue
        if title.lower() in ("bekijk","meer","recept","details","naar recept"):continue
        # Titels/links, geen teksten of illustraties; hergebruik voorkomt doublures.
        seen.add(url)
        result.append({"title":title,"source":source,"cuisine":cuisine,
                       "category":"Overig/onbekend","minutes":None,"url":url,
                       "verification":"Bronlink ontdekt, ingrediënten niet gecontroleerd",
                       "discovered_at":datetime.now(timezone.utc).date().isoformat(),
                       "price_status":"Niet doorgerekend"})
        if len(result)>=limit:break
    return result

def collect_world_links(session=None,limit_per_source=50,max_sources=None):
    http=session or requests.Session()
    results=[];status=[]
    # Dagelijkse rotatie: elke drie dagen komt iedere bron aan bod.
    shard=datetime.now(timezone.utc).date().toordinal()%3
    sources=WORLD_SOURCES[shard::3] if max_sources is None else WORLD_SOURCES[:max_sources]
    for source,cuisine,url in sources:
        if not robots_allowed(url):
            status.append({"source":source,"status":"robots-blokkade of robots onbekend","count":0})
            continue
        try:
            response=http.get(url,headers={"User-Agent":USER_AGENT,
                                             "Accept":"text/html"},timeout=10)
            response.raise_for_status()
            links=parse_links(response.text,url,source,cuisine,limit_per_source)
            results.extend(links)
            status.append({"source":source,"status":"bereikbaar","count":len(links)})
        except requests.RequestException as exc:
            status.append({"source":source,"status":"niet bereikbaar: "+type(exc).__name__,"count":0})
    return results,status
