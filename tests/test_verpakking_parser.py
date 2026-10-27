import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from verpakking_parser import parse_packaging
from receptenradar_v2 import measure_offer

class PackagingAcrossRetailers(unittest.TestCase):
 def test_all_retailers_same_contract(self):
  examples=[
   ({"name":"Jumbo Varkenshaas Culinair 1 Stuk ca. 405 g","quantity":"1 stuk"},(405,"g")),
   ({"name":"AH kipfilet 600 gram","quantity":"1 stuk"},(600,"g")),
   ({"name":"Lidl vis 2x125 g"},(250,"g")),
   ({"name":"PLUS kwark","size":"1 kg"},(1000,"g")),
   ({"name":"Dirk melk","quantity":"1 l"},(1000,"ml")),
   ({"name":"Aldi frisdrank 6x330 ml"},(1980,"ml")),
   ({"name":"Hoogvliet yoghurt","size":"75 cl"},(750,"ml")),
   ({"name":"Xenos kruiden 2 stuks"},(2,"st")),
   ({"name":"Kruidvat tandpasta","size":"2 x 1 l"},(2000,"ml")),
   ({"name":"Jumbo diepvriesgroente","size":"1 x 500 g"},(500,"g"))
  ]
  for raw,expected in examples:
   with self.subTest(raw=raw):
    self.assertEqual(parse_packaging(raw),expected)
    self.assertEqual(measure_offer(raw),expected)
 def test_unknown_is_unknown(self):
  self.assertEqual(parse_packaging({"name":"Verse kip tegen dagprijs"}),(None,None))
 def test_approx_weight_beats_piece_count(self):
  self.assertEqual(parse_packaging({"name":"Varkenshaas 1 stuk ca. 405 g","size":"1 stuk"}),(405,"g"))
if __name__=="__main__":unittest.main()
