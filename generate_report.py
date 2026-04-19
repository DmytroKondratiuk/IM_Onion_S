"""
Main entry point: full IM Onion-S simulation cycle.

Usage:
    python3 generate_report.py                   # interactive language prompt
    python3 generate_report.py --lang uk         # skip the prompt
    python3 generate_report.py --lang en --quick --export-pngs
    python3 generate_report.py --no-multi        # skip 10/15-year horizons
    python3 generate_report.py --help

Outputs (default paths are relative to the repo root):
    results/simulation_report.json          — raw data
    results/onion_s_simulation.xlsx         — xlsx with tables and charts
    figures/stock_flow.png, stock_flow.dot  — Stock-and-Flow diagram
    figures/heatmap_*.png (with --export-pngs) — Markov heatmaps + J(α,δ)
    figures/*.png                           — 5 main charts (with --export-pngs)

Installing dependencies:
    pip3 install -r requirements.txt
"""

from __future__ import annotations
import argparse
import json
import os
import sys
import time
from datetime import datetime

import numpy as np

# Make `src/` importable so all modules are available
_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC  = os.path.join(_HERE, "src")
sys.path.insert(0, _SRC)

from onion_s_simulation import (  # noqa: E402
    CONFIG, generate_enterprises, precompute_trajectory_quality,
    run_single_calibration, run_scenario_analysis, cross_validate,
    sensitivity_analysis,
)
import export_to_xlsx as xlsx_exporter  # noqa: E402
import stock_flow_diagram  # noqa: E402
import heatmap_generator  # noqa: E402
import chart_pngs  # noqa: E402
from i18n import get_labels, prompt_language  # noqa: E402


# ────────────────────────────────────────────────────────

DEFAULT_SEEDS = {
    "calibration_base": 42,
    "calibration_mult": 137,
    "scenario":         12345,
    "crossval":         54321,
    "multihorizon_base": 2024,
}


def derive_seeds(master_seed=None) -> dict:
    """
    Builds the seed bundle for the whole pipeline.

    master_seed=None -> DEFAULT_SEEDS (deterministic baseline, dissertation data).
    master_seed=N    -> all seeds derived from N (reproducible within N, but
                        different between different N values).
    """
    if master_seed is None:
        return dict(DEFAULT_SEEDS)
    rng = np.random.default_rng(int(master_seed))
    ints = [int(x) for x in rng.integers(0, 2**31 - 1, size=4)]
    return {
        "calibration_base":  ints[0],
        "calibration_mult":  137,  # keep the spacing between per-run seeds
        "scenario":          ints[1],
        "crossval":          ints[2],
        "multihorizon_base": ints[3],
    }


