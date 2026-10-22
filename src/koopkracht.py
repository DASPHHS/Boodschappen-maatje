"""Koopkracht scanner: publieke winkel-/folderlinks, tekstuele acties en optionele OCR."""
import argparse, csv, hashlib, html, json, os, re, time, urllib.parse, urllib.robotparser
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
import requests
from bs4 import BeautifulSoup

BASE="https://www.allefolders.nl"
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"; DOCS=ROOT/"docs"
HEADERS={"User-Agent":"KoopkrachtResearchBot/1.0 (personal deal index; respectful rate limiting)"}
PAGE_TYPES=("/winkels", "/nieuw", "/aanbiedingen", "/supermarkten", "/categorieen")
FOLDER_RX=re.compile(r"/([^/?#]+-aanbiedingen)/([a-f0-9-]{16,})(?:/\d+)?/?$",re.I)
PRICE_RX=re.compile(r"(?:€\s*|\beur\s*)(\d{1,4}[,.]\d{2})\b")
AMOUNT_RX=re.compile(r"(?<!\d)(\d{1,4}[,.]\d{2})\s*€")
STORE_PATTERN=re.compile(r"/(?:[a-z0-9-]+-aanbiedingen|winkels(?:/[^/?#]+)?)/?",re.I)
SESSION=requests.Session(); SESSION.headers.update(HEADERS)
ROBOTS={}

def safe_url(url):
    try:
        p=urllib.parse.urlparse(url)
        return p.scheme=="https" and p.hostname in {"www.allefolders.nl","allefolders.nl","cdn.jafolders.com"}
    except (TypeError, ValueError): return False

def normalise_name(name):
    return re.sub(r"\s+"," ",re.sub(r"[^\w\s]+"," ",name.lower())).strip()

def folder_identity(url):
    p=urllib.parse.urlparse(url)
    m=FOLDER_RX.search(p.path)
    return (m.group(1)+"/"+m.group(2)) if m else ""

def parse_amount(value):
    m=PRICE_RX.search(value) or AMOUNT_RX.search(value)
    return float(m.group(1).replace(",",".")) if m else None

def permitted(url):
    if not safe_url(url): return False
    host=urllib.parse.urlparse(url).hostname
    if host not in ROBOTS:
        rp=urllib.robotparser.RobotFileParser()
        rp.set_url("https://"+host+"/robots.txt")
        try: rp.read()
        except Exception: return False
        ROBOTS[host]=rp
    return ROBOTS[host].can_fetch(HEADERS["User-Agent"],url)

def fetch(url, binary=False):
    if not permitted(url): return None
    for attempt in range(3):
        try:
            r=SESSION.get(url,timeout=int(os.getenv("SCAN_TIMEOUT","15")))
            if r.status_code in (403,404): return None
            if r.status_code==429 or r.status_code>=500:
                time.sleep(2*(attempt+1)); continue
            r.raise_for_status()
            time.sleep(float(os.getenv("REQUEST_DELAY","0.5")))
            return r.content if binary else r.text
        except requests.RequestException:
            time.sleep(attempt+1)
    return None

def links(soup,base):
    found=set()
    for tag in soup.select("a[href]"):
        url=urllib.parse.urljoin(base,tag.get("href","")).split("#")[0]
        if safe_url(url):found.add(url)
    return found

