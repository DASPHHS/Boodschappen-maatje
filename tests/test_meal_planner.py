import sys, unittest
sys.path.insert(0,"src")
from meal_planner import plan_one_store
class TestMealPlanner(unittest.TestCase):
    def test_stays_at_single_store(self):
        offers=[
          {"store":"Jumbo","text":"Kipfilet 500 g","price":4.5,"valid_from":"2026-10-20","valid_until":"2026-10-27"},
          {"store":"Jumbo","text":"Volkoren wraps 6 stuks","price":1.8,"valid_from":"2026-10-20","valid_until":"2026-10-27"},
          {"store":"Lidl","text":"Paprika mix","price":1.0,"valid_from":"2026-10-20","valid_until":"2026-10-27"}]
        plans=plan_one_store(offers,"2026-10-23")
        p=next(x for x in plans if x["name"]=="Harissa-kipwraps" and x["store"]=="Jumbo")
        self.assertEqual({m["ingredient"] for m in p["matches"]},{"kipfilet","wrap"})
        self.assertIn("paprika",p["missing"])
        self.assertIsNone(p["total_price"])
    def test_expired_excluded(self):
        p=plan_one_store([{"store":"Jumbo","text":"Kipfilet","price":3.5,"valid_until":"2026-10-01"}],"2026-10-23")
        self.assertEqual(p,[])
if __name__=="__main__":unittest.main()
