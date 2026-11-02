#!/usr/bin/env python3
"""Refresh bounded factual ingredient-family evidence; never retain recipe text."""
import argparse
import datetime as dt
import json
import time
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from recipe_metadata import PROFILE_VERSION
from refresh_publisher_recipes import TARGET, fetch, schema_recipes, to_record
import refresh_hellofresh_recipes as hf


def refresh(limit=80, pause=0.5, missing_only=False):
    data=json.loads(TARGET.read_text('utf-8'))
    stamp=dt.date.today().isoformat()
    checked=updated=0
    rules=None
    try:rules=hf.allowed_robots(hf.fetch)
    except (OSError,ValueError,urllib.error.URLError):pass
    def inspect(old):
        try:
            url=old['url']
            page=(hf.fetch if old['source']=='HelloFresh' else fetch)(url)
            new=hf.record_from_page(url,page,stamp) if old['source']=='HelloFresh' else next((r for meta in schema_recipes(page) if (r:=to_record(url,meta,stamp))),None)
            return new,False
        except urllib.error.HTTPError as exc:return None,exc.code in (401,403,429)
        except (OSError,ValueError,urllib.error.URLError):return None,False
    # Two independent public-page requests at a time; no new batch after a refusal.
    # Persist each completed batch so a slow source cannot discard verified work.
    with ThreadPoolExecutor(max_workers=2) as pool:
        for source in ('HelloFresh','Allerhande'):
            records=sorted([r for r in data['recipes'] if r.get('source')==source],
                key=lambda r:(r.get('ingredient_profile_version')==PROFILE_VERSION,r.get('ingredient_checked_at',r.get('last_checked',''))))
            if missing_only:records=[r for r in records if r.get('ingredient_profile_version')!=PROFILE_VERSION]
            if source=='HelloFresh':records=[r for r in records if rules and rules.can_fetch(hf.USER_AGENT,r['url'])]
            records=records[:limit]
            for offset in range(0,len(records),2):
                batch=records[offset:offset+2]
                refused=False
                for old,(new,stop) in zip(batch,pool.map(inspect,batch)):
                    checked+=1
                    old['ingredient_checked_at']=dt.datetime.now(dt.timezone.utc).isoformat()
                    refused|=stop
                    if new and new.get('ingredient_evidence')=='publisher_recipe_schema':
                        old.update({**new,'id':old['id']});updated+=1
                data['generated_at']=stamp
                TARGET.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf-8')
                print(source,'checked',checked,'verified',updated,flush=True)
                if refused:break
                time.sleep(pause)
    print(f'Ingredient evidence: {checked} checked, {updated} updated')
    return updated

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--limit',type=int,default=80)
    parser.add_argument('--missing-only',action='store_true')
    args=parser.parse_args()
    refresh(args.limit,missing_only=args.missing_only)
