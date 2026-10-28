import unittest

from pipeline_model import Ins, _alu, compare, ex_schedule, loop_trace, mac_loop_body, simulate


class TestPipelineModel(unittest.TestCase):
    def test_independent_alu_fills_pipeline(self):
        trace = [_alu(f"r{i}", "x") for i in range(10)]
        self.assertEqual(simulate(trace), 10 + 4)

    def test_dependent_alu_no_stall_with_forwarding(self):
        trace = [_alu("a", "x"), _alu("b", "a"), _alu("c", "b")]
        self.assertEqual(simulate(trace), 3 + 4)

    def test_load_use_stalls_one_cycle(self):
        load_use = [Ins("lw", "t", ("x",), ready_delay=2), _alu("u", "t")]
        independent = [Ins("lw", "t", ("x",), ready_delay=2), _alu("u", "y")]
        self.assertEqual(simulate(load_use) - simulate(independent), 1)

    def test_taken_branch_flushes_two(self):
        base = [_alu("a", "x"), Ins("b", None, ("a",), taken=False), _alu("c", "x")]
        taken = [_alu("a", "x"), Ins("b", None, ("a",), taken=True), _alu("c", "x")]
        self.assertEqual(simulate(taken) - simulate(base), 2)

    def test_schedule_matches_simulate(self):
        trace = loop_trace(mac_loop_body, 3)
        last_ex = ex_schedule(trace)[-1][1]
        self.assertEqual(last_ex + 2, simulate(trace))

    def test_mac_faster_than_standard_loop(self):
        for n in (1, 10, 1000):
            std, mac = compare(n, mul_lat=1)
            self.assertLess(mac, std)

    def test_mul_latency_increases_standard_cycles(self):
        std1, _ = compare(100, mul_lat=1)
        std3, mac3 = compare(100, mul_lat=3)
        self.assertGreater(std3, std1)
        self.assertLess(mac3, std3)


if __name__ == "__main__":
    unittest.main()
