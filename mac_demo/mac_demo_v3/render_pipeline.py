"""Render the MAC loop's 5-stage pipeline timing (first iterations) as Markdown and SVG.

Stage timing comes from pipeline_model.ex_schedule, so the figure matches the cycle counts.
IF is one cell before the stalled decode block; ID covers the decode stall window.
"""

from pathlib import Path
from xml.sax.saxutils import escape

from pipeline_model import TAIL, ex_schedule, loop_trace, mac_loop_body, simulate

LABELS = ["lw t0, 0(a0)", "lw t1, 0(a1)", "mac t3, t0, t1",
          "addi a0, a0, 4", "addi a1, a1, 4", "addi a2, a2, -1", "bnez a2, loop"]
ITERATIONS = 2
COLORS = {"IF": "#9ecae1", "ID": "#a1d99b", "EX": "#fdae6b", "MEM": "#bdbdbd",
          "WB": "#bcbddc", "stall": "#f7f7f7", "": "#ffffff"}


def build_grid(n_iter: int = ITERATIONS):
    trace = loop_trace(mac_loop_body, n_iter)
    sched = ex_schedule(trace)
    cells = {}  # (row, cycle) -> label
    last = 0
    for row, (ins, t, stall, _flush) in enumerate(sched):
        lat = ins.lat
        cells[(row, t - 2 - stall)] = "IF"
        for c in range(t - 1 - stall, t):
            cells[(row, c)] = "ID" if c == t - 1 - stall else "stall"
        for c in range(t, t + lat):
            cells[(row, c)] = "EX"
        cells[(row, t + lat)] = "MEM"
        cells[(row, t + lat + 1)] = "WB"
        last = max(last, t + lat + 1)
    first = min(c for (_, c) in cells)
    return sched, cells, first, last


def render_markdown(n_iter: int = ITERATIONS) -> str:
    sched, cells, first, last = build_grid(n_iter)
    cycles = list(range(first, last + 1))
    header = "| 指令 | " + " | ".join(f"C{c}" for c in cycles) + " |"
    sep = "|---|" + "|".join([":-:"] * len(cycles)) + "|"
    rows = [header, sep]
    for row, (ins, *_rest) in enumerate(sched):
        label = LABELS[row % len(LABELS)]
        vals = [cells.get((row, c), "") for c in cycles]
        rows.append(f"| `{label}` | " + " | ".join(v for v in vals) + " |")
    total = simulate(loop_trace(mac_loop_body, n_iter))
    notes = [
        "",
        f"模型總週期(含 {n_iter} 次迭代):**{total}**,最後一拍為 WB = C{last}。",
        "stall:load-use 停頓(`lw t1` 之後的 `mac` 等待 1 拍)。",
        "累加鏈 `mac t3` → 下一個 `mac t3` 透過 forwarding 不停頓。",
        "`bnez` 跳回後,下一條有效指令的 EX 延後 3 拍(flush 2 拍的錯誤路徑未畫出)。",
    ]
    return "\n".join(rows + notes) + "\n"


def render_svg(n_iter: int = ITERATIONS) -> str:
    sched, cells, first, last = build_grid(n_iter)
    cycles = list(range(first, last + 1))
    cw, ch, lw, top = 62, 30, 170, 40
    width = lw + cw * len(cycles) + 20
    height = top + ch * len(sched) + 60
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
             f'font-family="monospace" font-size="13">']
    parts.append('<rect width="100%" height="100%" fill="#ffffff"/>')
    for i, c in enumerate(cycles):
        x = lw + i * cw
        parts.append(f'<text x="{x + cw / 2}" y="{top - 12}" text-anchor="middle">C{c}</text>')
    for row, (ins, *_r) in enumerate(sched):
        y = top + row * ch
        label = LABELS[row % len(LABELS)]
        parts.append(f'<text x="8" y="{y + ch / 2 + 5}">{escape(label)}</text>')
        for i, c in enumerate(cycles):
            x = lw + i * cw
            lab = cells.get((row, c), "")
            color = COLORS["stall" if lab == "stall" else lab if lab in COLORS else ""]
            parts.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" fill="{color}" '
                         f'stroke="#999"/>')
            if lab:
                txt = "" if lab == "stall" else lab
                parts.append(f'<text x="{x + cw / 2}" y="{y + ch / 2 + 5}" '
                             f'text-anchor="middle">{txt}</text>')
    legend_y = top + ch * len(sched) + 25
    lx = lw
    for stage in ("IF", "ID", "EX", "MEM", "WB", "stall"):
        parts.append(f'<rect x="{lx}" y="{legend_y - 12}" width="14" height="14" '
                     f'fill="{COLORS[stage]}" stroke="#999"/>')
        parts.append(f'<text x="{lx + 20}" y="{legend_y}">{stage}</text>')
        lx += 90
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def _font(size: int):
    from PIL import ImageFont

    for path in ("/System/Library/Fonts/Menlo.ttc", "/System/Library/Fonts/Supplemental/Courier New.ttf"):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_gif(path: Path, n_iter: int = ITERATIONS, frame_ms: int = 700) -> None:
    from PIL import Image, ImageDraw

    sched, cells, first, last = build_grid(n_iter)
    cycles = list(range(first, last + 1))
    cw, ch, lw, top = 62, 30, 170, 50
    width = lw + cw * len(cycles) + 20
    height = top + ch * len(sched) + 60
    font, small = _font(13), _font(11)

    frames, durations = [], []
    for now in cycles:
        img = Image.new("RGB", (width, height), "white")
        d = ImageDraw.Draw(img)
        d.text((8, 12), f"5-stage pipeline: MAC loop, cycle C{now}", fill="black", font=font)
        for i, c in enumerate(cycles):
            x = lw + i * cw
            d.text((x + cw / 2 - 12, top - 20), f"C{c}", fill="black", font=small)
        for row in range(len(sched)):
            y = top + row * ch
            d.text((8, y + ch / 2 - 6), LABELS[row % len(LABELS)], fill="black", font=small)
            for i, c in enumerate(cycles):
                x = lw + i * cw
                lab = cells.get((row, c), "")
                shown = lab if c <= now else ""
                fill = COLORS["stall" if lab == "stall" else lab if lab in COLORS else ""]
                if c > now:
                    fill = "#ffffff"
                d.rectangle([x, y, x + cw, y + ch], fill=fill, outline="#999999")
                if shown:
                    d.text((x + cw / 2 - 16 if shown == "stall" else x + cw / 2 - 12, y + ch / 2 - 6), shown, fill="#d62728" if shown == "stall" else "black", font=small)
        cx = lw + cycles.index(now) * cw
        d.rectangle([cx, top - 2, cx + cw, top + ch * len(sched) + 2], outline="#d62728", width=3)
        ly = top + ch * len(sched) + 22
        lx = lw
        for stage in ("IF", "ID", "EX", "MEM", "WB", "stall"):
            d.rectangle([lx, ly, lx + 14, ly + 14], fill=COLORS[stage], outline="#999999")
            d.text((lx + 20, ly), stage, fill="black", font=small)
            lx += 90
        frames.append(img)
        durations.append(frame_ms * 2 if now == last else frame_ms)

    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durations, loop=0)


def main():
    here = Path(__file__).resolve().parent
    (here / "pipeline_mac.md").write_text(render_markdown())
    (here / "pipeline_mac.svg").write_text(render_svg())
    render_gif(here / "pipeline_mac.gif")
    print("wrote pipeline_mac.md, pipeline_mac.svg, pipeline_mac.gif")


if __name__ == "__main__":
    main()
