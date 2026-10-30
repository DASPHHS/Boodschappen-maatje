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
if __name__=='__main__':unittest.main()
