#!/usr/bin/env python3
"""Bounded reader of Lidl's public data-grid-data. No account or private API.
Read only explicitly dated in-store offers; keep membership/regional constraints.
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from pathlib import Path
import json, re, sys, time
from sync_aanbiedingen import category
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/data/supplemental-offers.json'
SEED='https://www.lidl.nl/c/aanbiedingen/a10008785'
class Grid(HTMLParser):
    def __init__(self): super().__init__();self.products=[];self.links=[];self.errors=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get('data-grid-data'):
            try:self.products.append(json.loads(a['data-grid-data']))
            except (ValueError,TypeError):self.errors+=1
        if tag=='a' and a.get('href'):self.links.append(urljoin(SEED,a['href']))
def day(ts):
    return datetime.fromtimestamp(float(ts),ZoneInfo('Europe/Amsterdam')).date()
def parse_product(p,today,url,discount_only=True):
    if not p.get('store') or p.get('online') or p.get('productType')!='RETAIL':return None
    if not p.get('productId') or not p.get('fullTitle'):return None
    try:start,end=day(p['storeStartDate']),day(p['storeEndDate'])
    except (KeyError,ValueError,TypeError,OverflowError,OSError):return None
    # Sentinel/evergreen intervals are not current promotions.
    if not start<=today<=end or (end-start).days>35:return None
    direct=urljoin(SEED,p.get('canonicalUrl',''))
    if urlparse(direct).hostname!='www.lidl.nl' or not re.search(r'/p[^/]*'+str(p['productId'])+r'$',direct):return None
    prices=p.get('regionsPrices',{})
    if not prices:return None
    # A single all-region value is safe; differing regions require a user's store.
    if len({json.dumps(x,sort_keys=True) for x in prices.values()})!=1:return None
    r=next(iter(prices.values()));base=(r.get('currentPrice') or {})
    plus=(r.get('currentLidlPlusPrice') or {}).get('price',{})
    chosen=base;membership=False
    if plus and discount_only:
        try:
            ps=datetime.fromisoformat(plus['startDate'].replace('Z','+00:00')).astimezone(ZoneInfo('Europe/Amsterdam')).date()
            pe=datetime.fromisoformat(plus['endDate'].replace('Z','+00:00')).astimezone(ZoneInfo('Europe/Amsterdam')).date()
            if ps<=today<=pe:chosen=plus;membership=True;start=max(start,ps);end=min(end,pe)
        except (ValueError,KeyError,TypeError):pass
    try:
        cs=datetime.fromisoformat(chosen['startDate'].replace('Z','+00:00')).astimezone(ZoneInfo('Europe/Amsterdam')).date()
        ce=datetime.fromisoformat(chosen['endDate'].replace('Z','+00:00')).astimezone(ZoneInfo('Europe/Amsterdam')).date()
        if not cs<=today<=ce:return None
    except (KeyError,TypeError,ValueError):return None
    price=chosen.get('price');discount=(chosen.get('discount') or {})
    if chosen.get('currencyCode')!='EUR' or not isinstance(price,(int,float)) or isinstance(price,bool) or not 0<price<1000:return None
    if chosen.get('variantsHaveDifferentPrices'):return None
    # Only discounts, not every priced item in a campaign carousel.
    regular=discount.get('deletedPrice')
    if membership and not isinstance(regular,(int,float)):regular=base.get('price')
    if discount_only and (not isinstance(regular,(int,float)) or not price<regular):return None
    pack=chosen.get('packaging',{}).get('text','')
    return dict(id='lidl-official-'+str(p['productId']),product_id=str(p['productId']),name=p['fullTitle'],category=category(p['fullTitle']),
        price=price,regular_price=regular,pack_label=pack,start_date=start.isoformat(),end_date=end.isoformat(),
        source_provider='lidl_official',source={'url':direct,'label':'Lidl openbare productgegevens'},
        source_page=url,checked_at=today.isoformat(),evidence_date=today.isoformat(),verified=True,promotion_status='active',
        member_required=membership,requires_membership=membership,promo_note='Alleen met Lidl Plus' if membership else 'In de winkel; zolang de voorraad strekt',
        without_membership_price=base.get('price') if membership else None,
        semantic_evidence={'verified_identity':True,'brand':(p.get('brand') or {}).get('name',''),'categories':[(p.get('keyfacts') or {}).get('wonCategoryPrimary','')]})
def fetch(url):
    req=Request(url,headers={'User-Agent':'BoodschappenMaatje/1.0 (public offer check; max 10 pages per run)'})
    with urlopen(req,timeout=20) as r:return r.read(8000000).decode('utf8','replace')
def main():
    now=datetime.now(ZoneInfo('Europe/Amsterdam'));today=now.date();pending=[SEED];seen=set();offers={};regulars={};errors={};counts={}
    while pending and len(seen)<10:
        url=pending.pop(0)
        if url in seen:continue
        seen.add(url)
        try:
            g=Grid();g.feed(fetch(url));counts[url]=len(g.products)
            if g.errors or not g.products:errors[url]='No usable grid products or malformed product data'
            for p in g.products:
                o=parse_product(p,today,url)
                if o:offers[o['id']]=o
                regular=parse_product(p,today,url,False)
                if regular:regulars[regular['id']]=regular
            if url==SEED:
                pending.extend(sorted({u for u in g.links if urlparse(u).hostname=='www.lidl.nl' and (re.search(r'/c/(?:aanbiedingen|weekenddeals)/[as]\d+$',u) or u=='https://www.lidl.nl/c/lidl-plus/s10008463') and u!=SEED}))
        except Exception as e:
            errors[url]=str(e)[:160]
            if isinstance(e,HTTPError) and e.code in (403,429):break
        if pending:time.sleep(.3)
    old=json.loads(OUT.read_text()) if OUT.exists() else {'schema_version':1,'stores':{}}
    st=old.setdefault('stores',{}).setdefault('lidl',{})
    others=[o for o in st.get('offers',[]) if o.get('source_provider')!='lidl_official']
    # Do not refresh timestamps on retained observations after network failure.
    retained=[o for o in st.get('offers',[]) if o.get('source_provider')=='lidl_official' and o.get('end_date','')>=today.isoformat() and o['id'] not in offers] if errors else []
    st['official_prices']=list(regulars.values()) if regulars else st.get('official_prices',[]);st['offers']=others+retained+list(offers.values());st['official_check']={'checked_at':now.isoformat(),'status':'partial' if errors else 'ok','pages':counts,'errors':errors,'current_offers':len(offers)}
    old['generated_at']=now.isoformat();OUT.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(st['official_check'],ensure_ascii=False));return 2 if errors else 0
if __name__=='__main__':sys.exit(main())
