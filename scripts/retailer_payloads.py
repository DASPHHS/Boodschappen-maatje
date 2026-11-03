"""Read public product HTML as data, never execute embedded JavaScript.

Inspired by KortingKlok's retailer-specific adapters (MIT), implemented against
the current public Jumbo Nuxt payload and AH breadcrumb HTML. Exact SKU only.
"""
import datetime as dt
import json
import re
from html.parser import HTMLParser
from urllib.parse import urlparse, urljoin


class Breadcrumbs(HTMLParser):
    def __init__(self):
        super().__init__(); self.depth=0; self.anchor=False; self.label=[]; self.categories=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='nav' and a.get('data-testid')=='breadcrumb-nav':self.depth=1
        elif self.depth and tag=='nav':self.depth+=1
        if self.depth and tag=='a':
            self.anchor=str(a.get('href','')).startswith('/producten/') and '/merk/' not in a.get('href','')
            self.label=[]
    def handle_endtag(self,tag):
        if self.depth and tag=='a':
            label=' '.join(self.label).strip()
            if self.anchor and label:self.categories.append(label)
            self.anchor=False
        if self.depth and tag=='nav':self.depth-=1
    def handle_data(self,data):
        if self.depth and self.anchor:self.label.append(data)


def breadcrumb_categories(html):
    p=Breadcrumbs();p.feed(html);return list(dict.fromkeys(p.categories))


def nuxt_products(html):
    """Resolve only Product objects from Nuxt's flattened reference table."""
    for raw in re.findall(r'<script\b[^>]*id=["\']__NUXT_DATA__["\'][^>]*>(.*?)</script>',html,re.S|re.I):
        try:table=json.loads(raw)
        except ValueError:continue
        if not isinstance(table,list) or len(table)>100000:continue
        def resolve(index,seen=frozenset()):
            if type(index)!=int or not 0<=index<len(table) or index in seen or len(seen)>35:return None
            value=table[index];seen=seen|{index}
            if isinstance(value,dict):return {k:resolve(v,seen) for k,v in value.items()}
            if isinstance(value,list):return [resolve(v,seen) if type(v)==int else v for v in value]
            return value
        for i,value in enumerate(table):
            if isinstance(value,dict) and 'sku' in value and 'title' in value and 'price' in value:
                yield resolve(i)


def cents(value):
    return round(value/100,2) if type(value) in (int,float) and 0<value<100000 else None


def jumbo_product(html,url,product_id):
    if (urlparse(url).hostname or '').removeprefix('www.')!='jumbo.com':return None
    sku=product_id.rsplit('-',1)[-1]
    for p in nuxt_products(html):
        if p.get('sku')!=sku:continue
        canonical=p.get('canonicalUrl') or p.get('link')
        if not canonical or urljoin(url,canonical).rstrip('/')!=url.rstrip('/'):continue
        price=p.get('price') or {};base=cents(price.get('price'));promo=cents(price.get('promoPrice'))
        current=promo if promo is not None and base is not None and promo<base else base
        source_pack=p.get('subtitle')
        if not source_pack:
            measures=re.findall(r'(?<![\d.])(?:\d+\s*x\s*)?\d+(?:[.,]\d+)?\s*(?:kg|g|ml|cl|l)\b',p.get('title') or '',re.I)
            if len(measures)==1:source_pack=measures[0]
        categories=[x['name'] for x in p.get('categories') or [] if isinstance(x,dict) and isinstance(x.get('name'),str)]
        availability=p.get('availability') or {}
        return {'name':p.get('title'),'product_id':product_id,'verified_identity':True,
            'categories':categories,'brand':p.get('brand'),'ean':p.get('ean'),
            'product_pack':source_pack,'observed_price':current,'regular_price':base,
            'price_currency':'EUR','source_url':url,'extractor':'jumbo_nuxt_product',
            'availability_status':'unavailable' if availability.get('isAvailable') is False else 'available' if availability.get('isAvailable') is True else 'unknown',
            # Presence of a promotion tag does not prove a product discount.
            'has_product_discount':bool(promo is not None and base is not None and promo<base),
            'promotions':p.get('promotions') or []}
    return None


def promotion_window(promotion,today):
    months={'jan':1,'feb':2,'mrt':3,'apr':4,'mei':5,'jun':6,'jul':7,'aug':8,'sep':9,'okt':10,'nov':11,'dec':12}
    start,end=promotion.get('start') or {},promotion.get('end') or {}
    matches=[]
    for year in (today.year-1,today.year,today.year+1):
        try:
            a=dt.date(year,months[start['monthShort']],int(start['date']))
            b=dt.date(year+(months[end['monthShort']]<a.month),months[end['monthShort']],int(end['date']))
            weekdays=('ma','di','wo','do','vr','za','zo')
            if start.get('dayShort') and start['dayShort']!=weekdays[a.weekday()]:continue
            if end.get('dayShort') and end['dayShort']!=weekdays[b.weekday()]:continue
            if a<=today<=b and (b-a).days<=366:matches.append((a.isoformat(),b.isoformat()))
        except (KeyError,TypeError,ValueError):continue
    return matches[0] if len(matches)==1 else None
