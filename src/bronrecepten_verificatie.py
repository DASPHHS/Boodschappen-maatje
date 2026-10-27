"""Small, respectful rotating recipe-page verification batch.

Keep previously verified complete records; discard data lacking source
ingredient quantities, servings or time. Never write source instructions.
"""
import json
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse
import requests
from wereldkeuken_bronnen import robots_allowed
from schema_recept_extractie import extract

ROOT=Path(__file__).resolve().parents[1]
INDEX=ROOT/"recepten"/"inspiratie.json"
OUT=ROOT/"recepten"/"geverifieerde_bronrecepten.json"
HEADERS={"User-Agent":"BoodschappenMaatje/4.0 (+https://github.com/DASPHHS/Boodschappen-maatje)"}

def run(session=None,max_pages=12):
    http=session or requests.Session()
    try:index=json.loads(INDEX.read_text(encoding="utf-8")).get("items",[])
    except (ValueError,OSError):index=[]
    try:previous=json.loads(OUT.read_text(encoding="utf-8")).get("items",[])
    except (ValueError,OSError):previous=[]
    found={p["url"]:p for p in previous if p.get("url")}
    urls=sorted({str(x.get("url")) for x in index if
                 isinstance(x,dict) and isinstance(x.get("url"),str) and
                 x["url"].startswith("https://") and x.get("kind")!="collection"})
    # Walk source catalog across 30-minute batches.
    stamp=datetime.now(timezone.utc)
    slot=(stamp.toordinal()*48+stamp.hour*2+stamp.minute//30)
    start=(slot*max_pages)%max(len(urls),1)
    batch=(urls[start:start+max_pages]+urls[:max(0,start+max_pages-len(urls))]) if urls else []
    states={"scanned":0,"structured_complete":0,"robots_or_access_blocked":0,
            "incomplete_schema":0}
    for url in batch:
        if not robots_allowed(url):
            states["robots_or_access_blocked"]+=1
            continue
        try:
            response=http.get(url,headers=HEADERS,timeout=15)
            response.raise_for_status()
            recipe,error=extract(response.text,url)
            states["scanned"]+=1
            if not recipe:
                states["incomplete_schema"]+=1
                continue
            found[url]=recipe
            states["structured_complete"]+=1
        except requests.RequestException:
            states["robots_or_access_blocked"]+=1
    output={"updated_at":stamp.isoformat(),"source_status":states,
            "description":"Only complete structured source recipes; title-only entries excluded.",
            "items":list(found.values())[:1500]}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    temp=OUT.with_suffix(".tmp")
    temp.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    temp.replace(OUT)
    return output
if __name__=="__main__":
    result=run()
    print(json.dumps(result["source_status"]))
