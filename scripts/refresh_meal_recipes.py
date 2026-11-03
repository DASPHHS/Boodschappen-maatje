#!/usr/bin/env python3
"""Small verified publisher seed set for breakfast and lunch; no copied instructions."""
import datetime as dt
import json
import time
from refresh_publisher_recipes import TARGET,fetch,schema_recipes,to_record
SEEDS=(
'https://www.ah.nl/allerhande/recept/R-R1197684/havermout-bananenpancakes-met-pindakaas-en-amandel',
'https://www.ah.nl/allerhande/recept/R-R1197075/kwark-met-banaan-blauwe-bessen-en-pangranola',
'https://www.ah.nl/allerhande/recept/R-R1195926/kwark-met-gebakken-banaan-met-noten-en-zaden',
'https://www.ah.nl/allerhande/recept/R-R1199642/yoghurt-met-banaan-kaneel-en-geroosterde-havermout',
'https://www.ah.nl/allerhande/recept/R-R1198663/spinazieomelet-met-brood',
'https://www.ah.nl/allerhande/recept/R-R1198661/spinazieomelet-met-witte-kaas-en-brood',
'https://www.ah.nl/allerhande/recept/R-R1197938/volkorensandwich-met-groente-omelet',
'https://www.ah.nl/allerhande/recept/R-R1187570/boterham-met-groenteomelet')
def main():
 data=json.loads(TARGET.read_text());records={r['url']:r for r in data['recipes']}
 for index,url in enumerate(SEEDS):
  try:
   meta=schema_recipes(fetch(url))
   record=next((r for m in meta if (r:=to_record(url,m,dt.date.today().isoformat(),meal_hint='ontbijt' if index<4 else 'lunch'))),None)
   if record:
    records[url]=record;print(record['title'],record['meal_type'],flush=True)
  except OSError as exc:
   if getattr(exc,'code',None) in (401,403,429):break
  time.sleep(.3)
 data['recipes']=list(records.values());data['generated_at']=dt.date.today().isoformat()
 TARGET.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
