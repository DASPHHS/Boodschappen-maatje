#!/usr/bin/env python3
"""Refresh bounded factual ingredient-family evidence; never retain recipe text."""
import argparse
import datetime as dt
import json
import time
import urllib.error
from refresh_publisher_recipes import TARGET, fetch, schema_recipes, to_record
import refresh_hellofresh_recipes as hf


def refresh(limit=24, pause=0.3):
    data=json.loads(TARGET.read_text('utf-8'))
    stamp=dt.date.today().isoformat()
    checked=updated=0
    rules=None
    try: rules=hf.allowed_robots(hf.fetch)
    except (OSError,ValueError,urllib.error.URLError):pass
    for source in ('HelloFresh','Allerhande'):
        records=sorted([r for r in data['recipes'] if r.get('source')==source],
                       key=lambda r:(r.get('ingredient_checked_at',r.get('last_checked','')),r.get('ingredient_evidence')=='publisher_recipe_schema'))
        for old in records[:limit]:
            url=old['url']
            if source=='HelloFresh' and (rules is None or not rules.can_fetch(hf.USER_AGENT,url)):continue
            checked+=1
            old['ingredient_checked_at']=stamp
            try:
                page=(hf.fetch if source=='HelloFresh' else fetch)(url)
                if source=='HelloFresh':new=hf.record_from_page(url,page,stamp)
                else:new=next((r for meta in schema_recipes(page) if (r:=to_record(url,meta,stamp))),None)
                if new and new.get('ingredient_evidence')=='publisher_recipe_schema':
                    # Keep stable record identity and replace verified factual fields.
                    old.update({**new,'id':old['id']})
                    updated+=1
                    data['generated_at']=stamp
                    TARGET.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf-8')
                    print(source,checked,updated,flush=True)
            except urllib.error.HTTPError as exc:
                if exc.code in (401,403,429):break
            except (OSError,ValueError,urllib.error.URLError):pass
            time.sleep(pause)
    if checked:
        data['generated_at']=stamp
        TARGET.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(f'Ingredient evidence: {checked} checked, {updated} updated')
    return updated

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--limit',type=int,default=24)
    refresh(parser.parse_args().limit)
