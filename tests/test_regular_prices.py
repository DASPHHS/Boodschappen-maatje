import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import sync_regular_prices as p

MILK = {
    "store": "ah", "name": "AH Verse volle melk 1 L", "group": "volle_melk",
    "price": 1.39, "quantity": 1000, "unit": "ml", "checked_date": "2026-10-28",
    "status": "official_regular_observed",
    "url": "https://www.ah.nl/producten/product/wi1524/volle-melk"
}
SEREH = {
    "store": "ah", "name": "AH Verse sereh / citroengras 1 stuk", "group": "sereh",
    "price": 0.79, "checked_date": "2026-10-28",
    "status": "official_regular_observed",
    "url": "https://www.ah.nl/producten/product/wi387232/ah-sereh"
}
HTML_MILK = '''<html><h1>AH Volle melk</h1>
<script type="application/ld+json">{"@type":"Product","name":"AH Volle melk",
"offers":{"@type":"Offer","price":"1.39","priceCurrency":"EUR"}}</script></html>'''
HTML_SEREH = '''<html><h1>AH Sereh</h1><p>per stuk</p>
<div>Uit het assortiment</div><span>Kies alternatief</span></html>'''

class RegularPricesTest(unittest.TestCase):
    def test_direct_exact_product_pages_only(self):
        self.assertTrue(p.direct_url(MILK))
        self.assertFalse(p.direct_url({**MILK, "url": "https://www.ah.nl/allerhande/recepten"}))
        self.assertFalse(p.direct_url({**MILK, "url": "https://www.ah.nl.attacker.example/producten/product/wi1524"}))
        self.assertFalse(p.direct_url({**MILK, "url": "http://www.ah.nl/producten/product/wi1524"}))

    def test_title_and_precise_price(self):
        self.assertEqual(p.observed(HTML_MILK, MILK)["price"], 1.39)
        self.assertIsNone(p.observed(HTML_MILK, {**MILK, "name": "AH Magere kwark 1 L"}))
        self.assertIsNone(p.observed('<html><h1>AH Volle melk</h1><p>Voor 1.39</p></html>', MILK))
        self.assertIsNone(p.observed('''<h1>AH Volle melk</h1>
<script type="application/ld+json">[{"@type":"Offer","price":"1.39"},
{"@type":"Offer","price":"2.79"}]</script>''', MILK))

    def test_ah_litre_price_with_known_exact_size(self):
        html = '<html><h1>AH Volle melk</h1><span>1 l · Prijs per LT € 1,39</span></html>'
        self.assertTrue(p.title_match(MILK["name"], "AH Volle melk"))
        self.assertEqual(p.observed(html, MILK)["price"], 1.39)
        self.assertIsNone(p.observed(html, {**MILK, "unit": "stuk"}))
        self.assertIsNone(p.observed(html, {**MILK, "quantity": None}))

    def test_external_seed_is_upgraded_only_after_exact_page_proof(self):
        seeded = {**MILK, "status": "external_regular_observed",
                  "price": 1.19, "checked_date": "2026-10-27"}
        doc = {"products": [seeded]}
        p.refresh(doc, "2026-10-29", lambda url: HTML_MILK)
        row = doc["products"][0]
        self.assertEqual(row["status"], "official_regular_observed")
        self.assertEqual(row["price"], 1.39)
        self.assertEqual(row["price_history"][0]["price"], 1.19)
        self.assertEqual(row["price_history"][-1]["price"], 1.39)
        self.assertEqual(row["source_verification"], "retailer_product_page_checked")

    def test_unavailable_not_bought(self):
        self.assertEqual(p.observed(HTML_SEREH, SEREH)["availability_status"], "discontinued")

    def test_updater_keeps_older_price_on_failed_source(self):
        doc = {"products": [copy.deepcopy(MILK), copy.deepcopy(SEREH)]}
        def fetch(url):
            return None if "wi1524" in url else HTML_SEREH
        checked, updated = p.refresh(doc, "2026-10-29", fetch)
        self.assertEqual(checked, 2)
        self.assertEqual(updated, 1)
        self.assertEqual(doc["products"][0]["checked_date"], "2026-10-28")
        self.assertEqual(doc["products"][1]["checked_date"], "2026-10-28")
        self.assertEqual(doc["products"][1]["availability_status"], "discontinued")

    def test_successful_refresh_only_exact(self):
        doc = {"products": [copy.deepcopy(MILK)]}
        checked, updated = p.refresh(doc, "2026-10-29", lambda url: HTML_MILK)
        self.assertEqual((checked, updated), (1,1))
        self.assertEqual(doc["products"][0]["checked_date"], "2026-10-29")
        self.assertEqual(doc["products"][0]["price"], 1.39)

if __name__ == "__main__":
    unittest.main()
