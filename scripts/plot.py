#!/usr/bin/env python3
# impl: FR-004-04
"""Скатер «позиція в блоці проти CU price» по лідерах (SVG, тільки stdlib).

Використання: python3 scripts/plot.py data-mainnet [--out docs/plots/position-vs-fee.svg]
"""

import csv
import json
import math
import sys
from pathlib import Path

COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
          "#8c564b", "#e377c2", "#7f7f7f"]


def load_points(data_dir: Path):
    """(leader, cu_price, position) по кожній landed tx."""
    sent = {}
    with (data_dir / "sent.csv").open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            sent[row["signature"]] = row
    leaders = {}
    lp = data_dir / "leaders.json"
    if lp.is_file():
        leaders = json.loads(lp.read_text(encoding="utf-8")).get("slots", {})
    pts = []
    with (data_dir / "landed.csv").open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("status", "landed") != "landed":
                continue
            s = sent.get(row["signature"], {})
            try:
                price = int(s.get("cu_price_lamports", 0))
            except ValueError:
                price = 0
            pts.append((leaders.get(str(row["slot"]), "?")[:8],
                        price, int(row["position"])))
    return pts


def render_svg(points: list, title: str = "position vs CU price") -> str:
    """Логарифмічна вісь X (fee), лінійна Y (позиція)."""
    W, H, M = 760, 480, 60
    leaders = sorted({p[0] for p in points})
    color = {name: COLORS[i % len(COLORS)] for i, name in enumerate(leaders)}
    max_pos = max((p[2] for p in points), default=1)
    xs = [math.log10(p[1] + 1) for p in points]
    xmax = max(xs, default=1.0)

    def sx(x):
        return M + (W - 2 * M) * x / (xmax or 1.0)

    def sy(y):
        return H - M - (H - 2 * M) * y / (max_pos or 1)

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">',
           f"<title>{title}</title>",
           f'<text x="{W // 2}" y="24" text-anchor="middle" font-size="15">{title}</text>',
           f'<text x="{W // 2}" y="{H - 8}" text-anchor="middle" font-size="12">'
           f"CU price (micro-lamports, log10(x+1))</text>",
           f'<text x="14" y="{H // 2}" text-anchor="middle" font-size="12" '
           f'transform="rotate(-90 14,{H // 2})">position in block</text>']
    for p in points:
        out.append(
            f'<circle cx="{sx(math.log10(p[1] + 1)):.1f}" cy="{sy(p[2]):.1f}" '
            f'r="4" fill="{color[p[0]]}" fill-opacity="0.7">'
            f"<title>{p[0]} fee={p[1]} pos={p[2]}</title></circle>")
    lx = M
    for i, name in enumerate(leaders):
        out.append(
            f'<rect x="{lx}" y="{H - 42}" width="10" height="10" fill="{color[name]}"/>'
            f'<text x="{lx + 13}" y="{H - 34}" font-size="11">{name}</text>')
        lx += 13 + 8 * len(name)
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    args = [a for a in argv if not a.startswith("-")]
    if not args:
        print("використання: python3 scripts/plot.py data/ [--out file.svg]",
              file=sys.stderr)
        return 2
    out_path = None
    for i, a in enumerate(argv):
        if a == "--out" and i + 1 < len(argv):
            out_path = Path(argv[i + 1])
    pts = load_points(Path(args[0]))
    if not pts:
        print("plot: немає точок", file=sys.stderr)
        return 1
    svg = render_svg(pts)
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(svg, encoding="utf-8")
        print(f"plot: {len(pts)} точок -> {out_path}")
    else:
        print(svg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
