import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from officiele_winkelbronnen import parse_official_products

class OfficialSourcesTests(unittest.TestCase):
    def test_valid_own_domain_product_without_discount_claim(self):
        html='''<script type="application/ld+json">{"@graph":[
          {"@type":"Product","name":"Koffie bonen 1 kg",
            "url":"https://www.action.com/nl-nl/p/koffie/",
            "offers":{"price":"5.49"}},
          {"@type":"Product","name":"Koffie bonen 1 kg",
            "url":"https://untrusted.example/p/koffie/","offers":{"price":"1"}}]}
          </script>'''
        rows=parse_official_products(html,"https://www.action.com/nl-nl/weekactie/")
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["price"],5.49)
        self.assertFalse(rows[0]["discount_verified"])

    def test_no_price_invented(self):
        html='<script type="application/ld+json">{"@type":"Product","name":"Afwasmiddel","url":"https://www.xenos.nl/afwasmiddel"}</script>'
        rows=parse_official_products(html,"https://www.xenos.nl/folder")
        self.assertEqual(rows[0]["price"],None)

    def test_script_without_structured_products(self):
        self.assertEqual(parse_official_products("<h1>Veel deals</h1>",
            "https://www.lidl.nl/c/aanbiedingen/a10008785"),[])
if __name__=="__main__":unittest.main()
