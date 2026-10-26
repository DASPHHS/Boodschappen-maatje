"""Tests voor het halfuurlijkse alternatievenoverzicht zonder externe netwerkcalls."""
import sys
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from receptalternatieven import (
    FOCUS, generate, matching_focus, priced_suggestions,
    source_suggestions, rotating_sources
)

NOW = datetime(2026,10,26,13,0,tzinfo=timezone.utc)

class AlternativeTests(unittest.TestCase):
    def test_tuna_matches_dutch_and_english(self):
        self.assertIn("tonijn", matching_focus("Tonijnkikkererwtensalade met komkommer")
                      if False else matching_focus("Tonijn-bonensalade"))
        self.assertIn("tonijn", matching_focus("Healthy tuna wraps"))
        self.assertNotIn("tonijn", matching_focus("Salade met kip en tomaat"))

    def test_price_only_from_complete_cash_basket(self):
        prices={"updated_at":"2026-10-26T12:00:00+01:00","recipes":{
          "ah":[{
            "id":"t1","title":"Tonijnwraps met bonen","complete":True,"checkout":8.65,
            "per_serving":1.80,"sale_count":1,"nutrition":{"priority":True},
            "ingredients":[{"key":"tonijn","label":"tonijn"}],"minutes":20
          },{
            "id":"t2","title":"Tonijnsalade","complete":False,"checkout":None,
            "known_subtotal":4.50,"missing":[{"key":"sla"}],
            "ingredients":[{"key":"tonijn","label":"tonijn"}],
            "nutrition":{},"sale_count":0
          }],"jumbo":[],"lidl":[]
        }}
        results=priced_suggestions(prices)
        self.assertEqual(len(results),2)
        self.assertEqual(results[0]["checkout"],8.65)
        self.assertIsNone(results[1]["checkout"])
        self.assertEqual(results[1]["missing_count"],1)
        self.assertEqual(results[1]["status"],"niet volledig geprijsd")
        report=generate(prices,{"items":[]},{},[],[],NOW)
        self.assertEqual(report["focus_counts"]["tonijn"]["priced"],1)
        self.assertEqual(report["focus_counts"]["tonijn"]["unpriced"],1)

    def test_sources_dedupe_and_never_invent_price(self):
        src={"items":[
          {"title":"Tuna Salad","source":"Wikibooks","url":"https://en.wikibooks.org/wiki/Cookbook:Tuna_Salad"},
          {"title":"Tuna Salad","source":"Wikibooks","url":"https://en.wikibooks.org/wiki/Cookbook:Tuna_Salad"},
          {"title":"Tonijn met komkommer","source":"AH","url":"http://wrong.example/not-secure"},
          {"title":"Kip met rijst","source":"Jumbo","url":"https://www.jumbo.com/recepten/kip-rijst"}
        ]}
        found=source_suggestions(src,[],{},NOW)
        self.assertEqual(len(found),2)
        self.assertIn("tonijn",found[0]["focus"])
        self.assertNotIn("checkout",found[0])
        self.assertIn("prijs niet gecontroleerd",found[0]["status"])

    def test_expired_old_ideas_disappear(self):
        stale={"inspiration":[{
          "title":"Tuna Salad","source":"Bron","url":"https://example.com/tuna",
          "seen_at":(NOW-timedelta(days=30)).date().isoformat()
        }]}
        self.assertEqual(source_suggestions({"items":[]},[],stale,NOW),[])

    @patch("receptalternatieven.robots_allowed",return_value=False)
    def test_respects_robots_and_limits_requests(self, mocked):
        class NeverRequest:
            def get(self,*a,**kw):raise AssertionError("Netwerk verboden bij robotsblokkade")
        links,status=rotating_sources(NOW,session=NeverRequest(),max_sources=2)
        self.assertEqual(links,[])
        self.assertEqual(len(status),2)
        self.assertTrue(all(x["state"].startswith("robots") for x in status))

if __name__=="__main__":
    unittest.main()