def discover(max_stores,max_folders):
    start=[BASE+"/", BASE+"/winkels", BASE+"/nieuw", BASE+"/aanbiedingen"]
    queue=deque(start); visited=set(); folders={}; stores=set()
    while queue and len(visited)<max_stores+50 and len(folders)<max_folders:
        url=queue.popleft()
        if url in visited:continue
        visited.add(url)
        page=fetch(url)
        if page is None:continue
        soup=BeautifulSoup(page,"html.parser")
        for target in links(soup,url):
            ident=folder_identity(target)
            if ident:
                folders.setdefault(ident,target)
            elif urllib.parse.urlparse(target).hostname in ("www.allefolders.nl","allefolders.nl"):
                path=urllib.parse.urlparse(target).path.rstrip("/")
                if path.startswith("/winkels/") and len(stores)<max_stores:
                    stores.add(target); queue.append(target)
                elif path in PAGE_TYPES or path=="/":
                    if target not in visited:queue.append(target)
        # Find folder URLs embedded in initial HTML/Next data (including escaped URLs).
        raw=html.unescape(page).replace("\\/","/")
        for match in re.finditer(r"/[a-z0-9-]+-aanbiedingen/[a-f0-9-]{16,}(?:/\d+)?",raw,re.I):
            found=urllib.parse.urljoin(BASE,match.group(0))
            ident=folder_identity(found)
            if ident:folders.setdefault(ident,found)
    return dict(list(folders.items())[:max_folders]),{"pages_checked":len(visited),"stores_checked":len(stores)}

def scan_folder(identity,url):
    page=fetch(url)
    if page is None:return None,[]
    soup=BeautifulSoup(page,"html.parser")
    images=[]; seen=set()
    for tag in soup.select("img[src], img[data-src], a[href]"):
        link=tag.get("src") or tag.get("data-src") or tag.get("href") or ""
        link=urllib.parse.urljoin(url,link)
        if urllib.parse.urlparse(link).hostname=="cdn.jafolders.com" and link not in seen:
            seen.add(link);images.append(link)
    # Filenames in embedded JSON may be escaped, but never collect arbitrary third-party images.
    raw=page.replace("\\/","/")
    for match in re.finditer(r"https://cdn\.jafolders\.com/[^\s\"'<>\\]+",raw):
        link=html.unescape(match.group(0))
        if link not in seen: seen.add(link);images.append(link)
    store=identity.split("/")[0].replace("-aanbiedingen","").replace("-"," ").title()
    raw_title=soup.title.get_text(" ",strip=True) if soup.title else ""
    title=(raw_title if raw_title and "Actuele folders en aanbiedingen deze week | AlleFolders" not in raw_title else f"{store} folder")
    today=datetime.now(timezone.utc).date().isoformat()
    rec={"id":identity,"store":store,"title":title,"url":url,"images":images[:200],
         "page_count":len(images[:200]),"last_seen":today}
    offers=[]; unique=set()
    # These are text snippets, not validated product extraction.
    for el in soup.select("[class*=offer], [class*=product], [itemtype*=Offer]"):
        text=el.get_text(" ",strip=True)
        if not (5<=len(text)<=200):continue
        price=parse_amount(text)
        if price is None:continue
        key=hashlib.sha1((identity+text).encode()).hexdigest()[:20]
        if key in unique:continue
        unique.add(key)
        offers.append({"id":key,"folder_id":identity,"store":store,"text":text,
            "price":price,"url":url,"source":"website_text","verified":False})
        if len(offers)>=200:break
    return rec,offers

