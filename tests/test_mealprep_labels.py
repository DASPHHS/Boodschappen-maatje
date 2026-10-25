"""Voorkom onterechte 'mealprep' claims uitsluitend op basis van kookduur."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from receptenradar_v2 import mealprep_suitable

class MealprepLabelTests(unittest.TestCase):
    def test_lange_kooktijd_is_geen_mealprep_bewijs(self):
        self.assertFalse(mealprep_suitable("Gebakken zalm met sla","Avondeten","Vis"))
        self.assertFalse(mealprep_suitable("Verse tonijnsalade met komkommer","Avondeten","Vis"))
        self.assertFalse(mealprep_suitable("Kipsalade met rauwkost","Avondeten","Kip"))
        self.assertFalse(mealprep_suitable("Vis uit de oven","Avondeten","Vis"))
        self.assertFalse(mealprep_suitable("Omelet met tomaten","Avondeten","Vegetarisch"))

    def test_robuuste_gekookte_maaltijdbases_mealprep(self):
        for title,cat in [
           ("Linzencurry met spinazie","Vegetarisch"),
           ("Mealprep: pittige gehaktstoof","Vlees"),
           ("Ovenschotel met kip","Kip"),
           ("Vegetarische chili","Vegetarisch"),
           ("Surinaamse nasi met kip","Kip"),
           ("Italiaans geïnspireerde boerenkoolpasta met kipgehakt","Kip")]:
            with self.subTest(title=title):
                if "boerenkoolpasta" in title:
                    self.assertFalse(mealprep_suitable(title,"Avondeten",cat))
                else:
                    self.assertTrue(mealprep_suitable(title,"Avondeten",cat))

    def test_ontbijt_en_lunch_alleen_relevante_varianten(self):
        self.assertTrue(mealprep_suitable("Ontbijt: overnight oats met kwark","Ontbijt"))
        self.assertFalse(mealprep_suitable("Ontbijt: yoghurt met vers fruit","Ontbijt"))
        self.assertTrue(mealprep_suitable("Lunch: kruidige linzensoep","Lunch"))
        self.assertFalse(mealprep_suitable("Lunch: sandwich met garnalen","Lunch"))

if __name__=="__main__":unittest.main()
