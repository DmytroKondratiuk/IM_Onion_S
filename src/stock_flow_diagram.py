"""
Generates the Stock-and-Flow diagram of IM Onion-S (Fig. 2.3.1).

Title is NOT drawn on the figure — caption is supplied by the publication.
Labels are localised through `i18n.py` (uk / en).

Outputs:
  - stock_flow.dot — Graphviz source (import into draw.io: File → Import)
  - stock_flow.png — matplotlib render
"""

from __future__ import annotations
import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Ellipse

from i18n import get_labels


STOCK_KEYS = ["C", "L1", "L2", "L3", "L4", "I", "S"]
DEPRECIATION = {
    "C": 0.015, "L1": 0.020, "L2": 0.025, "L3": 0.030,
    "L4": 0.025, "I": 0.020, "S": 0.010,
}


def write_dot(output_path: str, labels: dict) -> None:
    """Writes a Graphviz .dot source (imports cleanly into draw.io)."""
    stock_label = labels["sf_legend_stock"]
    inflow_label = labels["sf_legend_inflow"]
    outflow_label = labels["sf_legend_outflow"]
    lines = [
        'digraph Onion_S_SD_Model {',
        '    rankdir=LR;',
        '    graph [fontname="Arial", fontsize=11, splines=curved, nodesep=0.5];',
        '    node  [fontname="Arial", fontsize=10];',
        '    edge  [fontname="Arial", fontsize=9];',
        '',
        f'    // {inflow_label}',
        '    subgraph cluster_inflows {',
        f'        label="{inflow_label}"; style=dashed; color=gray;',
        '        node [shape=diamond, style=filled, fillcolor="#d4f1d4"];',
    ]
    for key in STOCK_KEYS:
        lines.append(f'        EI_{key} [label="EI_{key}"];')
    lines.append('    }')
    lines.append('')
    lines.append(f'    // {stock_label}')
    lines.append('    subgraph cluster_stocks {')
    lines.append(f'        label="{stock_label}"; style=dashed; color=gray;')
    lines.append('        node [shape=box, style=filled, fillcolor="#fff4c2"];')
    for key in STOCK_KEYS:
        label = labels[f"sf_stock_{key}"].replace("\n", "\\n")
        lines.append(f'        {key} [label="{label}"];')
    lines.append('    }')
    lines.append('')
    lines.append(f'    // {outflow_label}')
    lines.append('    subgraph cluster_outflows {')
    lines.append(f'        label="{outflow_label}"; style=dashed; color=gray;')
    lines.append('        node [shape=diamond, style=filled, fillcolor="#fadadd"];')
    for key in STOCK_KEYS:
        lines.append(f'        D_{key} [label="D_{key}\\nd={DEPRECIATION[key]:.3f}"];')
    lines.append('    }')
    lines.append('')
    lines.append(f'    // {labels["sf_legend_modifier"]}')
    lines.append('    node [shape=ellipse, style=filled, fillcolor="#e6e0f8"];')
    for mod_key in ["F", "A", "Phi", "G", "E"]:
        lab = labels[f"sf_modif_{mod_key}"].replace("\n", "\\n")
        lines.append(f'    {mod_key}   [label="{lab}"];')
    lines.append('')
    lines.append('    // Flows into / out of stocks')
    for key in STOCK_KEYS:
        lines.append(f'    EI_{key} -> {key};')
        lines.append(f'    {key}   -> D_{key};')
    lines.append('')
    lines.append('    // Modifier influences')
    for key in ["C", "L1", "L2", "L3"]:
        lines.append(f'    {key} -> F [style=dotted, color=gray];')
    for key in ["L1", "L2", "L3", "L4"]:
        lines.append(f'    F -> EI_{key} [color="#8c1aff"];')
    lines.append('    L1 -> A [style=dotted, color=gray];')
    for key in STOCK_KEYS:
        lines.append(f'    A -> EI_{key} [color="#8c1aff"];')
    lines.append('    I -> Phi [style=dotted, color=gray];')
    for key in STOCK_KEYS:
        lines.append(f'    Phi -> EI_{key} [color="#8c1aff"];')
    for key in STOCK_KEYS:
        lines.append(f'    {key} -> G [style=dotted, color=gray];')
        lines.append(f'    G -> EI_{key} [color="#8c1aff"];')
    lines.append('    E -> EI_L4 [color=red, penwidth=1.5];')
    lines.append('')
    lines.append('    // Feedback-loop legend note')
    loops = (f'{labels["sf_loops_title"]}\\n'
             f'{labels["sf_loop_R1"]}\\n'
             f'{labels["sf_loop_B1"]}\\n'
             f'{labels["sf_loop_B2"]}\\n'
             f'{labels["sf_loop_B3"]}')
    lines.append(f'    loops [shape=note, label="{loops}"];')
    lines.append('}')
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def render_png(output_path: str, labels: dict, dpi: int = 160) -> None:
    """matplotlib render of the diagram (no overlaid title)."""
    fig, ax = plt.subplots(figsize=(14, 8.5), dpi=dpi)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis("off")

    c_stock    = "#fff4c2"
    c_inflow   = "#d4f1d4"
    c_outflow  = "#fadadd"
    c_modifier = "#e6e0f8"
    c_text     = "#1a1a1a"

    stock_positions = {
        "C":  (7.0, 5.0),
        "L1": (7.0, 6.5),
        "L2": (7.0, 8.0),
        "L3": (7.0, 3.5),
        "L4": (7.0, 2.0),
        "I":  (10.0, 5.0),
        "S":  (4.0, 5.0),
    }

    def add_box(x, y, w, h, label, color, fontsize=8.5):
        box = FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                             boxstyle="round,pad=0.05",
                             facecolor=color, edgecolor="#222", linewidth=1.0)
        ax.add_patch(box)
        ax.text(x, y, label, ha="center", va="center", fontsize=fontsize,
                color=c_text)

    def add_diamond(x, y, w, h, label, color, fontsize=8):
        pts = [(x, y + h / 2), (x + w / 2, y), (x, y - h / 2), (x - w / 2, y)]
        poly = plt.Polygon(pts, facecolor=color, edgecolor="#222", linewidth=1.0)
        ax.add_patch(poly)
        ax.text(x, y, label, ha="center", va="center", fontsize=fontsize,
                color=c_text)

    def add_ellipse(x, y, w, h, label, color, fontsize=8):
        e = Ellipse((x, y), width=w, height=h,
                    facecolor=color, edgecolor="#222", linewidth=1.0)
        ax.add_patch(e)
        ax.text(x, y, label, ha="center", va="center", fontsize=fontsize,
                color=c_text)

    def add_arrow(x0, y0, x1, y1, color="#333", lw=1.0, style="-|>", mutation=12):
        arr = FancyArrowPatch((x0, y0), (x1, y1),
                              arrowstyle=style, mutation_scale=mutation,
                              color=color, linewidth=lw)
        ax.add_patch(arr)

    inflow_positions = {k: (xy[0] - 2.0, xy[1]) for k, xy in stock_positions.items()}
    outflow_positions = {k: (xy[0] + 2.0, xy[1]) for k, xy in stock_positions.items()}
    inflow_positions["I"]  = (10.0, 6.8); outflow_positions["I"] = (10.0, 3.2)
    inflow_positions["S"]  = (4.0, 6.8);  outflow_positions["S"] = (4.0, 3.2)

    for key, (x, y) in stock_positions.items():
        add_box(x, y, 1.6, 0.9, labels[f"sf_stock_{key}"], c_stock, fontsize=8)

    for key in stock_positions:
        ix, iy = inflow_positions[key]
        add_diamond(ix, iy, 0.7, 0.5, f"EI_{key}", c_inflow, fontsize=7)
        ox, oy = outflow_positions[key]
        add_diamond(ox, oy, 0.7, 0.5, f"D_{key}", c_outflow, fontsize=7)
        sx, sy = stock_positions[key]
        if key in ("I", "S"):
            add_arrow(ix, iy - 0.25, sx, sy + 0.45, color="#2a7f2a", lw=1.1)
            add_arrow(sx, sy - 0.45, ox, oy + 0.25, color="#a32828", lw=1.1)
        else:
            add_arrow(ix + 0.35, iy, sx - 0.8, sy, color="#2a7f2a", lw=1.1)
            add_arrow(sx + 0.8, sy, ox - 0.35, oy, color="#a32828", lw=1.1)

    mod_positions = {
        "F":   (12.5, 8.2),
        "A":   (12.5, 6.8),
        "Phi": (12.5, 5.0),
        "G":   (12.5, 3.2),
        "E":   (12.5, 1.5),
    }
    for k, (x, y) in mod_positions.items():
        add_ellipse(x, y, 1.5, 0.75, labels[f"sf_modif_{k}"], c_modifier,
                    fontsize=7.5)

    legend_text = (
        f"{labels['sf_loops_title']}\n"
        f"{labels['sf_loop_R1']}\n"
        f"{labels['sf_loop_B1']}\n"
        f"{labels['sf_loop_B2']}\n"
        f"{labels['sf_loop_B3']}"
    )
    ax.text(0.3, 0.3, legend_text, fontsize=8, va="bottom", ha="left",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#f5f5f5",
                      edgecolor="#999", linewidth=0.8))

    patches = [
        mpatches.Patch(facecolor=c_stock,    edgecolor="#222", label=labels["sf_legend_stock"]),
        mpatches.Patch(facecolor=c_inflow,   edgecolor="#222", label=labels["sf_legend_inflow"]),
        mpatches.Patch(facecolor=c_outflow,  edgecolor="#222", label=labels["sf_legend_outflow"]),
        mpatches.Patch(facecolor=c_modifier, edgecolor="#222", label=labels["sf_legend_modifier"]),
    ]
    ax.legend(handles=patches, loc="upper right", fontsize=8, frameon=True)

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def generate(output_dir: str, lang: str = "uk") -> dict:
    """Generates both .dot and .png. Returns {dot: path, png: path}."""
    labels = get_labels(lang)
    os.makedirs(output_dir, exist_ok=True)
    dot_path = os.path.join(output_dir, "stock_flow.dot")
    png_path = os.path.join(output_dir, "stock_flow.png")
    write_dot(dot_path, labels)
    render_png(png_path, labels)
    return {"dot": dot_path, "png": png_path}


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "./figures"
    lang = sys.argv[2] if len(sys.argv) > 2 else "uk"
    paths = generate(out, lang=lang)
    print(f"Stock-and-Flow ({lang}):")
    for k, v in paths.items():
        print(f"  {k}: {v}")
