"""Reconcile imported Jumbo promotions with exact public product payloads.
Persistent evidence survives imports; changed product/price/terms invalidate it.
No browser impersonation, login, proxy rotation or access-control workarounds.
"""
import datetime as dt
from decimal import Decimal,ROUND_HALF_UP
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from zoneinfo import ZoneInfo
from retailer_payloads import jumbo_product,promotion_window
VERIFIER_VERSION=3
ROOT=Path(__file__).resolve().parents[1]/'docs'/'data'
FIELDS=('name','price','pack_label','start_date','end_date','member_required','requires_membership','multi_buy_quantity','multi_buy_price','loyalty_price','loyalty_program','max_promotion_quantity')

def fingerprint(o):
    return hashlib.sha256(json.dumps({**{k:o.get(k) for k in FIELDS if k!='max_promotion_quantity' or o.get(k) is not None},'url':o.get('source',{}).get('url'),'ean':o.get('ean')},sort_keys=True).encode()).hexdigest()

def pack_key(text):
    s=str(text or '').lower().replace(',','.').replace('×','x')
    if re.search(r'\b(ca|circa|ongeveer)\b',s):return None
    s=re.sub(r'\bliter\b','l',s);s=re.sub(r'\b(?:gram|gr)\b','g',s)
    if s.strip()=='per stuk':return (1,'piece')
    piece=re.fullmatch(r'\s*(\d+)\s*(?:stuks?|st|capsules|tabletten)\s*',s)
    if piece:return (int(piece[1]),'piece')
    m=re.fullmatch(r'\s*(?:(\d+)\s*x\s*)?(\d+(?:\.\d+)?)\s*(kg|g|l|ml|cl)\s*',s)
    if not m:return None
    count,amount,unit=m.groups();return (round(int(count or 1)*float(amount)*({'kg':1000,'g':1,'l':1000,'ml':1,'cl':10}[unit]),4),'g' if unit in ('g','kg') else 'ml')

def bundle_terms(promo,base):
    text=' '.join(str(t.get('text','')) for t in promo.get('tags') or [] if isinstance(t,dict))
    if promo.get('isKiesAndMix') or re.search(r'extra|klanten|kaart|online|bezorg',text,re.I):return None
    m=re.fullmatch(r'\s*(\d+)\s+voor\s+€?\s*(\d+[,.]\d{2})\s*',text,re.I)
    if m:return int(m[1]),round(float(m[2].replace(',','.')),2)
    if re.fullmatch(r'2e\s+halve\s+prijs',text,re.I):return 2,float((Decimal(str(base))*Decimal('1.5')).quantize(Decimal('.01'),rounding=ROUND_HALF_UP))
    if re.fullmatch(r'2e\s+gratis',text,re.I):return 2,base
    m=re.fullmatch(r'\s*(\d+)\s*\+\s*(\d+)\s*gratis\s*',text,re.I)
    if m:return int(m[1])+int(m[2]),round(int(m[1])*base,2)
    return None

