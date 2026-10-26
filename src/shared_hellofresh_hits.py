"""Turn user-shared HelloFresh indexes into visible hits, without invented prices."""
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from actie_receptmatches import matched_keys,normalized
from receptenradar_catalog import ING
ROOT=Path(__file__).resolve().parents[1]
ARCHIVES=('eigen-archief.json','hello-fresh-maart-archief.json','hello-fresh-kaarten.json')
def build(offers_by_store,archives=None,today=None):
 from receptenradar_v2 import match_ingredient,verified_discount
 today=today or datetime.now(ZoneInfo('Europe/Amsterdam')).date().isoformat()
 if archives is None:
  archives=[json.loads((ROOT/'recepten'/name).read_text()) for name in ARCHIVES if (ROOT/'recepten'/name).exists()]
 recipes=[];seen=set()
 for archive in archives:
  for item in archive.get('items',[]):
   if 'hellofresh' not in normalized(item.get('source','')).replace(' ',''):continue
   title=item.get('title','');key=normalized(title)
   if not key or key in seen:continue
   seen.add(key)
   ingredients=[x if isinstance(x,str) else x.get('name','') for x in item.get('ingredients',[])]
   text=' '.join([title,*ingredients,*item.get('keywords',[])])
   groups=matched_keys(text,set(ING))
   keys={key for values in groups.values() for key in values}
   recipes.append({'title':title,'source':item['source'],'category':item.get('category','Onbekend'),
    'cuisine':item.get('cuisine') or 'Internationaal','minutes':item.get('minutes'),
    'url':item.get('url'),'local_page':item.get('local_page'),'ingredient_names':ingredients,
    'search_text':text,'ingredient_keys':sorted(keys),'source_note':item.get('source_note',''),
    'complete':False,'checkout':None,'price_status':'Maaltijdprijs nog niet volledig gecontroleerd',
    'match_evidence':'gedeelde ingrediënten' if ingredients else 'alleen recepttitel'})
 stores={}
 for store,offers in offers_by_store.items():
  mapped=[]
  for recipe in recipes:
   matches=[]
   for offer in offers:
    if not (offer.get('valid_from','9999')<=today<=offer.get('valid_until','')):continue
    if not verified_discount(offer):continue
    keys=[key for key in recipe['ingredient_keys'] if match_ingredient(offer,key)]
    if keys:matches.append({'name':offer['name'],'keys':keys,'valid_until':offer['valid_until'],'url':offer.get('url')})
   mapped.append({**recipe,'possible_offers':matches,'has_possible_offer':bool(matches)})
  stores[store]=mapped
 return {'updated_at':datetime.now(ZoneInfo('Europe/Amsterdam')).isoformat(),'shared_recipe_count':len(recipes),'stores':stores}
def main():
 prices=json.loads((ROOT/'recepten/data.json').read_text());result=build(prices.get('deals',{}))
 for directory in ['recepten','docs/recepten']:
  (ROOT/directory/'shared-hellofresh-hits.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')))
 print('Gedeelde HelloFresh-recepten als hits:',result['shared_recipe_count'])
if __name__=='__main__':main()
