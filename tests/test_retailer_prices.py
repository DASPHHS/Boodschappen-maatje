import sys,unittest,json
sys.path.insert(0,'src')
from retailer_prices import parse_product
class RetailerTests(unittest.TestCase):
 def test_exact_structured_product_and_quantity(self):
  p={'@type':'Product','name':'Finish vaatwastabletten','sku':'123','description':'21 stuks. Inhoud 218 g.','offers':{'price':'4.38','priceCurrency':'EUR'}}
  row=parse_product('<script type="application/ld+json">'+json.dumps(p)+'</script>','https://www.action.com/nl-nl/p/123/')
  self.assertEqual(row['price'],4.38);self.assertEqual(row['quantity'],21);self.assertEqual(row['unit'],'st');self.assertIn('21 tabletten',row['name']);self.assertFalse(row['promotion'])
 def test_no_invented_price(self):
  self.assertIsNone(parse_product('<html>vanaf 1 euro</html>','https://example.com'))
 def test_non_euro_rejected(self):
  self.assertIsNone(parse_product('<script type="application/ld+json">{"@type":"Product","name":"x","offers":{"price":1,"priceCurrency":"USD"}}</script>','https://example.com'))
