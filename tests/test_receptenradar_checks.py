"""Controleer dat onjuiste winkelmanden de dagelijkse publicatie blokkeren."""
import unittest,sys
from copy import deepcopy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from receptenradar_checks import validate_publication


def sample():
    line={"cash_price":2.50,"used_price":2.00,"sale":False,"action":None}
    return {"ah":[{
        "id":"1","title":"Groenterecept","ingredients":[line],"missing":[],
        "covered_count":1,"ingredient_count":1,"complete":True,
        "known_subtotal":2.50,"checkout":2.50,"per_serving":0.50,
        "sale_count":0,
        "deal_basket":{"ingredients":[dict(line)],"used_actions":0,
                       "known_subtotal":2.50,"checkout":2.50}
    }]}


class PublicationTests(unittest.TestCase):
    def test_geldige_publicatie(self):
        self.assertEqual(validate_publication(sample()),1)

    def test_verkeerd_totaal_afwijzen(self):
        data=sample()
        data["ah"][0]["checkout"]=1.50
        with self.assertRaisesRegex(ValueError,"afrekenbedrag"):
            validate_publication(data)

    def test_misleidend_actieaantal_afwijzen(self):
        data=sample()
        data["ah"][0]["sale_count"]=1
        with self.assertRaisesRegex(ValueError,"acties"):
            validate_publication(data)

    def test_onvolledige_mand_mag_nooit_volledige_prijs_tonen(self):
        data=sample()
        recipe=data["ah"][0]
        recipe["missing"]=[{"label":"broccoli","amount":500,"unit":"g"}]
        recipe["ingredient_count"]=2
        recipe["complete"]=False
        recipe["checkout"]=None
        recipe["per_serving"]=None
        recipe["deal_basket"]["checkout"]=None
        self.assertEqual(validate_publication(data),1)
        recipe["checkout"]=2.50
        with self.assertRaises(ValueError):
            validate_publication(data)


if __name__=="__main__":
    unittest.main()
