import unittest
from scan_kwaliteitscontrole import inspect_snapshot

class ScanQualityTests(unittest.TestCase):
    def test_empty_feed_is_not_successful_coverage(self):
        result=inspect_snapshot({"ah":[],"jumbo":[],"lidl":[]},{"ah":[],"jumbo":[],"lidl":[]})
        self.assertEqual(result["stores"]["lidl"]["coverage_status"],"attention")
        self.assertFalse(result["all_sources_complete"])
        self.assertGreaterEqual(len(result["warnings"]),3)

    def test_unrealistic_positive_count_does_not_claim_completeness(self):
        p=[{"price":1.2}]*1200
        a=[{"price":1,"valid_from":"2026-10-26","valid_until":"2026-11-01"}]*101
        data=inspect_snapshot({s:p for s in ("ah","jumbo","lidl")},
                              {s:a for s in ("ah","jumbo","lidl")})
        self.assertEqual(data["stores"]["ah"]["coverage_status"],"plausible_not_complete")
        self.assertFalse(data["all_sources_complete"])

    def test_broken_price_flagged(self):
        p=[{"price":float("nan")}]*1200
        a=[{"price":1,"valid_from":"2026-10-26","valid_until":"2026-11-01"}]*101
        data=inspect_snapshot({s:p for s in ("ah","jumbo","lidl")},
                              {s:a for s in ("ah","jumbo","lidl")})
        self.assertEqual(data["stores"]["jumbo"]["invalid_shelf_prices"],1200)
if __name__=="__main__":unittest.main()