def ocr_folder_pages(folders,max_pages):
    """Collect OCR evidence across all stores; diagnostics are returned separately."""
    stats={"candidate_images":sum(len(f.get("images",[])) for f in folders),
           "download_attempts":0,"download_success":0,"decode_success":0,
           "ocr_success":0,"ocr_nonempty":0,"price_fragments":0,
           "errors":[],"sample_text":[]}
    if max_pages<=0:return [],stats
    try:
        import io,pytesseract
        from PIL import Image,ImageOps,ImageEnhance
        pytesseract.get_tesseract_version()
    except Exception as exc:
        stats["errors"].append("OCR niet beschikbaar: "+str(exc))
        return [],stats
    offers=[]
    # Round-robin: distribute OCR across ALL discovered folders first.
    queue=deque((rec,i,url) for i in range(2) for rec in folders
                for url in rec.get("images",[])[i:i+1])
    while queue and stats["ocr_success"]<max_pages:
        rec,pageidx,url=queue.popleft()
        stats["download_attempts"]+=1
        data=fetch(url,binary=True)
        if not data:
            if len(stats["errors"])<12:stats["errors"].append("Afbeelding niet gedownload: "+url[:150])
            continue
        stats["download_success"]+=1
        try:
            img=Image.open(io.BytesIO(data))
            img.load()
            stats["decode_success"]+=1
            if max(img.size)<350:
                img=img.resize((img.width*3,img.height*3))
            img=ImageOps.autocontrast(ImageOps.grayscale(img))
            body=pytesseract.image_to_string(img,lang="nld+eng",config="--psm 11")
            stats["ocr_success"]+=1
        except Exception as exc:
            if len(stats["errors"])<12:stats["errors"].append("OCR fout: "+str(exc)[:140])
            continue
        if not body.strip():continue
        stats["ocr_nonempty"]+=1
        if len(stats["sample_text"])<5:
            stats["sample_text"].append({"store":rec["store"],"page":pageidx+1,
                                         "excerpt":body[:250]})
        # Prices on folders frequently omit the euro sign. These are tentative OCR
        # fragments, never asserted as a product/price pair.
        for n,line in enumerate(body.splitlines()):
            line=line.strip()
            if not 2<len(line)<190:continue
            value=parse_amount(line)
            if value is None:
                m=re.search(r"(?<!\\d)(\\d{1,3}[,.]\\d{2})(?!\\d)",line)
                if m:value=float(m.group(1).replace(",","."))
            if value is None or not 0.05<=value<=999.99:continue
            offers.append({"id":hashlib.sha1((rec["id"]+str(pageidx)+line+str(n)).encode()).hexdigest()[:20],
                "folder_id":rec["id"],"store":rec["store"],"text":line,
                "price":value,"url":rec["url"],"image_url":url,
                "page":pageidx+1,"source":"ocr_unverified","verified":False})
    stats["price_fragments"]=len(offers)
    print("OCR diagnostics:",json.dumps(stats,ensure_ascii=False),flush=True)
    return offers,stats

RECIPES=[
 ("Harissa-kipwraps",["kip","wrap","paprika","spinazie"],"Kip kruiden met harissa, bakken en met groenten in volkoren wraps serveren."),
 ("Groenterijke nasi met ei",["rijst","ei","prei","wortel"],"Rijst bereiden, groenten wokken en ei toevoegen."),
 ("Kip met geroosterde groenten",["kip","courgette","paprika"],"Kip en groenten kruiden en roosteren in de oven."),
 ("Shakshuka",["ei","tomaat","paprika"],"Tomaten en paprika stoven, eieren erin garen."),
 ("Tonijnbonensalade",["tonijn","bonen","tomaat"],"Tonijn met bonen, tomaat en kruiden mengen."),
 ("Zalm met broccoli",["zalm","broccoli"],"Zalm bakken en broccoli stomen."),
 ("Kip-kerrie met bloemkoolrijst",["kip","bloemkool","kerrie"],"Kip met kerrie en groenten bakken; bloemkoolrijst roerbakken."),
 ("Vegetarische chili",["bonen","paprika","tomaat"],"Bonen en groenten met chili en komijn laten sudderen."),
 ("Kip uit de airfryer",["kip","sla","aardappel"],"Kip kruiden en bereiden in de airfryer, met salade serveren."),
 ("Volkoren pastasalade",["pasta","tomaat","kip"],"Volkoren pasta koken en met kip en groenten mengen."),
 ("Frittata met groenten",["ei","spinazie","champignon"],"Groenten bakken, ei toevoegen en laten stollen."),
 ("Gevulde paprika met gehakt",["paprika","gehakt","tomaat"],"Paprika vullen met gebakken gehakt en groenten; in oven garen."),
 ("Wrap met gekruide tofu",["tofu","wrap","komkommer"],"Tofu krokant bakken, met rauwkost in wraps serveren."),
 ("Couscous met gegrilde groenten",["couscous","courgette","aubergine"],"Groenten grillen en met couscous mengen."),
 ("Kruidige linzensoep",["linzen","wortel","tomaat"],"Groenten en linzen met specerijen gaar koken.")
]