def run_full_pipeline(L: dict, quick: bool = False,
                       run_multihorizon: bool = True,
                       seeds: dict = None) -> dict:
    if seeds is None:
        seeds = DEFAULT_SEEDS
    if quick:
        CONFIG["n_enterprises"] = 200
        CONFIG["n_runs"] = 3
        print(f"  {L['quick_mode']}")

    start_time = time.time()
    print("=" * 72)
    print(f"  {L['pipeline_title']}")
    print("=" * 72)

    print(f"\n{L['step_1_calibration']} ({CONFIG['n_runs']} × "
          f"{CONFIG['n_enterprises']})...")
    all_runs = []
    for run_id in range(CONFIG["n_runs"]):
        seed = seeds["calibration_base"] + run_id * seeds["calibration_mult"]
        result = run_single_calibration(run_id, seed)
        all_runs.append(result)
        print(f"    Run {run_id + 1}/{CONFIG['n_runs']}: "
              f"α={result['best_alpha']:.3f}, δ={result['best_delta']:.3f}, "
              f"J={result['best_score']:.4f}")

    all_alphas = [r["best_alpha"] for r in all_runs]
    all_deltas = [r["best_delta"] for r in all_runs]
    mean_alpha = float(np.mean(all_alphas))
    std_alpha = float(np.std(all_alphas))
    mean_delta = float(np.mean(all_deltas))
    std_delta = float(np.std(all_deltas))
    final_alpha = float(CONFIG["alpha_range"][np.argmin(np.abs(CONFIG["alpha_range"] - mean_alpha))])
    final_delta = float(CONFIG["delta_range"][np.argmin(np.abs(CONFIG["delta_range"] - mean_delta))])
    print(f"    {L['final_alpha_delta'].format(a=final_alpha, d=final_delta)}")

    avg_grid = np.mean([np.array(r["grid_scores"]) for r in all_runs], axis=0)

    print(f"\n{L['step_2_scenarios']} (5 × {CONFIG['n_years']})...")
    rng_scenario = np.random.default_rng(seeds["scenario"])
    scenario_enterprises = generate_enterprises(CONFIG["n_enterprises"], rng_scenario)
    scenario_results = run_scenario_analysis(scenario_enterprises, final_alpha,
                                              final_delta, rng_scenario)
    for name, data in scenario_results.items():
        ch = data["admi_mean"][-1] - data["admi_mean"][0]
        print(f"    {name:20s}: ΔADMI = {ch:+.3f}")

    print(f"\n{L['step_3_crossval']}...")
    rng_cv = np.random.default_rng(seeds["crossval"])
    cv_enterprises = generate_enterprises(CONFIG["n_enterprises"], rng_cv)
    cv_traj_quality = precompute_trajectory_quality(cv_enterprises, rng_cv)
    cv_results = {}
    for scenario_name in ["uniform", "S2_core", "S3_integration"]:
        cv = cross_validate(cv_enterprises, final_alpha, final_delta,
                            scenario_name, rng_cv)
        cv_results[scenario_name] = cv
        print(f"    {scenario_name:18s}: L1 = {cv['l1_deviation_predicted']:.4f}")

    print(f"\n{L['step_4_sensitivity']}...")
    sensitivity = sensitivity_analysis(cv_enterprises, final_alpha, final_delta,
                                        rng_cv, cv_traj_quality)
    for param, data in sorted(sensitivity.items(),
                               key=lambda x: x[1]["sensitivity"], reverse=True):
        print(f"    {param:30s}: {data['sensitivity']:.4f}")

    multi_horizon_data = None
    if run_multihorizon:
        print(f"\n{L['step_5_multihorizon']}...")
        multi_horizon_data = run_multihorizon_analysis(
            final_alpha, final_delta, L, seeds["multihorizon_base"])
    else:
        print(f"\n{L['step_5_skipped']}")

    elapsed = time.time() - start_time
    print(f"\n  {L['cycle_done'].format(t=elapsed)}")

    report = {
        "calibration": {
            "final_alpha": final_alpha, "final_delta": final_delta,
            "mean_alpha": mean_alpha, "std_alpha": std_alpha,
            "median_alpha": float(np.median(all_alphas)),
            "mean_delta": mean_delta, "std_delta": std_delta,
            "median_delta": float(np.median(all_deltas)),
            "all_alphas": all_alphas, "all_deltas": all_deltas,
            "individual_runs": [
                {"run_id": r["run_id"], "best_alpha": r["best_alpha"],
                 "best_delta": r["best_delta"], "best_score": r["best_score"],
                 "c1_correlation": r["best_c1"], "c2_entropy": r["best_c2"],
                 "c3_misclass": r["best_c3"]}
                for r in all_runs
            ],
        },
        "scenarios": scenario_results,
        "cross_validation": cv_results,
        "sensitivity": {k: v for k, v in sensitivity.items()},
        "config": {
            "n_enterprises": CONFIG["n_enterprises"],
            "n_runs": CONFIG["n_runs"], "n_years": CONFIG["n_years"],
            "dt": CONFIG["dt"], "w_correlation": CONFIG["w_correlation"],
            "w_entropy": CONFIG["w_entropy"], "w_misclass": CONFIG["w_misclass"],
        },
        "calibration_grid": avg_grid.tolist(),
        "alpha_range": [float(a) for a in CONFIG["alpha_range"]],
        "delta_range": [float(d) for d in CONFIG["delta_range"]],
        "execution_time_seconds": round(elapsed, 1),
        "multi_horizon": multi_horizon_data,
    }
    return report


