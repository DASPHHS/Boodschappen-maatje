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
    def test_truncated_full_sync_rejected(self):
        def get(path,params):return {'cursor':1,'has_more':False,'changes':[]} if path.endswith('changes') else {'total':101,'products':[self.product('one')]}
        with self.assertRaises(ValueError):sync('lidl',None,get)
class Folderz(unittest.TestCase):
    url='https://www.folderz.nl/winkels/lidl/aanbiedingen/broccoli-aanbieding-123/'
    def html(self,**kw):
        offer=dict(seller={'@id':'lidl'},url=self.url,priceCurrency='EUR',validFrom='2026-10-26T00:00:00+01:00',validThrough='2026-11-01T23:59:59+01:00',price='0.69');offer.update(kw)
        return '<script type="application/ld+json">'+json.dumps({'@graph':[{'@type':'Organization','@id':'lidl','name':'Lidl'},{'@type':'Product','name':'Broccoli','offers':[offer]}]})+'</script>'
    def test_dated_external_price_without_guessed_weight(self):
        o=parse(self.html(),self.url,date(2026,11,1));self.assertEqual(o['price'],.69);self.assertFalse(o['verified']);self.assertIsNone(o['regular_price']);self.assertEqual(o['pack_label'],'inhoud niet bevestigd')
    def test_wrong_seller_expired_currency_missing_dates_rejected(self):
        for kw in [dict(seller={'@id':'ah'}),dict(priceCurrency='USD'),dict(validFrom=''),dict(validThrough='2026-10-30T23:59:59+01:00')]:self.assertIsNone(parse(self.html(**kw),self.url,date(2026,11,1)))
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
if __name__=='__main__':unittest.main()

