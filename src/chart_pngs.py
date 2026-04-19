"""
Matplotlib versions of the five main charts (for embedding into MD/DOCX).

Titles are NOT drawn on the figures themselves — the caption is provided in
the consuming publication. Label language is controlled through the `labels`
dict from `i18n.py`.
"""

from __future__ import annotations
import os
from typing import Dict
import numpy as np
import matplotlib.pyplot as plt

from i18n import get_labels, scenario_label


COMPONENT_LABELS = {
    "C":  r"$DM_C$",
    "L1": r"$DM_{L_1}$",
    "L2": r"$DM_{L_2}$",
    "L3": r"$DM_{L_3}$",
    "L4": r"$DM_{L_4}$",
    "I":  r"$DM_I$",
    "S":  r"$DM_S$",
}

SCENARIO_COLORS = {
    "baseline":       "#999999",
    "uniform":        "#1f77b4",
    "S2_core":        "#2ca02c",
    "S3_integration": "#ff7f0e",
    "S4_market":      "#d62728",
}


def plot_trajectories(scenarios: Dict, output_path: str, labels: dict,
                      dpi: int = 160) -> None:
    fig, ax = plt.subplots(figsize=(9, 5.4), dpi=dpi)
    for s, data in scenarios.items():
        years = list(range(len(data["admi_mean"])))
        color = SCENARIO_COLORS.get(s, None)
        ax.plot(years, data["admi_mean"], marker="o", markersize=5,
                linewidth=2.0, color=color,
                label=scenario_label(s, labels))
    ax.set_xlabel(labels["ax_year"], fontsize=11)
    ax.set_ylabel(labels["ax_admi"], fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=9, framealpha=0.9)
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_profiles_radar(scenarios: Dict, output_path: str, labels: dict,
                        year_index: int = -1, dpi: int = 160) -> None:
    components = ["C", "L1", "L2", "L3", "L4", "I", "S"]
    n = len(components)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 7), dpi=dpi,
                            subplot_kw={"projection": "polar"})
    for s, data in scenarios.items():
        dm_comp = data.get("dm_components_mean", {})
        if not dm_comp:
            continue
        vals = [dm_comp[k][year_index] for k in components]
        vals += vals[:1]
        color = SCENARIO_COLORS.get(s, None)
        ax.plot(angles, vals, marker="o", markersize=4, linewidth=1.6,
                color=color, label=scenario_label(s, labels))
        ax.fill(angles, vals, alpha=0.08, color=color)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([COMPONENT_LABELS[k] for k in components], fontsize=11)
    ax.set_rlim(0, 1.0)
    ax.set_rticks([0.2, 0.4, 0.6, 0.8])
    ax.set_rlabel_position(90)
    ax.grid(True, alpha=0.4)
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.05), fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_multihorizon_bar(mh_results: Dict, output_path: str, labels: dict,
                           dpi: int = 160) -> None:
    scenarios_by_horizon = mh_results["scenarios_by_horizon"]
    scenarios = list(scenarios_by_horizon[5].keys())
    horizons = sorted(scenarios_by_horizon.keys())

    changes = {
        h: [
            scenarios_by_horizon[h][s]["admi_mean"][-1]
            - scenarios_by_horizon[h][s]["admi_mean"][0]
            for s in scenarios
        ]
        for h in horizons
    }

    x = np.arange(len(scenarios))
    width = 0.26

    fig, ax = plt.subplots(figsize=(9.5, 5.8), dpi=dpi)
    h_colors = {5: "#1f77b4", 10: "#2ca02c", 15: "#d62728"}
    for i, h in enumerate(horizons):
        offset = (i - (len(horizons) - 1) / 2) * width
        bars = ax.bar(x + offset, changes[h], width,
                      label=labels["legend_horizon_years"].format(h=h),
                      color=h_colors.get(h))
        for b, v in zip(bars, changes[h]):
            ax.text(b.get_x() + b.get_width() / 2, v + (0.003 if v > 0 else -0.005),
                    f"{v:+.2f}", ha="center",
                    va="bottom" if v > 0 else "top", fontsize=8)

    ax.axhline(0, color="#666", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([scenario_label(s, labels) for s in scenarios],
                       rotation=15, ha="right", fontsize=10)
    ax.set_ylabel(labels["ax_delta_admi"], fontsize=11)
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(loc="best", fontsize=10)

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_crossvalidation_bar(cv_results: Dict, output_path: str, labels: dict,
                              scenario: str = "uniform",
                              dpi: int = 160) -> None:
    cv = cv_results.get(scenario) or list(cv_results.values())[0]
    sd = cv["empirical_distribution_year5"]
    mk = cv["markov_predicted_year5"]

    level_prefix = labels["level_prefix"]
    level_labels = [f"{level_prefix} {i + 1}" for i in range(5)]
    x = np.arange(5)
    width = 0.35

    fig, ax = plt.subplots(figsize=(8.5, 5.2), dpi=dpi)
    b1 = ax.bar(x - width / 2, sd, width,
                label=labels["legend_sd_empirical"], color="#1f77b4")
    b2 = ax.bar(x + width / 2, mk, width,
                label=labels["legend_markov_predicted"], color="#ff7f0e")

    for b, v in list(zip(b1, sd)) + list(zip(b2, mk)):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.005,
                f"{v * 100:.1f}%", ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(level_labels, fontsize=10)
    ax.set_ylabel(labels["ax_enterprise_share"], fontsize=11)
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(loc="upper right", fontsize=10)
    ax.set_ylim(0, max(max(sd), max(mk)) * 1.2 + 0.02)

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_sensitivity_tornado(sensitivity: Dict, output_path: str, labels: dict,
                              dpi: int = 160) -> None:
    sorted_params = sorted(sensitivity.items(),
                            key=lambda x: x[1]["sensitivity"], reverse=True)
    params = [p for p, _ in sorted_params]
    vals = [d["sensitivity"] for _, d in sorted_params]

    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=dpi)
    y = np.arange(len(params))
    bars = ax.barh(y, vals, color="#2a7f7f", edgecolor="#1a4d4d")

    for b, v in zip(bars, vals):
        ax.text(v + max(vals) * 0.01, b.get_y() + b.get_height() / 2,
                f"{v:.4f}", va="center", fontsize=9)

    ax.set_yticks(y)
    ax.set_yticklabels(params, fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel(labels["ax_sensitivity"], fontsize=11)
    ax.grid(True, axis="x", alpha=0.3)
    ax.set_xlim(0, max(vals) * 1.18)

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def generate_all(report: Dict, output_dir: str, lang: str = "uk") -> Dict[str, str]:
    """Generates all 5 PNG charts. Label language is controlled via `lang`."""
    labels = get_labels(lang)
    os.makedirs(output_dir, exist_ok=True)
    paths = {}

    tr_path = os.path.join(output_dir, "trajectories_admi.png")
    plot_trajectories(report["scenarios"], tr_path, labels)
    paths["trajectories"] = tr_path

    pr_path = os.path.join(output_dir, "profiles_radar.png")
    plot_profiles_radar(report["scenarios"], pr_path, labels)
    paths["profiles"] = pr_path

    if report.get("multi_horizon"):
        mh_path = os.path.join(output_dir, "multi_horizon_bar.png")
        plot_multihorizon_bar(report["multi_horizon"], mh_path, labels)
        paths["multi_horizon"] = mh_path

    cv_path = os.path.join(output_dir, "cross_validation_bar.png")
    plot_crossvalidation_bar(report["cross_validation"], cv_path, labels)
    paths["cross_validation"] = cv_path

    sn_path = os.path.join(output_dir, "sensitivity_tornado.png")
    plot_sensitivity_tornado(report["sensitivity"], sn_path, labels)
    paths["sensitivity"] = sn_path

    return paths


if __name__ == "__main__":
    import json
    import sys
    if len(sys.argv) < 3:
        print("Usage: python3 chart_pngs.py <report.json> <output_dir> [lang]")
        sys.exit(1)
    with open(sys.argv[1], encoding="utf-8") as f:
        report = json.load(f)
    lang = sys.argv[3] if len(sys.argv) > 3 else "uk"
    paths = generate_all(report, sys.argv[2], lang=lang)
    for k, v in paths.items():
        print(f"  {k}: {v}")
