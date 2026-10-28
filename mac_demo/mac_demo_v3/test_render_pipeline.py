import tempfile
import unittest
import xml.dom.minidom
from pathlib import Path

from PIL import Image

from render_pipeline import LABELS, build_grid, render_gif, render_markdown, render_svg


class TestBuildGrid(unittest.TestCase):
    def test_load_use_stall_appears_before_mac_ex(self):
        sched, cells, first, last = build_grid(2)
        mac_row = 2
        self.assertEqual(cells[(mac_row, 3)], "IF")
        self.assertEqual(cells[(mac_row, 4)], "ID")
        self.assertEqual(cells[(mac_row, 5)], "stall")
        self.assertEqual(cells[(mac_row, 6)], "EX")

    def test_last_writeback_matches_simulated_cycles(self):
        from pipeline_model import loop_trace, mac_loop_body, simulate

        _, _, _, last = build_grid(2)
        self.assertEqual(last, simulate(loop_trace(mac_loop_body, 2)))

    def test_row_count_matches_instruction_count(self):
        sched, _, _, _ = build_grid(2)
        self.assertEqual(len(sched), 2 * len(LABELS))


class TestMarkdown(unittest.TestCase):
    def test_header_and_rows(self):
        md = render_markdown(2)
        lines = md.splitlines()
        self.assertTrue(lines[0].startswith("| 指令 | C"))
        table_rows = [l for l in lines if l.startswith("| `")]
        self.assertEqual(len(table_rows), 2 * len(LABELS))

    def test_total_cycles_reported(self):
        self.assertIn("**22**", render_markdown(2))


class TestSvg(unittest.TestCase):
    def test_is_well_formed_xml(self):
        doc = xml.dom.minidom.parseString(render_svg(2))
        self.assertEqual(doc.documentElement.tagName, "svg")

    def test_contains_every_label(self):
        svg = render_svg(2)
        for label in LABELS:
            self.assertIn(label.replace("<", "&lt;"), svg)


class TestGif(unittest.TestCase):
    def test_one_frame_per_cycle(self):
        sched, _, first, last = build_grid(2)
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "p.gif"
            render_gif(out, 2)
            with Image.open(out) as im:
                self.assertEqual(im.n_frames, last - first + 1)


if __name__ == "__main__":
    unittest.main()
