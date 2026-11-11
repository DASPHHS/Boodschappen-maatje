import unittest,json,sys
from pathlib import Path
from urllib.error import HTTPError
from datetime import date
from scripts.promotion_changefeed import sync
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from sync_folderz import parse
class ChangeFeed(unittest.TestCase):
    def product(self,key,**kw):return dict(product_id=key,retailer='lidl',name='Broccoli',**kw)
    def test_bootstrap_captures_cursor_before_products(self):
        calls=[]
        def get(path,params):
            calls.append(path)
            return {'cursor':10,'has_more':False,'changes':[]} if path.endswith('changes') else {'total':1,'products':[self.product('one')]}
        s,mode=sync('lidl',None,get);self.assertEqual(calls,['/products/changes','/products']);self.assertEqual(mode,'bootstrap');self.assertEqual(s['cursor'],10)
    def test_ordered_upsert_delete_and_cursor_commit(self):
        old={'retailer':'lidl','cursor':10,'products':{'one':self.product('one')}}
        pages=iter([{'cursor':11,'has_more':True,'changes':[{'seq':11,'change':'delete','product_id':'one','retailer':'lidl'}]},
        {'cursor':12,'has_more':False,'changes':[{'seq':12,'change':'upsert','product_id':'two','retailer':'lidl','product':self.product('two')}]}])
        new,mode=sync('lidl',old,lambda *a:next(pages));self.assertEqual(mode,'delta');self.assertEqual(list(new['products']),['two']);self.assertEqual(new['cursor'],12);self.assertIn('one',old['products']);self.assertEqual(old['cursor'],10)
    def test_failed_second_page_does_not_mutate_original(self):
        old={'retailer':'lidl','cursor':10,'products':{}};calls=[]
        def get(*a):
            calls.append(1)
            if len(calls)>1:raise OSError('network failure')
            return {'cursor':11,'has_more':True,'changes':[{'seq':11,'change':'upsert','product_id':'one','retailer':'lidl','product':self.product('one')}]}
        with self.assertRaises(OSError):sync('lidl',old,get)
        self.assertEqual(old['cursor'],10);self.assertEqual(old['products'],{})
    def test_expired_cursor_bootstraps(self):
        calls=[]
        def get(path,params):
            calls.append(path)
            if len(calls)==1:raise HTTPError('url',410,'expired',{},None)
            return {'cursor':99,'has_more':False,'changes':[]} if path.endswith('changes') else {'total':0,'products':[]}
        new,mode=sync('lidl',{'retailer':'lidl','cursor':1,'products':{}},get);self.assertEqual(mode,'bootstrap');self.assertEqual(new['cursor'],99)
    def test_malformed_or_unscoped_changes_stop(self):
        old={'retailer':'lidl','cursor':1,'products':{}}
        for data in [{'cursor':1,'has_more':True,'changes':[]},{'cursor':2,'has_more':False,'changes':[{'retailer':'jumbo','product_id':'x','change':'delete'}]}]:
            with self.assertRaises(ValueError):sync('lidl',old,lambda *a:data)
    def test_corrupt_cached_rows_bootstrap_instead_of_sticking(self):
        def get(path,params):return {'cursor':20,'has_more':False,'changes':[]} if path.endswith('changes') else {'total':0,'products':[]}
        state,mode=sync('lidl',{'retailer':'lidl','cursor':1,'products':{'bad':'broken'}},get)
        self.assertEqual(mode,'bootstrap');self.assertEqual(state['products'],{})
    def test_truncated_full_sync_rejected(self):
        def get(path,params):return {'cursor':1,'has_more':False,'changes':[]} if path.endswith('changes') else {'total':101,'products':[self.product('one')]}
        with self.assertRaises(ValueError):sync('lidl',None,get)
    def test_non_advancing_cursor_with_changes_is_rejected(self):
        old={'retailer':'lidl','cursor':20,'products':{}}
        data={'cursor':20,'has_more':False,'changes':[{'seq':21,'change':'delete','product_id':'x','retailer':'lidl'}]}
        with self.assertRaisesRegex(ValueError,'without advancing'):
            sync('lidl',old,lambda *_:data)
        self.assertEqual(old['cursor'],20)
    def test_duplicate_or_unsorted_change_sequences_rejected_without_committing(self):
        old={'retailer':'lidl','cursor':12,'products':{'one':self.product('one')}}
        for seqs in ([5,5],[8,7],[-1,2],['8',9]):
            data={'cursor':30,'has_more':False,'changes':[
                {'seq':s,'change':'delete','product_id':'one','retailer':'lidl'} for s in seqs]}
            with self.subTest(seqs=seqs),self.assertRaisesRegex(ValueError,'sequence'):
                sync('lidl',old,lambda *_:data)
            self.assertIn('one',old['products'])
    def test_cursor_is_opaque_and_not_used_as_sequence_limit(self):
        old={'retailer':'lidl','cursor':15,'products':{'one':self.product('one')}}
        data={'cursor':100,'has_more':False,'changes':[
            {'seq':500,'change':'delete','product_id':'one','retailer':'lidl'}]}
        updated,mode=sync('lidl',old,lambda *_:data)
        self.assertEqual(updated['products'],{})
        self.assertEqual(updated['cursor'],100)
        self.assertEqual(mode,'delta')

