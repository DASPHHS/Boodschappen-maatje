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
if __name__=='__main__':unittest.main()
