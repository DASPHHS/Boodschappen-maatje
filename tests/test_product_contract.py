"""Herbruikbare kwaliteitschecks voor genormaliseerde aanbiedingen."""
import unittest
from product_contract import normalized_offer, compare_sources, product_identity

class ProductContractTests(unittest.TestCase):
 def test_invalid_price(self):
  self.assertIsNone(normalized_offer({"name":"Kwark","price":float("nan")},"ah","a","2026-10-27"))
 def test_variant_sizes_remain_separate(self):
  a={"name":"Skyr naturel","quantity":500,"unit":"g"}
  b={"name":"Skyr naturel","quantity":1000,"unit":"g"}
  self.assertNotEqual(product_identity(a),product_identity(b))
 def test_independent_agreement(self):
  rows=[normalized_offer({"name":"Kwark","price":2.49,"quantity":1000,"unit":"g"},"ah",source,"2026-10-27") for source in ("api","official")]
  self.assertEqual(compare_sources(rows)[0]["status"],"confirmed_by_two_sources")
  rows[-1]["price"]=3.49
  self.assertEqual(compare_sources(rows)[0]["status"],"conflicting_sources")
 def test_dont_merge_two_single_sources(self):
  row=normalized_offer({"name":"Kwark","price":2.49},"jumbo","api","2026-10-27")
  self.assertEqual(compare_sources([row])[0]["status"],"single_source")
if __name__=="__main__":unittest.main()
