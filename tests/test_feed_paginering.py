import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from feed_paginering import pagination_issue,page_fingerprint
class PaginationTests(unittest.TestCase):
 def test_duplicate_page(self):
  rows=[{"id":1,"price":1.99}]
  self.assertEqual(pagination_issue(rows,{page_fingerprint(rows)},2),"herhaalde_pagina")
 def test_normal_page(self):
  rows=[{"id":2,"price":1.99}]
  self.assertIsNone(pagination_issue(rows,{page_fingerprint([{"id":1,"price":1.99}])},2))
 def test_empty_before_end(self):
  self.assertEqual(pagination_issue([],set(),2,total=500),"voortijdig_lege_pagina")
 def test_bad_format(self):
  self.assertEqual(pagination_issue({},set(),1),"ongeldig_formaat")
if __name__=="__main__":unittest.main()