def assess(o,html,today):
    url=o['source']['url'];pid=url.rstrip('/').rsplit('/',1)[-1]
    p=jumbo_product(html,url,pid)
    if not p:return {'verdict':'unresolved','reason':'Exact product not present in public payload'}
    if p.get('availability_status')=='unavailable':return {'verdict':'disputed','reason':'Retailer product unavailable'}
    if p.get('availability_status')!='available':return {'verdict':'unresolved','reason':'Retailer availability not explicit'}
    if not p.get('observed_price'):return {'verdict':'unresolved','reason':'Retailer product price missing'}
    # A shelf price and an effective bundle price must not be mistaken for a
    # conflict. Confirm the mandatory quantity and total directly from the tags.
    for promo in p['promotions']:
        if promo.get('group')=='GeenBestelkosten':continue
        terms=bundle_terms(promo,p['regular_price'])
        if not terms or promotion_window(promo,today)!=(o.get('start_date'),o.get('end_date')):continue
        quantity,total=terms
        if quantity<2 or not pack_key(p.get('product_pack')) or pack_key(p['product_pack'])!=pack_key(o.get('pack_label')):continue
        if o.get('member_required') or o.get('requires_membership') or o.get('loyalty_price'):continue
        if o.get('multi_buy_quantity')!=quantity or not isinstance(o.get('multi_buy_price'),(int,float)) or abs(o['multi_buy_price']-total)>.011:continue
        effective=round(total/quantity,2)
        if abs(o['price']-effective)>.011:continue
        proof={k:o.get(k) for k in FIELDS}
        proof.update(status='available',checked_at=today.isoformat(),url=url,max_promotion_quantity=promo.get('maxPromotionQuantity'),price=effective,pricing_basis='effective_per_item_with_mandatory_bundle')
        return {'verdict':'confirmed','promotion_evidence':proof,'regular_price':p['regular_price'],'source_title':p['name']}
    conditional=any(x.get('volumeDiscounts') or x.get('isKiesAndMix') or re.search(r"\d\s+voor|stuks|gratis|halve|extra|kaart|bij elke|\d\s*\+\s*\d",' '.join(str(t.get('text','')) for t in x.get('tags') or [] if isinstance(t,dict)),re.I) for x in p['promotions'] if x.get('group')!='GeenBestelkosten')
    if conditional:return {'verdict':'unresolved','reason':'Conditional retailer promotion: effective per-item price is not a single-pack price'}
    if abs(p['observed_price']-o['price'])>.011:return {'verdict':'disputed','reason':'Retailer price differs','observed_price':p['observed_price']}
    fixed_promotions=[x for x in p['promotions'] if x.get('group')!='GeenBestelkosten' and any(re.fullmatch(r'voor\s+€?\s*\d+[,.]\d{2}',str(t.get('text','')),re.I) for t in x.get('tags') or [] if isinstance(t,dict))]
    if not p.get('has_product_discount') and not fixed_promotions:
        if any(x.get('group')!='GeenBestelkosten' for x in p['promotions']):return {'verdict':'unresolved','reason':'Promotion exists but product discount is not explicit in price payload'}
        return {'verdict':'disputed','reason':'No product discount in retailer price; delivery rewards are not product discounts','observed_price':p['observed_price']}
    if not pack_key(p.get('product_pack')) or pack_key(p['product_pack'])!=pack_key(o.get('pack_label')):
        return {'verdict':'unresolved','reason':'Exact packaging not corroborated'}
    # Membership and multibuys need additional source-specific parsing. Never
    # promote their price to a universal single-pack discount.
    if any(o.get(k) for k in ('member_required','requires_membership','multi_buy_quantity','multi_buy_price','loyalty_price')):
        return {'verdict':'unresolved','reason':'Membership or bundle terms require exact source evidence'}
    for promo in p['promotions']:
        tags=' '.join(str(x.get('text','')) for x in promo.get('tags') or [] if isinstance(x,dict))
        if promo.get('group')=='GeenBestelkosten' or promo.get('isKiesAndMix') or promo.get('volumeDiscounts') or re.search(r"extra|klanten|kaart|online|bezorg|bij elke|stuks",tags,re.I):continue
        fixed=re.fullmatch(r'voor\s+€?\s*(\d+[,.]\d{2})',tags,re.I)
        if fixed and abs(float(fixed[1].replace(',','.'))-o['price'])>.011:continue
        window=promotion_window(promo,today)
        if not window or window!=(o.get('start_date'),o.get('end_date')):continue
        proof={k:o.get(k) for k in FIELDS}
        proof.update(status='available',checked_at=today.isoformat(),url=url,max_promotion_quantity=promo.get('maxPromotionQuantity'))
        return {'verdict':'confirmed','promotion_evidence':proof,'regular_price':p['regular_price'],'source_title':p['name']}
    return {'verdict':'unresolved','reason':'Retailer product discount found; exact validity or conditions not corroborated'}

def reusable(record,o,today):
    try:age=(today-dt.date.fromisoformat(record.get('checked_at',''))).days
    except ValueError:return False
    return record.get('verifier_version')==VERIFIER_VERSION and 0<=age<=2 and fingerprint(o) in (record.get('fingerprint'),record.get('resolved_fingerprint'))

def apply(o,record):
    if record.get('verdict')=='confirmed':
        o.update(verified=True,max_promotion_quantity=record['promotion_evidence'].get('max_promotion_quantity'),price=record['promotion_evidence']['price'],promotion_evidence=record['promotion_evidence'],regular_price=record['regular_price'],date_estimated=False)
    elif record.get('verdict')=='disputed':
        o.update(verified=False,promotion_status='disputed',verification_reason=record['reason'])

