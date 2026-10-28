import unittest
from datetime import date
from scripts.sync_lidl_supplemental import parse
class SupplementalTests(unittest.TestCase):
 def setUp(self):
  self.source={"id":"test","name":"Perlenbacher Strong","category":"bier","liters":0.5,"pack_label":"500 ml","url":"https://www.biernet.nl/example","provider":"Biernet"}
  self.html="<html><body>Normale Prijs <b>€1,49</b> Aanbieding prijs <b>€1,12</b> Geldig vanaf maandag 26 oktober 2026 Geldig t/m zondag 1 november 2026</body></html>"
 def test_active_price_and_dates(self):
  x=parse(self.html,self.source,date(2026,10,28))
  self.assertEqual(x["price"],1.12);self.assertEqual(x["unit_price"],2.24)
  self.assertFalse(x["verified"])
 def test_expired_never_published(self):
  self.assertIsNone(parse(self.html,self.source,date(2026,11,2)))
 def test_dont_publish_old_ad(self):
  self.assertIsNone(parse(self.html+" Deze bier aanbieding is niet meer geldig",self.source,date(2026,10,28)))
 def test_no_guessing_prices(self):
  with self.assertRaises(ValueError):parse(self.html.replace("€1,12","aanbieding onbekend"),self.source,date(2026,10,28))
if __name__=="__main__":unittest.main()
