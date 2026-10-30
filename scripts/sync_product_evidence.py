#!/usr/bin/env python3
"""Bounded, identity-checked retailer metadata refresh; no name-only enrichment.
Never works around login, 403/429 or bot screens. Only public JSON-LD Product
and BreadcrumbList metadata is used, not guessed categories or prices.
"""
import datetime as dt
import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError
ROOT=Path(__file__).resolve().parents[1]/'docs'/'data'
MAX_REQUESTS=24
EXTRACTOR_VERSION=1
DOMAINS={'ah':'ah.nl','jumbo':'jumbo.com','lidl':'lidl.nl'}
def fingerprint(name,pack):
    return hashlib.sha256((name+'\n'+pack).encode()).hexdigest()[:24]
def nodes(value):
    if isinstance(value,list):
        for v in value:yield from nodes(v)
    elif isinstance(value,dict):
        yield value
        if '@graph' in value:yield from nodes(value['@graph'])
def extract(html,url,store,product_id):
    host=(urlparse(url).hostname or '').removeprefix('www.')
    if host!=DOMAINS[store]:raise ValueError('not an approved retailer host')
    docs=[]
    for s in re.findall(r'<script\b[^>]*type=[\"\']application/ld\+json[\"\'][^>]*>(.*?)</script>',html,re.S|re.I):
        try:docs.extend(nodes(json.loads(s)))
        except ValueError:continue
    breadcrumbs=[]
    for item in docs:
        if item.get('@type')=='BreadcrumbList':
            breadcrumbs.extend(x.get('name') or x.get('item',{}).get('name','') for x in item.get('itemListElement',[]) if isinstance(x,dict) and isinstance(x.get('item',{}),dict))
    for item in docs:
        types=item.get('@type',[]);types=[types] if isinstance(types,str) else types
        if 'Product' not in types:continue
        identifiers=[str(item.get(k,'')) for k in ['sku','productID','mpn']]
        urls=[str(item.get('url','')),str(item.get('@id',''))]
        # An exact retailer identifier must be corroborated by Product metadata.
        codes=[product_id,product_id.split('/')[0]] if store=='ah' else [product_id,product_id.rsplit('-',1)[-1]]
        if not any(code in identifiers or any(re.search(r'(?<![A-Za-z0-9])'+re.escape(code)+r'(?![A-Za-z0-9])',x) for x in urls) for code in codes):continue
        categories=item.get('category',[]);categories=[categories] if isinstance(categories,str) else categories
        name=str(item.get('name',''))
        categories=[str(c) for c in [*categories,*[b for b in breadcrumbs if b!=name]] if isinstance(c,str) and c]
        if not categories:raise ValueError('structured product category is missing')
        offers=item.get('offers',{});offers=offers[0] if isinstance(offers,list) and offers else offers
        price=(offers or {}).get('price') if isinstance(offers,dict) else None
        if price is None and isinstance(offers,dict) and offers.get('@type')=='AggregateOffer':
            low,high=offers.get('lowPrice'),offers.get('highPrice')
            if low is not None and str(low)==str(high):price=low
        currency=(offers or {}).get('priceCurrency') if isinstance(offers,dict) else None
        price=float(price) if isinstance(price,(int,float,str)) and re.fullmatch(r'\d+(?:\.\d+)?',str(price)) and currency=='EUR' else None
        brand=item.get('brand',{})
        brand=brand.get('name','') if isinstance(brand,dict) else brand if isinstance(brand,str) else ''
        return {'product_pack':item.get('size') if isinstance(item.get('size'),str) else None,'brand':brand,'observed_price':price if price and 0<price<1000 else None,'price_currency':currency,'verified_identity':True,'product_id':product_id,'name':name,
                'categories':list(dict.fromkeys(categories)),'source_url':url,
                'ean':item.get('gtin13') or item.get('gtin') or None}
    raise ValueError('no matching JSON-LD Product identity')
def main():
    queuefile=ROOT/'semantic-review.json'
    if not queuefile.exists():return
    queue=json.loads(queuefile.read_text()).get('queue',[])
    target=ROOT/'product-evidence.json'
    prior=json.loads(target.read_text()) if target.exists() else {'schema_version':1,'products':{}}
    now=dt.datetime.now(dt.timezone.utc);today=now.date().isoformat()
    queue.sort(key=lambda x:(x.get('priority',1),prior['products'].get(x['store']+':'+x['product_id'],{}).get('last_attempt','')))
    per_store={s:[x for x in queue if x['store']==s] for s in DOMAINS}
    queue=[per_store[s][i] for i in range(max([len(v) for v in per_store.values()] or [0])) for s in DOMAINS if i<len(per_store[s])]
    blocked=set();attempts=0
    for candidate in queue:
        store=candidate['store'];key=store+':'+candidate['product_id'];url=candidate.get('url')
        if attempts>=MAX_REQUESTS:break
        if not url or store in blocked:continue
        if (urlparse(url).hostname or '').removeprefix('www.')!=DOMAINS[store]:continue
        previous=prior['products'].get(key,{})
        if previous.get('evidence_version')==EXTRACTOR_VERSION and previous.get('last_attempt','')[:10]>=str((now-dt.timedelta(days=3)).date()) and previous.get('status')!='ok' and previous.get('fingerprint')==candidate['fingerprint']:continue
        if previous.get('evidence_version')==EXTRACTOR_VERSION and previous.get('checked_at','')[:10]==today and previous.get('fingerprint')==candidate['fingerprint']:continue
        attempts+=1
        result={'evidence_version':EXTRACTOR_VERSION,'fingerprint':candidate['fingerprint'],'last_attempt':now.isoformat()}
        try:
            req=Request(url,headers={'User-Agent':'Boodschappenmaatje/1.0 public-product-metadata'})
            with urlopen(req,timeout=18) as res:
                final=res.geturl();html=res.read(2500000).decode('utf8',errors='replace')
            info=extract(html,final,store,candidate['product_id'])
            result.update(info,checked_at=now.isoformat(),status='ok')
        except HTTPError as exc:
            result.update(status='unavailable',reason='HTTP '+str(exc.code))
            if exc.code in (403,429):blocked.add(store)
        except Exception as exc:result.update(status='needs_evidence',reason=str(exc)[:200])
        prior['products'][key]=result
        time.sleep(.7)
    prior['generated_at']=now.isoformat();prior['attempted']=attempts
    target.write_text(json.dumps(prior,ensure_ascii=False,separators=(',',':'))+'\n')
    print('Metadata refresh:',attempts,'requests; blocked retailers:',','.join(sorted(blocked)) or 'none')
if __name__=='__main__':main()
