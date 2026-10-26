"""Bounded official retailer Product JSON-LD scanner. No hidden/private APIs.

Fetch robots.txt first; one request per second; exact product URLs only.
Store factual prices and quantities, never full descriptions or recipe text.
"""
import json,re,time,sys
from html import unescape
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urljoin,urlparse
from urllib.robotparser import RobotFileParser
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
AGENT='BoodschappenMaatje/1.0 (+https://github.com/DASPHHS/Boodschappen-maatje)'
SEEDS=['https://www.action.com/nl-nl/c/huishouden/afwas---wasmiddelen/',
       'https://www.action.com/nl-nl/c/persoonlijke-verzorging/',
       'https://www.action.com/nl-nl/weekactie/']

def nodes(obj):
 if isinstance(obj,list):
  for x in obj:yield from nodes(x)
 elif isinstance(obj,dict):
  yield obj
  for v in obj.values():
   if isinstance(v,(dict,list)):yield from nodes(v)

def parse_product(html,url):
 soup=BeautifulSoup(html,'html.parser')
 for tag in soup.select('script[type="application/ld+json"]'):
  try:tree=json.loads(tag.string or tag.get_text())
  except (ValueError,TypeError):continue
  for p in nodes(tree):
   kinds=p.get('@type',[]);kinds=[kinds] if isinstance(kinds,str) else kinds
   if 'Product' not in kinds:continue
   offers=p.get('offers') or {};offers=offers if isinstance(offers,list) else [offers]
   for offer in offers:
    if not isinstance(offer,dict) or offer.get('priceCurrency')!='EUR':continue
    try:price=float(offer.get('price'))
    except (TypeError,ValueError):continue
    if not 0<price<10000:continue
    name=unescape(str(p.get('name') or '')).strip()
    if not name:continue
    if not re.search(r'vaatwas|wasmiddel|wasverzachter|waspoeder|wasgel|pods|wascapsule|geurbooster|toiletpapier|keukenrol|shampoo|conditioner|tandpasta|reiniger|schoonmaak|bleek|ontkalker|afwasmiddel|koffie',name,re.I):continue
    desc=str(p.get('description') or '')
    # Explicit declared number of washes/tablets, never infer rolls -> sheets.
    text=name+' '+desc
    unit=None;q=None
    m=re.search(r'(\d+(?:[.,]\d+)?)\s*(wasbeurten|wasbeurt|stuks|ml|cl|liter|kg|gram|g)\b',desc,re.I)
    size=m.group(0) if m else ''
    if m:
     q=float(m.group(1).replace(',','.'));u=m.group(2).lower()
     if u in ('wasbeurten','wasbeurt','stuks'):unit='st'
     elif u=='kg':q*=1000;unit='g'
     elif u in ('gram','g'):unit='g'
     else:q*=1000 if u=='liter' else 10 if u=='cl' else 1;unit='ml'
    # Keep explicit consumption units in display label for deterministic comparison.
    label=name+(' · '+size if size else '')
    if 'vaatwas' in name.lower() and size.endswith('stuks'):label=label.replace('stuks','tabletten')
    return {'name':label,'price':price,'quantity':q,'unit':unit,'url':url,
            'sku':str(p.get('sku') or ''),'ean':str(p.get('gtin13') or ''),
            'source':'Action officiële productpagina','promotion':False}
 return None

def collect(limit=24,session=None):
 http=session or requests.Session();http.headers.update({'User-Agent':AGENT})
 robot=RobotFileParser();r=http.get('https://www.action.com/robots.txt',timeout=20);r.raise_for_status();robot.parse(r.text.splitlines())
 def get(url):
  if urlparse(url).netloc!='www.action.com' or not robot.can_fetch(AGENT,url):raise ValueError('Robots of domein weigert '+url)
  time.sleep(1);r=http.get(url,timeout=20);r.raise_for_status();return r.text
 urls=[];errors=[]
 for seed in SEEDS:
  try:
   soup=BeautifulSoup(get(seed),'html.parser')
   for a in soup.select('a[href]'):
    u=urljoin(seed,a['href']).split('?')[0].split('#')[0]
    if re.match(r'https://www\.action\.com/nl-nl/p/\d+/',u) and u not in urls:urls.append(u)
  except Exception as e:errors.append(str(e)[:180])
 products=[]
 priority=lambda url:(0 if 'vaatwas' in url else 1 if any(x in url for x in ('wasmiddel','pods','wasverzachter','wascapsule')) else 2)
 urls.sort(key=priority)
 for url in urls[:limit]:
  try:
   product=parse_product(get(url),url)
   if product:products.append(product)
   else:errors.append('Geen bevestigde Product-prijs: '+url)
  except requests.HTTPError as e:
   errors.append(str(e)[:180])
   if e.response is not None and e.response.status_code in (401,403,429):break
  except Exception as e:errors.append(str(e)[:180])
 if not products:raise RuntimeError('Action leverde geen bevestigde productprijzen: '+str(errors))
 return {'updated_at':datetime.now(timezone.utc).isoformat(),'source':'Officiële Action Product JSON-LD',
         'stores':{'action':{'ordinary':[[p['name'],p['price'],p['quantity'],p['unit'],p['url']] for p in products],'promotions':[]}},
         'products':products,'errors':errors,'discovered_product_urls':len(urls)}

def main():
 status_path=ROOT/'docs/koopjes/retailer-status.json'
 try:
  report=collect()
 except Exception as exc:
  status_path.write_text(json.dumps({'last_attempt':datetime.now(timezone.utc).isoformat(),'status':'failed','error':str(exc)[:600]},ensure_ascii=False,indent=2))
  raise
 dest=ROOT/'docs/koopjes/retailer-prices.json';tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(report,ensure_ascii=False,indent=2));tmp.replace(dest)
 status_path.write_text(json.dumps({'last_attempt':report['updated_at'],'status':'ok','products':len(report['products']),'errors':report['errors']},ensure_ascii=False,indent=2))
 print(json.dumps({'products':len(report['products']),'discovered':report['discovered_product_urls'],'errors':report['errors']},ensure_ascii=False))
if __name__=='__main__':main()