class PrijsProfeetPriceEvidence(unittest.TestCase):
    def test_only_active_valid_prices_and_honest_discounts(self):
        from scripts.sync_aanbiedingen import item
        base={'product_id':'100','name':'Broccoli 500 g','price':1.45,
              'promotion_status':'active','valid_from':'2026-10-29','valid_until':'2026-11-04',
              'product_url':'https://www.ah.nl/producten/product/wi123/example','quantity':'500 g'}
        valid=item(dict(base,original_price=2.5,loyalty_price=1.1,valid_until_estimated=True),'2026-11-01')
        self.assertAlmostEqual(valid['regular_price'],2.5)
        self.assertAlmostEqual(valid['loyalty_price'],1.1)
        self.assertTrue(valid['date_estimated'])
        self.assertFalse(valid['verified'])
        for raw in [dict(base,price=float('nan')),dict(base,price=float('inf')),dict(base,price=True),
                    dict(base,promotion_status='upcoming'),dict(base,valid_from='2026-11-08'),
                    dict(base,valid_until='2026-10-31')]:
            self.assertIsNone(item(raw,'2026-11-01'))
        bad=item(dict(base,original_price=1.0,loyalty_price=4.0),'2026-11-01')
        self.assertIsNone(bad['regular_price'])
        self.assertIsNone(bad['loyalty_price'])
class Folderz(unittest.TestCase):
    url='https://www.folderz.nl/winkels/lidl/aanbiedingen/broccoli-aanbieding-123/'
    def html(self,**kw):
        offer=dict(seller={'@id':'lidl'},url=self.url,priceCurrency='EUR',validFrom='2026-10-26T00:00:00+01:00',validThrough='2026-11-01T23:59:59+01:00',price='0.69');offer.update(kw)
        return '<script type="application/ld+json">'+json.dumps({'@graph':[{'@type':'Organization','@id':'lidl','name':'Lidl'},{'@type':'Product','name':'Broccoli','offers':[offer]}]})+'</script>'
    def test_dated_external_price_without_guessed_weight(self):
        o=parse(self.html(),self.url,date(2026,11,1));self.assertEqual(o['price'],.69);self.assertFalse(o['verified']);self.assertIsNone(o['regular_price']);self.assertEqual(o['pack_label'],'inhoud niet bevestigd')
    def test_wrong_seller_expired_currency_missing_dates_rejected(self):
        for kw in [dict(seller='lidl'),dict(price=True),dict(seller={'@id':'ah'}),dict(priceCurrency='USD'),dict(validFrom=''),dict(validThrough='2026-10-30T23:59:59+01:00')]:self.assertIsNone(parse(self.html(**kw),self.url,date(2026,11,1)))
class ImportTransaction(unittest.TestCase):
    def test_main_bootstrap_delta_then_failure_retains_both_versions(self):
        import tempfile
        from unittest.mock import patch
        from scripts import sync_aanbiedingen as importer
        product=dict(product_id='one',retailer='lidl',name='Broccoli',promotion_status='active',valid_from='2020-01-01',valid_until='2099-01-01',price=1)
        def first(params,base):
            return {'cursor':3,'has_more':False,'changes':[]} if base.endswith('changes') else {'total':1,'products':[product]}
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'feed.json';state=Path(td)/'state.json'
            with patch.object(importer,'OUT',out),patch.object(importer,'SYNC_STATE',state),patch.object(importer,'RETAILERS',{'lidl':'lidl'}),patch.object(importer.time,'sleep'):
                with patch.object(importer,'request',side_effect=first):self.assertEqual(importer.main(),0)
                self.assertEqual(json.loads(out.read_text())['stores']['lidl']['sync_mode'],'bootstrap')
                changed=dict(product,price=2)
                with patch.object(importer,'request',return_value={'cursor':4,'has_more':False,'changes':[{'seq':4,'change':'upsert','product_id':'one','retailer':'lidl','product':changed}]}):self.assertEqual(importer.main(),0)
                self.assertEqual(json.loads(out.read_text())['stores']['lidl']['offers'][0]['price'],2)
                prior_feed=out.read_text();prior_state=state.read_text()
                with patch.object(importer,'request',side_effect=OSError('service down')):self.assertEqual(importer.main(),1)
                self.assertEqual(out.read_text(),prior_feed);self.assertEqual(state.read_text(),prior_state)

class ProteinOfferClassification(unittest.TestCase):
    def test_sukade_riblappen_and_shoarma_are_protein_bases(self):
        from scripts.sync_aanbiedingen import kind
        for name,expected in [
            ('Jumbo Rund Sukadelappen 525 g','vlees'),
            ('Jumbo Rund Riblappen 500 g','vlees'),
            ('Jumbo Kipshoarma 300 g','kip'),
            ('Jumbo Kip Shoarma 300 g','kip'),
            ('Jumbo Varken Shoarma 500 g','vlees'),
            ('Jumbo Shoarma 500 g','vlees'),
            ('Vegetarische shoarma 175 g','vega'),
        ]:
            with self.subTest(name=name):
                self.assertEqual(kind(name),expected)
    def test_spices_sauces_and_meals_not_meat_bases(self):
        from scripts.sync_aanbiedingen import kind
        for name in ['Shoarmakruiden', 'Shoarmasaus', 'Kipshoarma maaltijd', 'Shoarma kruidenmix']:
            with self.subTest(name=name):
                self.assertIsNone(kind(name))
    def test_expired_promotion_cannot_reenter_feed(self):
        from scripts.sync_aanbiedingen import item
        base=dict(product_id='shoarma',name='Jumbo Kipshoarma 300 g',
                  promotion_status='active',price=4.35,valid_from='2026-11-11',
                  valid_until='2026-11-17')
        self.assertIsNotNone(item(base,'2026-11-11'))
        self.assertIsNone(item(base,'2026-11-18'))
        self.assertIsNone(item({**base,'promotion_status':'upcoming'},'2026-11-11'))

if __name__=='__main__':unittest.main()

