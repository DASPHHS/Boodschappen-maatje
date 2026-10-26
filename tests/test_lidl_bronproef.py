import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from lidl_bronproef import evaluate_pages
class SourceProbeTests(unittest.TestCase):
 def test_repeated_page(self):
  p={"results":[{"id":"a","name":"X","retailer":"lidl"}],"total":200}
  self.assertIn("herhaalde-pagina",evaluate_pages([p,p])["issues"])
 def test_schema_mismatch(self):
  self.assertIn("geen-productlijst",evaluate_pages([{"unexpected":[]}])["issues"])
 def test_other_retailer_detected(self):
  self.assertIn("ander-winkellabel",evaluate_pages([{"results":[{"id":1,"retailer":"jumbo"}]}])["issues"])
 def test_no_false_full_coverage(self):
  self.assertFalse(evaluate_pages([{"results":[{"id":1,"retailer":"lidl"}]}])["proven_full_coverage"])
if __name__=="__main__":unittest.main()
