"""No-network tests for Netherlands HelloFresh public link metadata indexing."""
import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import refresh_hellofresh_recipes as hf

class HelloFreshTests(unittest.TestCase):
    def test_exact_url_allowlist(self):
        good="https://www.hellofresh.nl/recipes/nasi-goreng-met-roerei-633eee0477adddd743098bd6"
        self.assertEqual(hf.canonical(good),good)
        self.assertEqual(hf.canonical(good+"?locale=nl-nl"),good)
        self.assertIsNone(hf.canonical("http://www.hellofresh.nl/recipes/x-633eee0477adddd743098bd6"))
        self.assertIsNone(hf.canonical("https://www.hellofresh.nl.evil.example/recipes/"+good.split("/")[-1]))
        self.assertIsNone(hf.canonical("https://www.hellofresh.nl/recipes/market/hachee-633eee0477adddd743098bd6"))
        self.assertIsNone(hf.canonical("https://www.hellofresh.nl/recipes/indonesische-recepten"))
        self.assertIsNone(hf.canonical("https://www.hellofresh.nl/recipes/not-a-real-id"))
    def test_metadata_from_actual_page(self):
        good="https://www.hellofresh.nl/recipes/nasi-goreng-met-roerei-633eee0477adddd743098bd6"
        html='<html><head><meta name="description" content="Nasi goreng met eieren, paprika en tomaten."></head><body><h1>Nasi goreng met roerei en paprika</h1><h2>Instructies</h2><p>Copyrighted recipe must never be copied</p><img src="recipe.jpg"></body></html>'
        r=hf.record_from_page(good,html,"2026-11-01")
        self.assertEqual(r["source"],"HelloFresh")
        self.assertIn("paprika",r["families"])
        self.assertIn("eieren",r["families"])
        self.assertEqual(r["review_status"],"publisher_page_title_verified")
        self.assertNotIn("instructions",r)
        self.assertNotIn("recipeIngredient",r)
        self.assertNotIn("image",r)
        self.assertNotIn("Copyrighted recipe",str(r))
    def test_bounded_network_and_failure_keeps_index(self):
        link="https://www.hellofresh.nl/recipes/nasi-goreng-met-roerei-633eee0477adddd743098bd6"
        listing=f'<a href="{link}">Nasi goreng met roerei</a>'
        page="<html><h1>Nasi goreng met roerei en paprika</h1></html>"
        sources={"https://www.hellofresh.nl/robots.txt":"User-agent: *\nAllow: /recipes/",
                 **{hf.BASE+p:listing for p in hf.CATEGORIES},link:page}
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/"publisher-recipes.json"
            target.write_text(json.dumps({"recipes":[],"generated_at":"2026-10-30"}),encoding="utf8")
            def fake_fetch(url,cap=999999):
                if url not in sources:raise AssertionError("Unexpected url: "+url)
                return sources[url]
            with patch.object(hf,"TARGET",target):
                self.assertEqual(hf.discover(max_pages=1,fetcher=fake_fetch,day=dt.date(2026,11,1),pause=0),1)
                saved=json.loads(target.read_text())
                self.assertEqual(len(saved["recipes"]),1)
                self.assertEqual(hf.discover(max_pages=1,fetcher=fake_fetch,day=dt.date(2026,11,1),pause=0),0)
                self.assertEqual(len(json.loads(target.read_text())["recipes"]),1)
                before=target.read_text()
                with patch.object(hf,"allowed_robots",side_effect=OSError("blocked")):
                    self.assertEqual(hf.discover(max_pages=1,fetcher=fake_fetch,pause=0),0)
                self.assertEqual(before,target.read_text())
    def test_robots_disallow(self):
        link="https://www.hellofresh.nl/recipes/nasi-goreng-met-roerei-633eee0477adddd743098bd6"
        calls=[]
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/"index.json"
            target.write_text(json.dumps({"recipes":[]}),encoding="utf8")
            def fake_fetch(url,cap=999999):
                calls.append(url)
                return "User-agent: *\nDisallow: /recipes"
            with patch.object(hf,"TARGET",target):
                self.assertEqual(hf.discover(fetcher=fake_fetch,pause=0),0)
            self.assertEqual(calls,["https://www.hellofresh.nl/robots.txt"])

if __name__=="__main__":
    unittest.main()
