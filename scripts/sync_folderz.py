#!/usr/bin/env python3
"""Bounded independent public Lidl listing adapter. Never infer dates/old prices.
Inspired by Samvox1/nl-supermarkt-mcp's independent Folderz source, not its parser.
"""
from html.parser import HTMLParser
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.request import Request,urlopen
from urllib.parse import urljoin,urlparse
from urllib.error import HTTPError
from pathlib import Path
import json,re,time
from sync_aanbiedingen import category
OUT=Path(__file__).resolve().parents[1]/'docs/data/supplemental-offers.json'
SEED='https://www.folderz.nl/winkels/lidl/aanbiedingen'
class Page(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.graph=[];self.script=False;self.buffer=''
    def handle_starttag(self,t,a):
        a=dict(a)
        if t=='script' and a.get('type')=='application/ld+json':self.script=True;self.buffer=''
        if t=='a':
            u=urljoin(SEED,a.get('href',''))
            if urlparse(u).hostname=='www.folderz.nl' and re.search(r'^/winkels/lidl/aanbiedingen/[^/]+-aanbieding-\d+/$',urlparse(u).path):self.links.append(u)
    def handle_data(self,s):
        if self.script:self.buffer+=s
    def handle_endtag(self,t):
        if t=='script' and self.script:
            self.script=False
            try:
                x=json.loads(self.buffer);self.graph.extend(x.get('@graph',[x]) if isinstance(x,dict) else x)
            except (ValueError,TypeError):pass

def parse(html,url,today):
    page=Page();page.feed(html)
    sellers={o.get('@id') for o in page.graph if isinstance(o,dict) and o.get('@type')=='Organization' and o.get('name')=='Lidl'}
    for product in page.graph:
        if not isinstance(product,dict) or product.get('@type')!='Product':continue
        candidates=product.get('offers',[]);candidates=[candidates] if isinstance(candidates,dict) else candidates
        accepted=[]
        for offer in candidates:
            if not isinstance(offer,dict) or not isinstance(offer.get('seller'),dict) or isinstance(offer.get('price'),bool):continue
            if offer.get('seller',{}).get('@id') not in sellers or offer.get('url')!=url or offer.get('priceCurrency')!='EUR':continue
            try:
                start=datetime.fromisoformat(offer['validFrom']).astimezone(ZoneInfo('Europe/Amsterdam')).date()
                end=datetime.fromisoformat(offer['validThrough']).astimezone(ZoneInfo('Europe/Amsterdam')).date()
                price=float(offer['price'])
            except (KeyError,TypeError,ValueError):continue
            if not start<=today<=end or (end-start).days>35 or not 0<price<1000:continue
            accepted.append((start,end,price))
        if len(set(accepted))!=1:continue
        start,end,price=accepted[0];name=product.get('name','').strip()
        if not name:continue
        identity=re.search(r'-aanbieding-(\d+)/$',url)
        if not identity:continue
        return dict(id='folderz-lidl-'+identity[1],name=name,category=category(name),price=price,regular_price=None,
          pack_label='inhoud niet bevestigd',start_date=start.isoformat(),end_date=end.isoformat(),promotion_status='active',verified=False,
          source_provider='Folderz',source={'url':url,'label':'Folderz externe aanbiedingsmelding'},checked_at=today.isoformat(),
          note='Externe melding; verpakking, Lidl Plus-voorwaarden en kassaprijs bij Lidl controleren.')
    return None

def fetch(url):
    with urlopen(Request(url,headers={'User-Agent':'BoodschappenMaatje/1.0 (+https://dasphhs.github.io/Boodschappen-maatje/docs/)'}),timeout=15) as r:return r.read(4000000).decode('utf8','replace')
def main():
    now=datetime.now(ZoneInfo('Europe/Amsterdam'));errors={};found={};checked=0
    try:
        page=Page();page.feed(fetch(SEED))
        links=list(dict.fromkeys(page.links))
        if not links:raise ValueError('No detail links; source layout may have changed')
        priority=lambda u:0 if re.search(r'broccoli|vega|tofu|groente|fruit|melk|dreft|toilet|wasmiddel',u) else 1
        for url in sorted(links,key=priority)[:12]:
            try:
                o=parse(fetch(url),url,now.date());checked+=1
                if o:found[o['id']]=o
            except Exception as e:
                errors[url]=str(e)[:120]
                if isinstance(e,HTTPError) and e.code in (403,429):break
            time.sleep(.5)
    except Exception as e:errors[SEED]=str(e)[:120]
    data=json.loads(OUT.read_text());shop=data['stores']['lidl']
    keep=[o for o in shop.get('offers',[]) if o.get('source_provider')!='Folderz' or (o.get('end_date','')>=now.date().isoformat() and o['id'] not in found)]
    shop['offers']=keep+list(found.values());shop['folderz_check']={'checked_at':now.isoformat(),'status':'partial' if errors else 'ok','details_checked':checked,'accepted':len(found),'errors':errors,'coverage':'bounded_first_listing_page'}
    data['generated_at']=now.isoformat();OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(shop['folderz_check'],ensure_ascii=False));return 2 if errors else 0
if __name__=='__main__':raise SystemExit(main())
