"""Regressietests voor veilige, gedifferentieerde wereldkeukenindex."""
import sys, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from wereldkeuken_bronnen import (WORLD_SOURCES,parse_links,collect_world_links,robots_allowed)

class BronnenTests(unittest.TestCase):
    def test_breedte_en_surinaamse_bronnen(self):
        cuisines={c for _,c,_ in WORLD_SOURCES}
        self.assertGreaterEqual(len(cuisines),15)
        for name in ("Surinaams","Koreaans","Indiaas","Marokkaans","Italiaans"):
            self.assertIn(name,cuisines)
        self.assertGreaterEqual(len([x for x in WORLD_SOURCES if x[1]=="Surinaams"]),7)

    def test_alleen_bronreceptlinks_en_geen_tekst(self):
        html=('<h2><a href="/allerhande/recept/R-12345/kip-met-groenten">Kip met groenten</a></h2>'
              '<h3><a href="https://evil.example/recept/iets">Onbetrouwbare verwijzing</a></h3>'
              '<a href="/allerhande/recepten/indiaas">Een receptencollectie</a>'
              '<a href="/allerhande/recept/R-12345/kip-met-groenten">Kip met groenten</a>')
        found=parse_links(html,"https://www.ah.nl/allerhande/recepten/indiase-recepten","Allerhande","Indiaas")
        self.assertEqual(len(found),1)
        self.assertEqual(found[0]["title"],"Kip met groenten")
        self.assertEqual(found[0]["cuisine"],"Indiaas")
        self.assertEqual(found[0]["price_status"],"Niet doorgerekend")
        self.assertNotIn("instructions",found[0])
        self.assertNotIn("image",found[0])

    def test_geen_urlmet_http(self):
        found=parse_links('<h2><a href="http://www.ah.nl/allerhande/recept/R-123">Recept voorbeeld</a></h2>',
                          "https://www.ah.nl/allerhande/recepten/surinaamse-recepten","AH","Surinaams")
        self.assertEqual(found,[])

    @patch("wereldkeuken_bronnen.requests.get")
    def test_robots_onbekend_wordt_niet_gegokt(self,get):
        from requests import Timeout
        get.side_effect=Timeout()
        robots_allowed.cache_clear()
        self.assertFalse(robots_allowed("https://sranangkukru.net/test/"))

    @patch("wereldkeuken_bronnen.robots_allowed",return_value=False)
    def test_blokkade_geeft_controle_status_geen_gevonden_recepten(self,robots):
        recipes,status=collect_world_links(max_sources=1)
        self.assertEqual(recipes,[])
        self.assertEqual(status[0]["count"],0)
        self.assertIn("robots",status[0]["status"])

if __name__=="__main__":
    unittest.main()
