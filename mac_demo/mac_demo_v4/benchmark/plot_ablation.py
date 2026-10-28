"""Plot the ablation results: configuration ladder and factor sensitivity."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from benchmark.ablation import ablation_rows  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "figures"
FONT = ["Heiti TC", "Arial Unicode MS", "DejaVu Sans"]


def draw(path_stem: Path = OUT / "ablation") -> list:
    plt.rcParams["font.sans-serif"] = FONT
    plt.rcParams["axes.unicode_minus"] = False
    rows = ablation_rows()
    ladder = [r for r in rows if r["id"] in ("A0", "A1", "A2", "A3")]
    full = next(r for r in rows if r["id"] == "A4")
    factors = [
        ("移除封包(標量 mac)", next(r for r in rows if r["id"] == "B1")["pipe"], full["pipe"]),
        ("MAC 延遲 2 拍", next(r for r in rows if r["id"] == "A5")["pipe"], full["pipe"]),
        ("週期時間比 1.2", next(r for r in rows if r["id"] == "A6")["pipe"], full["pipe"]),
    ]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.2), gridspec_kw={"width_ratios": [1.3, 1]})

    labels = ["A0 base(v1)", "A1 +展開4(v2)", "A2 +封包mac2(v3)", "A3 +編譯器基準"]
    vals = [r["instr"] for r in ladder]
    bars = ax1.bar(labels, vals, color=["#9ecae1", "#6baed6", "#3182bd", "#08519c"])
    for b, v in zip(bars, vals):
        ax1.text(b.get_x() + b.get_width() / 2, v + 0.03, f"{v:.2f}x", ha="center", fontsize=11)
    ax1.axhline(1.0, color="gray", linestyle="--", linewidth=1)
    ax1.set_ylabel("指令層級加速比(越高越好)")
    ax1.set_title("(a) 配置階梯:各策略疊加後的加速", fontsize=13)
    ax1.set_ylim(0, 2.4)
    ax1.tick_params(axis="x", labelsize=9)

    names = ["完整配置 A4\n(封包 mac2,延遲 1)"] + [f[0] for f in factors]
    pipe_vals = [full["pipe"]] + [f[1] for f in factors]
    colors = ["#31a354"] + ["#e6550d", "#fd8d3c", "#fdae6b"]
    ybar = range(len(names))
    bars2 = ax2.barh(list(ybar), pipe_vals, color=colors)
    for b, v in zip(bars2, pipe_vals):
        ax2.text(v + 0.01, b.get_y() + b.get_height() / 2, f"{v:.2f}x", va="center", fontsize=11)
    ax2.set_yticks(list(ybar))
    ax2.set_yticklabels(names, fontsize=10)
    ax2.invert_yaxis()
    ax2.axvline(1.0, color="gray", linestyle="--", linewidth=1)
    ax2.set_xlabel("管線週期加速比")
    ax2.set_xlim(0, 1.6)
    ax2.set_title("(b) 因素敏感度:管線層級", fontsize=13)

    fig.suptitle("MAC 策略消融實驗(模型估計,非實測)", fontsize=14)
    fig.tight_layout()
    OUT.mkdir(exist_ok=True)
    written = []
    for ext in ("png", "svg"):
        p = path_stem.with_suffix(f".{ext}")
        fig.savefig(p, dpi=150)
        written.append(p)
    plt.close(fig)
    return written


if __name__ == "__main__":
    for p in draw():
        print("wrote", p)
