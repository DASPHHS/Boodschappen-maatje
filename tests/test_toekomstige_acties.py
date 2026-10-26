"""Acties voor morgen onderscheiden van acties die vandaag kassageldig zijn."""
import sys,unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from receptenradar_v2 import load_deals

def deal(name,start,end,status="upcoming",price=1.19):
    return {"id":name,"retailer":"albert_heijn","name":name,
            "quantity":"500 g","price":price,"original_price":1.99,
            "promotion_status":status,"valid_from":start,"valid_until":end,
            "url":"https://www.ah.nl/bonus"}

class FakeResponse:
    def __init__(self,rows):self.rows=rows
    def json(self):return {"results":self.rows,"total":len(self.rows)}

class AanbiedingenVooruitTests(unittest.TestCase):
    @patch("receptenradar_v2.fetch")
    def test_tomorrow_alleen_vooruit_niet_meegeprijsd_vandaag(self,fetch):
        fetch.side_effect=lambda url,params:FakeResponse([
            deal("Broccoli vandaag","2026-10-26","2026-10-28","active"),
            deal("Broccoli morgen","2026-10-29","2026-11-01","upcoming"),
            deal("Spruiten volgend weekend","2026-10-31","2026-11-02","active"),
            deal("Gepasseerde actie","2026-10-20","2026-10-27","historical"),
            deal("Pas over 8 dagen","2026-11-05","2026-11-12","upcoming"),
            deal("Voorbij","2026-10-20","2026-10-21","active"),
        ] if params["retailer"]=="albert_heijn" else [])
        today,errors,future=load_deals(include_upcoming=True,as_of=date(2026,10,28))
        self.assertEqual([p["name"] for p in today["ah"]],["Broccoli vandaag"])
        self.assertEqual([p["name"] for p in future["ah"]],
                         ["Broccoli morgen","Spruiten volgend weekend"])
        self.assertEqual(len(today["jumbo"]),0)
        self.assertEqual(errors,[])
        self.assertEqual(future["ah"][0]["valid_from"],"2026-10-29")
        self.assertTrue(future["ah"][0]["valid_until"])

    @patch("receptenradar_v2.fetch")
    def test_nieuwe_actieweek_vanaf_maandag_ondanks_verouderde_upcoming_status(self,fetch):
        fetch.side_effect=lambda url,params:FakeResponse([
            deal("AH Bonus vanaf maandag","2026-10-26","2026-11-01","upcoming"),
            deal("Zaterdag pas geldig","2026-10-31","2026-11-01","upcoming"),
            deal("Zonder einddatum","2026-10-26","","upcoming"),
            deal("Verlopen vrijdag","2026-10-19","2026-10-25","active"),
        ] if params["retailer"]=="albert_heijn" else [])
        active,errors,future=load_deals(include_upcoming=True,as_of=date(2026,10,26))
        self.assertEqual(errors,[])
        self.assertEqual([p["name"] for p in active["ah"]],["AH Bonus vanaf maandag"])
        self.assertEqual([p["name"] for p in future["ah"]],["Zaterdag pas geldig"])
        self.assertEqual(active["ah"][0]["valid_from"],"2026-10-26")
        self.assertEqual(active["ah"][0]["valid_until"],"2026-11-01")

    @patch("receptenradar_v2.fetch")
    def test_bestaand_contract_en_onbevestigde_startdatum(self,fetch):
        fetch.side_effect=lambda url,params:FakeResponse([
            deal("Onbekende startdatum","","2026-11-01","upcoming"),
            deal("Ingang morgen","2026-10-29","2026-11-01","active")
        ] if params["retailer"]=="albert_heijn" else [])
        now,errors=load_deals(as_of=date(2026,10,28))
        self.assertEqual(now["ah"],[])
        now,errors,future=load_deals(include_upcoming=True,as_of=date(2026,10,28))
        self.assertEqual(len(future["ah"]),1)
        self.assertEqual(future["ah"][0]["name"],"Ingang morgen")

if __name__=="__main__":unittest.main()
