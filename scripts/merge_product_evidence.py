"""Merge independently refreshed evidence by timestamp, then enrich exact rows.
No network, no new source dates, and no fuzzy identity or guessed pack sizes.
"""
import datetime as dt
import json
import sys
from pathlib import Path
from sync_product_evidence import fingerprint
ROOT=Path(__file__).resolve().parents[1]/'docs'/'data'

def merge(current,incoming):
    products=dict(current.get('products',{}))
    for key,value in incoming.get('products',{}).items():
        previous=products.get(key,{})
        if value.get('last_attempt','')>=previous.get('last_attempt',''):products[key]=value
    return {**current,'products':products,'generated_at':dt.datetime.now(dt.timezone.utc).isoformat()}

def enrich(catalog,evidence,today):
    count=0
    for store,rows in catalog.get('stores',{}).items():
        for row in rows:
            if len(row)>5 and row[5].get('fingerprint')!=fingerprint(row[0],row[2]):del row[5:]
            e=evidence.get('products',{}).get(store+':'+str(row[4]),{})
            try:age=(today-dt.date.fromisoformat(str(e.get('checked_at',''))[:10])).days
            except ValueError:continue
            if e.get('status')!='ok' or not 0<=age<=14 or not e.get('verified_identity') or e.get('fingerprint')!=fingerprint(row[0],row[2]):continue
            if len(row)>5:row[5]=e
            else:row.append(e)
            count+=1
    return count

def main():
    path=ROOT/'product-evidence.json';e=json.loads(path.read_text())
    if len(sys.argv)>1:e=merge(e,json.loads(Path(sys.argv[1]).read_text()))
    catalogpath=ROOT/'retailer-catalog.json';c=json.loads(catalogpath.read_text())
    n=enrich(c,e,dt.datetime.now(dt.timezone.utc).date())
    path.write_text(json.dumps(e,ensure_ascii=False,separators=(',',':'))+'\n')
    catalogpath.write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n')
    print('Exact catalog rows enriched:',n)
if __name__=='__main__':main()
