import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import sync_product_evidence as evidence
class EvidenceTests(unittest.TestCase):
    def page(self,value):return '<script type="application/ld+json">'+json.dumps(value)+'</script>'
    def test_exact_product_identity_and_categories_required(self):
        p={'@type':'Product','sku':'wi123','name':'AH Kipfilet','category':'Verse kipfilet'}
        e=evidence.extract(self.page(p),'https://www.ah.nl/producten/product/wi123/kip','ah','wi123/kip')
        self.assertTrue(e['verified_identity']);self.assertEqual(e['categories'],['Verse kipfilet'])
        with self.assertRaises(ValueError):evidence.extract(self.page(p),'https://www.ah.nl/producten/product/wi999/kip','ah','wi999/kip')
        with self.assertRaises(ValueError):evidence.extract(self.page(p),'https://attacker.example/product','ah','wi123/kip')
        del p['category']
        with self.assertRaises(ValueError):evidence.extract(self.page(p),'https://www.ah.nl/producten/product/wi123/kip','ah','wi123/kip')
    def test_aggregate_price_only_when_all_prices_agree(self):
        p={'@type':'Product','sku':'wi123','name':'Kipfilet','category':'Kipfilet',
           'brand':{'name':'Nieuwmerk'},'offers':{'@type':'AggregateOffer','lowPrice':2.99,'highPrice':2.99,'priceCurrency':'EUR'}}
        url='https://www.ah.nl/producten/product/wi123/kip'
        e=evidence.extract(self.page(p),url,'ah','wi123/kip')
        self.assertEqual(e['observed_price'],2.99);self.assertEqual(e['brand'],'Nieuwmerk')
        p['offers']['highPrice']=3.99
        self.assertIsNone(evidence.extract(self.page(p),url,'ah','wi123/kip')['observed_price'])
    def test_non_product_and_malformed_metadata_is_not_evidence(self):
        for p in [{'@type':'WebPage','name':'Kipfilet'}, {'@type':'Product','sku':'wi123','name':'Other','category':'other'}]:
            with self.assertRaises(ValueError):evidence.extract(self.page(p),'https://www.ah.nl/producten/product/wi999/kip','ah','wi999/kip')
    def test_fingerprint_invalidates_changed_name_or_pack(self):
        self.assertNotEqual(evidence.fingerprint('Kipfilet','500 g'),evidence.fingerprint('Kipfilet gerookt','500 g'))
        self.assertNotEqual(evidence.fingerprint('Kipfilet','500 g'),evidence.fingerprint('Kipfilet','800 g'))