def run_multihorizon_analysis(alpha: float, delta: float, L: dict,
                                mh_base_seed: int = 2024) -> dict:
    original_n_years = CONFIG["n_years"]
    original_n_steps = CONFIG["n_steps"]
    original_n_ent = CONFIG["n_enterprises"]
    try:
        CONFIG["n_enterprises"] = min(500, CONFIG["n_enterprises"])
        scenarios_by_horizon = {}
        for h in (5, 10, 15):
            CONFIG["n_years"] = h
            CONFIG["n_steps"] = h * int(1.0 / CONFIG["dt"])
            print(f"    {L['horizons_years'].format(h=h)}", end=" ", flush=True)
            rng_mh = np.random.default_rng(mh_base_seed + h)
            ent = generate_enterprises(CONFIG["n_enterprises"], rng_mh)
            results = run_scenario_analysis(ent, alpha, delta, rng_mh)
            scenarios_by_horizon[h] = results
            summary = {s: (results[s]["admi_mean"][-1] - results[s]["admi_mean"][0])
                       for s in results}
            print(" ".join(f"{s}={v:+.3f}" for s, v in summary.items()))
    finally:
        CONFIG["n_years"] = original_n_years
        CONFIG["n_steps"] = original_n_steps
        CONFIG["n_enterprises"] = original_n_ent
    return {"scenarios_by_horizon": scenarios_by_horizon}


# ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="IM Onion-S — full simulation report (xlsx + PNG)")
    parser.add_argument("--lang", choices=["uk", "en"], default=None,
                        help="Output language; omit to prompt interactively")
    parser.add_argument("--export-pngs", action="store_true",
                        help="Save standalone PNGs for all charts and heatmaps")
    parser.add_argument("--no-multi", action="store_true",
                        help="Skip the multi-horizon analysis (10/15 years)")
    parser.add_argument("--quick", action="store_true",
                        help="Quick mode: 200 enterprises × 3 runs")
    parser.add_argument("--seed", type=int, default=None,
                        help="Master seed for stochastic components. Omit to "
                             "use the fixed dissertation seeds (deterministic). "
                             "If given, all seeds are derived from --seed N.")
    parser.add_argument("--output-dir", default=os.path.join(_HERE, "results"),
                        help="Folder for JSON and xlsx (default: ./results)")
    parser.add_argument("--figures-dir", default=os.path.join(_HERE, "figures"),
                        help="Folder for PNG and .dot (default: ./figures)")
    args = parser.parse_args()

    lang = args.lang if args.lang else prompt_language()
    L = get_labels(lang)
    print(f"  {L['lang_confirmed']}")

    seeds = derive_seeds(args.seed)
    if args.seed is not None:
        print(f"  Master seed: {args.seed} (non-default; results will differ "
              f"from dissertation baseline)")
    else:
        print(f"  Seeds: default (deterministic, dissertation baseline)")

    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(args.figures_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    report = run_full_pipeline(L, quick=args.quick,
                                run_multihorizon=not args.no_multi,
                                seeds=seeds)
    report["seeds"] = seeds
    report["master_seed"] = args.seed

    json_path = os.path.join(args.output_dir, "simulation_report.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n  {L['json_saved'].format(path=json_path)}")

    print(f"\n  {L['sf_generating']}")
    sf_paths = stock_flow_diagram.generate(args.figures_dir, lang=lang)
    for k, v in sf_paths.items():
        print(f"    {k}: {v}")

    if args.export_pngs:
        print(f"\n  {L['heatmap_exporting']}")
        hm_paths = heatmap_generator.generate_all(
            cv_results=report["cross_validation"],
            calib_grid=np.array(report["calibration_grid"]),
            alpha_range=report["alpha_range"],
            delta_range=report["delta_range"],
            output_dir=args.figures_dir, lang=lang,
        )
        for k, v in hm_paths.items():
            print(f"    {k}: {v}")

        print(f"\n  {L['charts_exporting']}")
        ch_paths = chart_pngs.generate_all(report, args.figures_dir, lang=lang)
        for k, v in ch_paths.items():
            print(f"    {k}: {v}")

    xlsx_path = os.path.join(args.output_dir, "onion_s_simulation.xlsx")
    print(f"\n  {L['xlsx_exporting']}")
    xlsx_exporter.export_to_xlsx(
        report=report,
        cv_results=report["cross_validation"],
        multi_horizon=report.get("multi_horizon"),
        output_path=xlsx_path,
        calib_grid=np.array(report["calibration_grid"]),
        alpha_range=report["alpha_range"],
        delta_range=report["delta_range"],
        timestamp=timestamp, lang=lang,
    )
    print(f"    {L['xlsx_saved'].format(path=xlsx_path)}")

    print(f"\n{'═' * 72}")
    print(f"  {L['report_complete']}")
    print(f"{'═' * 72}")


if __name__ == "__main__":
    main()
