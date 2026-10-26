"""Independent coverage and freshness audit for published retail snapshots.

Pagination completeness is never interpreted as assortment/weekly-flyer coverage.
A previous snapshot is not a verified current price.
"""
from __future__ import annotations
from datetime import datetime, timezone, date
import json
from pathlib import Path

RETAILERS=("ah","jumbo","lidl","aldi","dirk","plus","hoogvliet","dekamarkt","vomar")
SHELF_FLOORS={"ah":5000,"jumbo":5000,"lidl":2000}
PROMOTION_FLOORS={"ah":100,"jumbo":100,"lidl":100}
EXTRA_CODES={"albert_heijn":"ah","jumbo":"jumbo","lidl":"lidl","aldi":"aldi",
             "dirk":"dirk","plus":"plus","hoogvliet":"hoogvliet",
             "dekamarkt":"dekamarkt","vomar":"vomar"}

def age_hours(ts,now=None):
    if not ts:return None
    try:
        dt=datetime.fromisoformat(str(ts).replace("Z","+00:00"))
        if dt.tzinfo is None:return None
        now=now or datetime.now(timezone.utc)
        return round(max(0,(now-dt.astimezone(timezone.utc)).total_seconds()/3600),1)
    except (ValueError,TypeError):return None

def analyse(primary,extra=None,official=None,now=None):
    now=now or datetime.now(timezone.utc)
    extra=extra or {}
    official=official or {}
    shelf=primary.get("shelf_products") or {}
    promos=primary.get("promotion_mentions") or {}
    extra_stores=extra.get("stores") or {}
    extra_coverage=extra.get("coverage") or {}
    official_stores=official.get("stores") or {}
    states=official.get("status") or {}
    primary_age=age_hours(primary.get("updated_at"),now)
    extra_age=age_hours(extra.get("updated_at"),now)
    official_age=age_hours(official.get("updated_at"),now)
    data={}
    for code in RETAILERS:
        coverage_name=next((k for k,v in EXTRA_CODES.items() if v==code),code)
        paged=extra_coverage.get(coverage_name) or {}
        extra_rows=extra_stores.get(code) or []
        official_rows=official_stores.get(code) or []
        amount=int(promos.get(code) or 0)
        problems=[]
        if code in SHELF_FLOORS and int(shelf.get(code) or 0)<SHELF_FLOORS[code]:
            problems.append("assortiment_onder_grens")
        if code in PROMOTION_FLOORS and amount<PROMOTION_FLOORS[code]:
            problems.append("weinig_acties_voor_weekdekking")
        if primary_age is None or primary_age>4:problems.append("hoofdaanvoer_verouderd")
        if extra_age is None or extra_age>4:problems.append("aanvullende_aanvoer_verouderd")
        if not paged.get("complete"):problems.append("api_paginering_niet_bevestigd")
        if not official_rows:problems.append("geen_officiele_productverificatie")
        data[code]={
            "shelf_records":int(shelf.get(code) or 0),
            "primary_promotion_records":amount,
            "extra_promotion_records":len(extra_rows),
            "official_product_records":len(official_rows),
            "primary_age_hours":primary_age,"extra_age_hours":extra_age,
            "official_age_hours":official_age,
            "api_pagination_complete":bool(paged.get("complete")),
            "retailer_coverage_complete":False,
            "official_status":states.get(code,{}).get("state","unknown"),
            "issues":problems,
            "quality":"needs_attention" if problems else "plausible_not_verified"
        }
    for code in ("action","xenos","zeeman"):
        rows=official_stores.get(code) or []
        data[code]={"official_product_records":len(rows),
                    "official_status":states.get(code,{}).get("state","unknown"),
                    "retailer_coverage_complete":False,
                    "quality":"partial" if rows and official_age is not None and official_age<=4 else "needs_attention",
                    "issues":[] if rows and official_age is not None and official_age<=4 else ["geen_recente_gecontroleerde_productfeed"]}
    return {"updated_at":now.isoformat(),"scope":"online_landelijk_met_lokale_winkelprioriteit",
            "primary_age_hours":primary_age,"extra_age_hours":extra_age,
            "official_age_hours":official_age,"retailers":data,
            "warning":"API-paginering compleet is geen bewijs van volledige weekfolder of assortiment."}

def main():
    root=Path(__file__).resolve().parents[1]
    def read(path):
        try:return json.loads(path.read_text(encoding="utf-8"))
        except (OSError,ValueError):return {}
    data=analyse(read(root/"recepten"/"status.json"),
                 read(root/"docs"/"recepten"/"extra-supermarkt-deals.json"),
                 read(root/"recepten"/"officiele-winkels.json"))
    target=root/"docs"/"recepten"/"bronkwaliteit.json"
    target.parent.mkdir(parents=True,exist_ok=True)
    temp=target.with_suffix(".tmp")
    temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    temp.replace(target)
    print(json.dumps({"quality":{k:v["quality"] for k,v in data["retailers"].items()}},ensure_ascii=False))
if __name__=="__main__":main()