def recipe_suggestions(offers):
    text=" ".join(o.get("text","").lower() for o in offers)
    output=[]
    for name,ingredients,steps in RECIPES:
        matches=[x for x in ingredients if x in text]
        output.append({"name":name,"ingredients":ingredients,"method":steps,
            "matched_keywords":matches,"matched_count":len(matches),
            "cost_4_portions":None,"cost_note":"Geen betrouwbare totaalprijs zonder gevalideerde ingrediënten en hoeveelheden."})
    return sorted(output,key=lambda x:-x["matched_count"])

def render(data):
    DOCS.mkdir(parents=True,exist_ok=True)
    (DOCS/"data.json").write_text(json.dumps(data,ensure_ascii=False,indent=2))
    template=(ROOT/"src"/"template.html").read_text()
    (DOCS/"index.html").write_text(template.replace("__DATA__",json.dumps(data,ensure_ascii=False).replace("</","<\\/")))
    DATA.mkdir(exist_ok=True)
    (DATA/"latest.json").write_text(json.dumps(data,ensure_ascii=False,indent=2))
    with (DATA/"folders.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=["store","title","url","page_count","last_seen"])
        writer.writeheader()
        for rec in data["folders"]:writer.writerow({k:rec.get(k,"") for k in writer.fieldnames})

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--max-stores",type=int,default=int(os.getenv("MAX_STORES","80")))
    p.add_argument("--max-folders",type=int,default=int(os.getenv("MAX_FOLDERS","200")))
    p.add_argument("--ocr-pages",type=int,default=int(os.getenv("OCR_PAGES","20")))
    args=p.parse_args()
    DATA.mkdir(exist_ok=True)
    prior={}
    if (DATA/"latest.json").exists():
        try:prior=json.loads((DATA/"latest.json").read_text())
        except (ValueError,OSError):pass
    found,stats=discover(args.max_stores,args.max_folders)
    existing={x["id"]:x for x in prior.get("folders",[])}
    current=[]; offers=[]; errors=[]
    for idx,(ident,url) in enumerate(found.items(),1):
        folder,items=scan_folder(ident,url)
        if folder:
            current.append(folder);offers.extend(items)
        else:errors.append(url)
        if idx%25==0:print(f"Folders verwerkt: {idx}/{len(found)}",flush=True)
    # Preserve historical folders but identify which were seen during this run.
    for ident,rec in existing.items():
        if ident not in {r["id"] for r in current}:current.append(rec)
    # Retain past offers with deduplication, capped for GitHub's repository limits.
    offermap={o["id"]:o for o in prior.get("offers",[])}
    ocr_offers,ocr_stats=ocr_folder_pages(current[:len(found)],args.ocr_pages)
    for item in offers+ocr_offers:offermap[item["id"]]=item
    alloffers=list(offermap.values())[-30000:]
    now=datetime.now(timezone.utc).isoformat()
    report={"scanned_at":now,"folders":current,"offers":alloffers,
        "recipes":recipe_suggestions(alloffers),"stats":{**stats,"folder_links_found":len(found),
        "folders_accessible":len(current)-len(existing.keys()-found.keys()),
        "offer_entries":len(alloffers),"new_offer_entries":len(offers)+len(ocr_offers),
        "failed_folders":len(errors),"ocr":ocr_stats},
        "errors":errors[:50],"quality_notice":"Ongecontroleerde bron- en OCR-extractie; vergelijkbare consumentenprijzen niet gegarandeerd."}
    if not found:
        print("FOUT: Geen folderlinks ontdekt. Controleer robots.txt, sitewijzigingen en toegang.")
        if prior:
            prior["last_failed_scan"]=now
            render(prior)
        raise SystemExit(2)
    render(report)
    print(json.dumps(report["stats"],ensure_ascii=False))
    if not offers and not ocr_offers:
        raise SystemExit("Geen nieuwe prijsfragmenten gevonden; scan als fout gemarkeerd. Zie OCR diagnostics.")

if __name__=="__main__":main()