def merge_journals(current,incoming):
    products=dict(current.get('products',{}))
    for key,record in incoming.get('products',{}).items():
        previous=products.get(key,{})
        if record.get('observed_at',record.get('checked_at',''))>=previous.get('observed_at',previous.get('checked_at','')):products[key]=record
    return {**current,'products':products}

def main():
    day=dt.datetime.now(ZoneInfo('Europe/Amsterdam')).date()
    catalogpath=ROOT/'offers-catalog.json';c=json.loads(catalogpath.read_text())
    journalpath=ROOT/'retailer-offer-evidence.json'
    journal=json.loads(journalpath.read_text()) if journalpath.exists() else {'schema_version':1,'products':{}}
    replay_only=len(sys.argv)>2 and sys.argv[1]=='--merge-replay'
    if replay_only:journal=merge_journals(journal,json.loads(Path(sys.argv[2]).read_text()))
    # Include all product categories; food is checked first, not exclusively.
    candidates=[o for o in c.get('stores',{}).get('jumbo',{}).get('offers',[]) if o.get('start_date','z')<=day.isoformat()<=o.get('end_date','') and re.match(r'^https://www\.jumbo\.com/producten/[^/]+-\d+[A-Za-z]*$',o.get('source',{}).get('url',''))]
    candidates.sort(key=lambda o:(journal['products'].get(o['id'],{}).get('checked_at',''),o.get('category') in ('overig','huishouden'),o['id']))
    for o in candidates:
        if o.get('promotion_status')=='disputed' and journal['products'].get(o['id'],{}).get('verifier_version')!=VERIFIER_VERSION:
            o['promotion_status']='active';o.pop('verification_reason',None)
    journal['products']={k:v for k,v in journal['products'].items() if v.get('verifier_version')==VERIFIER_VERSION}
    attempts=0;counts={};limit=0 if replay_only else max(1,min(int(os.getenv('RETAILER_VERIFY_LIMIT','240')),500))
    # Replay all still-valid evidence before any request can fail or block.
    for o in candidates:
        prior=journal['products'].get(o['id'],{})
        if reusable(prior,o,day):apply(o,prior)
    selected=set(filter(None,os.getenv('RETAILER_VERIFY_IDS','').split(',')))
    deadline=time.monotonic()+420
    for o in candidates:
        prior=journal['products'].get(o['id'],{})
        if reusable(prior,o,day):
            apply(o,prior)
            if prior.get('verdict')=='confirmed' or prior.get('verdict')=='disputed':continue
        if selected and o['id'] not in selected:continue
        if attempts>=limit or time.monotonic()>=deadline:continue
        attempts+=1
        try:
            req=Request(o['source']['url'],headers={'User-Agent':'Boodschappenmaatje/1.0 public-product-verification'})
            with urlopen(req,timeout=15) as r:
                if r.geturl().rstrip('/')!=o['source']['url'].rstrip('/'):raise ValueError('Retailer redirected to another product or listing')
                result=assess(o,r.read(2500000).decode('utf8','replace'),day)
            result.update(verifier_version=VERIFIER_VERSION,checked_at=day.isoformat(),observed_at=dt.datetime.now(dt.timezone.utc).isoformat(),fingerprint=fingerprint(o))
            if result.get('verdict')=='confirmed':result['resolved_fingerprint']=fingerprint({**o,**{k:result['promotion_evidence'].get(k) for k in FIELDS}})
            journal['products'][o['id']]=result;apply(o,result)
        except HTTPError as exc:
            if exc.code in (401,403,429):break
        except (OSError,ValueError):pass
        time.sleep(.5)
    for o in candidates:
        r=journal['products'].get(o['id'],{});v=r.get('verdict','not_checked') if reusable(r,o,day) else 'not_checked';counts[v]=counts.get(v,0)+1
    journal.update(generated_at=dt.datetime.now(dt.timezone.utc).isoformat(),attempted=attempts,coverage=counts)
    journalpath.write_text(json.dumps(journal,ensure_ascii=False,separators=(',',':'))+'\n')
    catalogpath.write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n')
    print('Retailer offer reconciliation:',attempts,'requests;',counts,flush=True)
if __name__=='__main__':main()
