import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from portie_flexibiliteit import needed_quantity

class FlexTests(unittest.TestCase):
    def test_750_instead_of_800(self):
        self.assertEqual(needed_quantity("shoarma",800,"g",750),750)
        self.assertEqual(needed_quantity("kipfilet",800,"g",750),750)
    def test_large_shortage_not_accepted(self):
        self.assertEqual(needed_quantity("kipfilet",800,"g",600),800)
    def test_no_shortage_in_staples_or_fixed_units(self):
        self.assertEqual(needed_quantity("rijst",800,"g",750),800)
        self.assertEqual(needed_quantity("eieren",8,"st",6),8)
    def test_vegetables_tolerance(self):
        self.assertEqual(needed_quantity("broccoli",800,"g",750),750)
    def test_no_one_pack_reduction_too_large(self):
        self.assertEqual(needed_quantity("kipfilet",800,"g",300),800)

if __name__=="__main__":unittest.main()
