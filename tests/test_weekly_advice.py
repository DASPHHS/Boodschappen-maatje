"""Regressie tegen misleidende lege mand en oude/ontbrekende winkelprijzen."""
import json,tempfile,unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from weekly_advice import calculate,report_from_receptenradar

class WekelijksAdviesTests(unittest.TestCase):
    def test_leeg_is_niet_nul_euro_koopadvies(self):
        report=calculate([],[],["Jumbo","Albert Heijn","Lidl"],150)
        self.assertEqual(report["status"],"basket_not_configured")
        self.assertIsNone(report["recommended"])
        self.assertTrue(all(x["total_eur"] is None for x in report["stores"]))

    def write(self,data):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"data.json"
            p.write_text(json.dumps(data))
            return report_from_receptenradar(p,150)

    def test_identiek_weekmenu_gebruikt_zonder_verzonnen_picnic_prijzen(self):
        d={"updated_at":datetime.now(timezone.utc).isoformat(),
           "weekmenu_advice":{"status":"indicative_online_comparison",
             "recipe_count":3,"portion_count":12,
             "stores":{"ah":{"checkout":50.01},"jumbo":{"checkout":47.0},
                       "lidl":{"checkout":35.0}},
             "meals":[{"title":"Kip met groente"}]}}
        out=self.write(d)
        self.assertEqual(out["status"],"indicative_recipe_comparison")
        self.assertEqual(out["recommended"]["store"],"Lidl")
        self.assertEqual(out["recipe_count"],3)
        self.assertEqual(out["portion_count"],12)
        self.assertIsNone(out["stores"][-1]["total_eur"])
        self.assertEqual(out["stores"][-1]["store"],"Picnic")

    def test_oud_of_onvolledig_levert_nooit_verouderd_koopadvies(self):
        d={"updated_at":(datetime.now(timezone.utc)-timedelta(days=5)).isoformat(),
           "weekmenu_advice":{"status":"indicative_online_comparison",
             "recipe_count":3,"portion_count":12,
             "stores":{"ah":{"checkout":3},"jumbo":{"checkout":4},"lidl":{"checkout":5}}}}
        out=self.write(d)
        self.assertEqual(out["status"],"stale_recipe_prices")
        self.assertIsNone(out["recommended"])
        d["updated_at"]=datetime.now(timezone.utc).isoformat()
        d["weekmenu_advice"]={"status":"no_common"}
        self.assertEqual(self.write(d)["status"],"no_common_weekmenu")

if __name__=="__main__":unittest.main()
