import sys, unittest
sys.path.insert(0,"src")
from koopkracht import folder_identity, parse_amount, safe_url, normalise_name
class TestKoopkracht(unittest.TestCase):
    def test_folder_identity(self):
        self.assertEqual(folder_identity("https://www.allefolders.nl/jumbo-aanbiedingen/abc/0"), "jumbo-aanbiedingen/abc")
    def test_amount(self):
        self.assertEqual(parse_amount("€ 2,49"),2.49)
        self.assertIsNone(parse_amount("geen prijs"))
    def test_urls(self):
        self.assertTrue(safe_url("https://www.allefolders.nl/winkels"))
        self.assertFalse(safe_url("http://127.0.0.1/private"))
    def test_names(self):
        self.assertEqual(normalise_name("  Coca   Cola!  "), "coca cola")
if __name__=="__main__":unittest.main()
