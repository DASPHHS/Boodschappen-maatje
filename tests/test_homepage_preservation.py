import sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,'src')
import koopkracht
class HomepageRegression(unittest.TestCase):
 def test_scanner_preserves_platform_home(self):
  with tempfile.TemporaryDirectory() as temp:
   docs=Path(temp)/'docs';docs.mkdir();data=Path(temp)/'data';home=docs/'index.html';home.write_text('platform homepage')
   with patch.object(koopkracht,'DOCS',docs),patch.object(koopkracht,'DATA',data):
    koopkracht.render({'folders':[],'offers':[]})
   self.assertEqual(home.read_text(),'platform homepage')
   self.assertTrue((docs/'aanbiedingen.html').exists())