class RetailerRecoveryTests(unittest.TestCase):
    def setUp(self):
        import copy
        self.product=json.loads((Path(__file__).parent/'fixtures/jumbo-public-product.json').read_text())
        self.url=self.product['canonicalUrl'];self.pid=self.url.rsplit('/',1)[-1]
    def nuxt(self,*products):
        table=[]
        def encode(value):
            index=len(table);table.append(None)
            if isinstance(value,dict):table[index]={k:encode(v) for k,v in value.items()}
            elif isinstance(value,list):table[index]=[encode(v) for v in value]
            else:table[index]=value
            return index
        for product in products:encode(product)
        return '<script id="__NUXT_DATA__" type="application/json">'+json.dumps(table)+'</script>'
    def offer(self):
        return dict(id='sample',name=self.product['title'],pack_label='1.5 l',price=2.79,start_date='2026-10-28',end_date='2026-11-03',source={'url':self.url},member_required=False)
    def test_live_nuxt_identity_pack_price_and_categories(self):
        import copy
        other=copy.deepcopy(self.product);other.update(sku='999OTHER',canonicalUrl='https://www.jumbo.com/producten/ander-999OTHER');other['price']['price']=1
        e=evidence.extract(self.nuxt(other,self.product),self.url,'jumbo',self.pid)
        self.assertEqual(e['observed_price'],2.79);self.assertEqual(e['product_pack'],'1.5 liter')
        self.assertIn('Volle melk',e['categories']);self.assertEqual(e['ean'],'8713300402994')
        with self.assertRaises(ValueError):evidence.extract(self.nuxt(other),self.url,'jumbo',self.pid)
    def test_ah_breadcrumb_scoped_and_exact_jsonld_identity(self):
        p={'@type':'Product','sku':'wi123','name':'AH Pompoen','weight':{'value':'per stuk'},'offers':{'price':'2.49','priceCurrency':'EUR'}}
        page='<a href="/producten/snacks">Snoep</a><nav data-testid="breadcrumb-nav"><a href="/producten/groente">Groente</a><a href="/producten/merk/test">Merk</a></nav>'
        html='<script type="application/ld+json">'+json.dumps(p)+'</script>'+page
        e=evidence.extract(html,'https://www.ah.nl/producten/product/wi123/pompoen','ah','wi123/pompoen')
        self.assertEqual(e['categories'],['Groente']);self.assertEqual(e['product_pack'],'per stuk')
        with self.assertRaises(ValueError):evidence.extract(html,'https://www.ah.nl/producten/product/wi999/pompoen','ah','wi999/pompoen')
    def test_delivery_discount_does_not_confirm_product_discount(self):
        from verify_retailer_offers import assess
        from datetime import date
        r=assess(self.offer(),self.nuxt(self.product),date(2026,11,3))
        self.assertEqual(r['verdict'],'disputed');self.assertIn('delivery',r['reason'])
    def test_conditional_bundle_is_not_a_single_pack_price_conflict(self):
        from verify_retailer_offers import assess
        from datetime import date
        self.product['promotions'][0].update(group='ProductPromotion',tags=[{'text':'1 + 1 gratis'}])
        o=self.offer();o['price']=1.40
        self.assertEqual(assess(o,self.nuxt(self.product),date(2026,11,3))['verdict'],'unresolved')
    def test_actual_discount_with_exact_window_confirms(self):
        from verify_retailer_offers import assess, reusable, fingerprint, VERIFIER_VERSION
        from datetime import date
        self.product['price']['promoPrice']=200
        self.product['promotions'][0].update(group='ProductPromotion',tags=[{'text':'Korting'}])
        o=self.offer();o['price']=2
        r=assess(o,self.nuxt(self.product),date(2026,11,3))
        self.assertEqual(r['verdict'],'confirmed');self.assertEqual(r['regular_price'],2.79)
        r.update(checked_at='2026-11-03',fingerprint=fingerprint(o),verifier_version=VERIFIER_VERSION)
        self.assertTrue(reusable(r,o,date(2026,11,3)))
        self.assertFalse(reusable(r,{**o,'price':1.99},date(2026,11,3)))
        o['end_date']='2026-11-04'
        self.assertEqual(assess(o,self.nuxt(self.product),date(2026,11,3))['verdict'],'unresolved')
    def test_metadata_merge_preserves_newer_and_checks_fingerprint(self):
        from merge_product_evidence import merge,enrich
        from datetime import date
        row=['Product',2,'500 g','https://www.jumbo.com/producten/product-123','product-123']
        e={'status':'ok','verified_identity':True,'checked_at':'2026-11-03','last_attempt':'2026-11-03','fingerprint':evidence.fingerprint('Product','500 g')}
        old={'products':{'jumbo:product-123':{**e,'last_attempt':'2026-11-01'}}};new={'products':{'jumbo:product-123':e}}
        combined=merge(new,old);self.assertEqual(combined['products']['jumbo:product-123']['last_attempt'],'2026-11-03')
        catalog={'stores':{'jumbo':[row]}};self.assertEqual(enrich(catalog,combined,date(2026,11,3)),1)
        row[2]='1 kg';self.assertEqual(enrich(catalog,combined,date(2026,11,3)),0)

    def test_bundle_confirmed_with_mandatory_quantity_and_total(self):
        from verify_retailer_offers import assess,pack_key
        from datetime import date
        self.product['promotions'][0].update(group='Week',tags=[{'text':'4 voor 4,99'}])
        o=self.offer();o.update(price=1.25,multi_buy_quantity=4,multi_buy_price=4.99)
        r=assess(o,self.nuxt(self.product),date(2026,11,3))
        self.assertEqual(r['verdict'],'confirmed')
        self.assertEqual(r['promotion_evidence']['multi_buy_price'],4.99)
        self.assertEqual(r['promotion_evidence']['multi_buy_quantity'],4)
        self.assertEqual(pack_key('6 x 30 cl'),pack_key('6 x 300 ml'))
        o['multi_buy_price']=4
        self.assertNotEqual(assess(o,self.nuxt(self.product),date(2026,11,3))['verdict'],'confirmed')


    def test_explicit_quantity_in_exact_product_title_fills_missing_subtitle(self):
        self.product['subtitle']=None
        self.product['title']='Grolsch Winterbok 6x300ML'
        e=evidence.extract(self.nuxt(self.product),self.url,'jumbo',self.pid)
        self.assertEqual(e['product_pack'],'6x300ML')
    def test_fixed_price_offer_requires_matching_source_tag_and_period(self):
        from verify_retailer_offers import assess
        from datetime import date
        self.product['promotions'][0].update(group='Week',tags=[{'text':'voor 2,79'}])
        r=assess(self.offer(),self.nuxt(self.product),date(2026,11,3))
        self.assertEqual(r['verdict'],'confirmed')
        self.product['promotions'][0]['tags']=[{'text':'voor 1,99'}]
        self.assertNotEqual(assess(self.offer(),self.nuxt(self.product),date(2026,11,3))['verdict'],'confirmed')


    def test_access_denial_does_not_erase_previously_confirmed_imports(self):
        import tempfile
        from unittest.mock import patch
        from urllib.error import HTTPError
        import verify_retailer_offers as v
        day=v.dt.datetime.now(v.ZoneInfo('Europe/Amsterdam')).date()
        o=self.offer();o.update(id='cached',price=2,start_date=day.isoformat(),end_date=(day+v.dt.timedelta(days=1)).isoformat())
        proof={k:o.get(k) for k in v.FIELDS};proof.update(price=2,status='available',checked_at=day.isoformat(),url=self.url)
        cached={'checked_at':day.isoformat(),'verifier_version':v.VERIFIER_VERSION,'fingerprint':v.fingerprint(o),'verdict':'confirmed','regular_price':2.79,'promotion_evidence':proof}
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'offers-catalog.json').write_text(json.dumps({'stores':{'jumbo':{'offers':[{**o,'id':'first-new'},o]}}}))
            (root/'retailer-offer-evidence.json').write_text(json.dumps({'schema_version':1,'products':{'cached':cached}}))
            with patch.object(v,'ROOT',root),patch.object(v,'urlopen',side_effect=HTTPError(self.url,403,'Denied',{},None)),patch.dict(v.os.environ,{'RETAILER_VERIFY_IDS':''}):v.main()
            saved=json.loads((root/'offers-catalog.json').read_text())['stores']['jumbo']['offers']
            self.assertTrue(next(x for x in saved if x['id']=='cached')['verified'])


    def test_rebased_offer_journal_keeps_all_newer_confirmations(self):
        from verify_retailer_offers import merge_journals
        current={'products':{'a':{'observed_at':'2026-11-03T12:00:00Z'},'b':{'checked_at':'2026-11-03'}}}
        incoming={'products':{'a':{'observed_at':'2026-11-03T11:00:00Z'},'c':{'checked_at':'2026-11-03'}}}
        merged=merge_journals(current,incoming)['products']
        self.assertEqual(set(merged),{'a','b','c'})
        self.assertEqual(merged['a']['observed_at'],'2026-11-03T12:00:00Z')


    def test_second_half_price_and_source_confirmed_six_week_window(self):
        from verify_retailer_offers import assess,bundle_terms
        from datetime import date
        self.assertEqual(bundle_terms({'tags':[{'text':'2e halve prijs'}]},2.49),(2,3.74))
        self.product['price']['promoPrice']=200
        p=self.product['promotions'][0]
        p.update(group='Week',tags=[{'text':'Korting'}],start={'date':23,'monthShort':'sep','dayShort':'wo'})
        o=self.offer();o.update(price=2,start_date='2026-09-23')
        self.assertEqual(assess(o,self.nuxt(self.product),date(2026,11,3))['verdict'],'confirmed')
        p['start']['dayShort']='di'
        self.assertNotEqual(assess(o,self.nuxt(self.product),date(2026,11,3))['verdict'],'confirmed')


    def test_counted_packs_and_promotion_cap_are_preserved(self):
        from verify_retailer_offers import assess,pack_key,apply
        from datetime import date
        self.assertEqual(pack_key('350 gr'),pack_key('350 g'))
        self.assertEqual(pack_key('60 stuks'),(60,'piece'))
        self.assertNotEqual(pack_key('60 stuks'),pack_key('60 g'))
        self.product['subtitle']=None;self.product['title']='Nieuw product 60 stuks'
        self.product['promotions'][0].update(group='Week',tags=[{'text':'2 voor 4,99'}],maxPromotionQuantity=4)
        o=self.offer();o.update(pack_label='60 stuks',price=2.50,multi_buy_quantity=2,multi_buy_price=4.99)
        result=assess(o,self.nuxt(self.product),date(2026,11,3))
        self.assertEqual(result['verdict'],'confirmed')
        self.assertEqual(result['promotion_evidence']['max_promotion_quantity'],4)
        apply(o,result);self.assertEqual(o['max_promotion_quantity'],4)

if __name__=='__main__':unittest.main()
