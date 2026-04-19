"""
Generates heatmaps for Markov transition matrices and the J(α, δ) calibration grid.

Titles are NOT drawn on the figures themselves — the caption is provided in
the consuming publication. Label language is controlled through the `labels`
dict from `i18n.py`.
"""

from __future__ import annotations
import os
from typing import Dict, Sequence
import numpy as np
import matplotlib.pyplot as plt

from i18n import get_labels, scenario_label, levels_short


def plot_markov_heatmap(P: np.ndarray, labels: dict,
                        output_path: str, dpi: int = 160) -> None:
    """Heatmap of a 5×5 transition matrix."""
    fig, ax = plt.subplots(figsize=(6.2, 5.4), dpi=dpi)
    im = ax.imshow(P, cmap="Blues", vmin=0.0, vmax=1.0, aspect="equal")

    level_labels = levels_short(labels)
    ax.set_xticks(range(5)); ax.set_yticks(range(5))
    ax.set_xticklabels(level_labels, fontsize=9)
    ax.set_yticklabels(level_labels, fontsize=9)
    ax.set_xlabel(labels["ax_to_level"], fontsize=10)
    ax.set_ylabel(labels["ax_from_level"], fontsize=10)

    for i in range(5):
        for j in range(5):
            val = P[i, j]
            txt = "0" if val < 0.001 else f"{val:.3f}"
            color = "white" if val > 0.5 else "#222"
            ax.text(j, i, txt, ha="center", va="center",
                    fontsize=8.5, color=color)

    cbar = plt.colorbar(im, ax=ax, fraction=0.045, pad=0.04)
    cbar.set_label(labels["ax_transition_prob"], fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_calibration_heatmap(grid: np.ndarray, alpha_range: Sequence[float],
                              delta_range: Sequence[float], labels: dict,
                              output_path: str, dpi: int = 160) -> None:
    fig, ax = plt.subplots(figsize=(7.5, 5.5), dpi=dpi)
    im = ax.imshow(grid, cmap="viridis", aspect="auto", origin="lower")

    ax.set_xticks(range(len(delta_range)))
    ax.set_yticks(range(len(alpha_range)))
    ax.set_xticklabels([f"{d:.3f}" for d in delta_range],
                       fontsize=8, rotation=45, ha="right")
    ax.set_yticklabels([f"{a:.2f}" for a in alpha_range], fontsize=8)
    ax.set_xlabel(labels["ax_delta"], fontsize=10)
    ax.set_ylabel(labels["ax_alpha"], fontsize=10)

    max_idx = np.unravel_index(np.argmax(grid), grid.shape)
    ax.plot(max_idx[1], max_idx[0], marker="*", markersize=16,
            color="white", markeredgecolor="red", markeredgewidth=1.2)

    cbar = plt.colorbar(im, ax=ax, fraction=0.045, pad=0.04)
    cbar.set_label("J(α, δ)", fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def generate_all(cv_results: Dict, calib_grid: np.ndarray,
                 alpha_range: Sequence[float], delta_range: Sequence[float],
                 output_dir: str, lang: str = "uk") -> Dict[str, str]:
    labels = get_labels(lang)
    os.makedirs(output_dir, exist_ok=True)
    paths = {}

    for scenario_name, cv in cv_results.items():
        P = np.array(cv["transition_matrix"])
        fname = f"heatmap_{scenario_name}.png"
        fpath = os.path.join(output_dir, fname)
        plot_markov_heatmap(P, labels, fpath)
        paths[f"heatmap_{scenario_name}"] = fpath

    calib_path = os.path.join(output_dir, "heatmap_calibration.png")
    plot_calibration_heatmap(np.array(calib_grid), alpha_range, delta_range,
                              labels, calib_path)
    paths["heatmap_calibration"] = calib_path

    return paths


if __name__ == "__main__":
    rng = np.random.default_rng(42)
    P_demo = np.eye(5) * 0.94 + np.diag([0.04] * 4, 1) + np.diag([0.005] * 4, -1)
    P_demo /= P_demo.sum(axis=1, keepdims=True)
    plot_markov_heatmap(P_demo, get_labels("uk"), "/tmp/heatmap_demo.png")
    print("Demo heatmap: /tmp/heatmap_demo.png")
