import unittest

from pipeline_model import compare_mac_latency, loop_trace, mac_loop_body, simulate


class TestMacLatency(unittest.TestCase):
    def test_default_latency_one_matches_original(self):
        self.assertEqual(simulate(loop_trace(mac_loop_body, 10)),
                         simulate(loop_trace(mac_loop_body, 10, mac_lat=1)))

    def test_longer_mac_adds_cycles(self):
        base = simulate(loop_trace(mac_loop_body, 100, mac_lat=1))
        slow = simulate(loop_trace(mac_loop_body, 100, mac_lat=3))
        self.assertGreater(slow, base)

    def test_compare_mac_latency_table(self):
        rows = compare_mac_latency(n=100, mac_lats=(1, 2, 3))
        self.assertEqual([r["mac_lat"] for r in rows], [1, 2, 3])
        self.assertLess(rows[0]["mac_cycles"], rows[2]["mac_cycles"])
        self.assertEqual(rows[0]["std_cycles"], rows[2]["std_cycles"])


if __name__ == "__main__":
    unittest.main()
