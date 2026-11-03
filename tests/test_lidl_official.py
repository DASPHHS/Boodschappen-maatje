import unittest,json,sys,copy,tempfile
from pathlib import Path
from datetime import date
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import sync_lidl_official as s
class LidlOfficial(unittest.TestCase):
    def setUp(self):self.p=json.loads((Path(__file__).parent/'fixtures/lidl-grid-product.json').read_text());self.today=date(2026,10,30)
    def parse(self,p=None):return s.parse_product(p or self.p,self.today,s.SEED)
    def test_real_public_grid(self):
        o=self.parse();self.assertEqual(o['price'],1.89);self.assertEqual(o['without_membership_price'],2.19);self.assertTrue(o['member_required']);self.assertEqual(o['category'],'vega');self.assertEqual(o['end_date'],'2026-11-01')
        regular=s.parse_product(self.p,self.today,s.SEED,False);self.assertEqual(regular['price'],2.19);self.assertFalse(regular['member_required'])
    def test_promotion_proof_matches_actual_price_window(self):
        p=copy.deepcopy(self.p)
        price=p['regionsPrices']['1']['currentLidlPlusPrice']['price']
        price['endDate']='2026-10-30T22:59:59Z'
        o=self.parse(p)
        self.assertEqual(o['end_date'],'2026-10-30')
        e=o['promotion_evidence']
        for key in ['name','price','pack_label','start_date','end_date','member_required','requires_membership']:
            self.assertEqual(e[key],o[key])
        self.assertEqual(e['url'],o['source']['url'])
        self.assertEqual(e['checked_at'],self.today.isoformat())
    def test_regional_price_not_guessed(self):
        self.p['regionsPrices']['2']=copy.deepcopy(self.p['regionsPrices']['1']);self.p['regionsPrices']['2']['currentPrice']['price']=99
        self.assertIsNone(self.parse())
    def test_expired_upcoming_online_unknown_price(self):
        self.assertIsNone(s.parse_product(self.p,date(2026,11,5),s.SEED));self.assertIsNone(s.parse_product(self.p,date(2026,10,20),s.SEED))
        for field,value in [('online',True),('store',False),('canonicalUrl','https://evil.example/p1'),('productType','RETAIL_HEAD')]:
            p=copy.deepcopy(self.p);p[field]=value;self.assertIsNone(self.parse(p))
        p=copy.deepcopy(self.p);p['regionsPrices']['1']['currentLidlPlusPrice']['price']['currencyCode']='USD';self.assertIsNone(self.parse(p))
    def test_grid_json_decoded_and_bad_json_visible(self):
        from html import escape
        g=s.Grid();g.feed('<div data-grid-data="'+escape(json.dumps(self.p),quote=True)+'"></div><div data-grid-data="broken"></div>');self.assertEqual(len(g.products),1);self.assertEqual(g.errors,1)
    def test_failure_preserves_original_evidence_dates(self):
        from datetime import datetime
        now=s.datetime.now(s.ZoneInfo('Europe/Amsterdam'));o=self.parse();o['end_date']='2099-01-01';o['checked_at']='2026-10-20'
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'out.json';out.write_text(json.dumps({'stores':{'lidl':{'offers':[o],'official_prices':[o]}}}))
            with patch.object(s,'OUT',out),patch.object(s,'fetch',side_effect=OSError('unavailable')):self.assertEqual(s.main(),2)
            data=json.loads(out.read_text())['stores']['lidl'];self.assertEqual(data['offers'][0]['checked_at'],'2026-10-20');self.assertEqual(data['official_check']['status'],'partial')
    def test_service_failure_retried_once(self):
        from urllib.error import HTTPError
        from io import BytesIO
        error=HTTPError(s.SEED,503,'Service unavailable',{},None)
        with patch.object(s,'urlopen',side_effect=[error,BytesIO(b'ok')]) as request,patch.object(s.time,'sleep'):
            self.assertEqual(s.fetch(s.SEED),'ok');self.assertEqual(request.call_count,2)
        for code in [403,429]:
            with patch.object(s,'urlopen',side_effect=HTTPError(s.SEED,code,'Denied',{},None)) as request,patch.object(s.time,'sleep'):
                with self.assertRaises(HTTPError):s.fetch(s.SEED)
                self.assertEqual(request.call_count,1)
    def test_secondary_source_runs_after_primary_service_failure(self):
        from html import escape
        # Keep fixture dates current for this integration check.
        p=copy.deepcopy(self.p)
        from datetime import timedelta
        now=s.datetime.now(s.ZoneInfo('Europe/Amsterdam'));today=now.date()
        p['storeStartDate']=int(now.timestamp());p['storeEndDate']=int((now+timedelta(days=1)).timestamp())
        price=p['regionsPrices']['1']['currentLidlPlusPrice']['price']
        price['startDate']=now.isoformat();price['endDate']=(now+timedelta(days=1)).isoformat()
        p['regionsPrices']['1']['currentPrice']['startDate']=now.isoformat()
        html='<div data-grid-data="'+escape(json.dumps(p),quote=True)+'"></div>'
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'out.json'
            with patch.object(s,'OUT',out),patch.object(s,'fetch',side_effect=[OSError('service unavailable'),html]),patch.object(s.time,'sleep'):
                self.assertEqual(s.main(),2)
            st=json.loads(out.read_text())['stores']['lidl'];self.assertEqual(st['official_check']['current_offers'],1)
            self.assertEqual(st['offers'][0]['price'],1.89)
    def test_optional_editorial_page_without_grid_is_not_broken_import(self):
        from html import escape
        html='<div data-grid-data="'+escape(json.dumps(self.p),quote=True)+'"></div>'
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'out.json'
            with patch.object(s,'OUT',out),patch.object(s,'fetch',side_effect=[html,'<main>Lidl Plus</main>']),patch.object(s.time,'sleep'):
                self.assertEqual(s.main(),0)
            self.assertIn(s.PLUS_SEED,json.loads(out.read_text())['stores']['lidl']['official_check']['skipped_pages'])
if __name__=='__main__':unittest.main()
