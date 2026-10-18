#!/usr/bin/env python3
"""
============================================================================
IM Onion-S — експеримент S5 із послідовністю шарів
IM Onion-S — S5 layer-sequence experiment
============================================================================

UA: Вимірює ціну відхилення від порядку шарів (3) C → L1 → L2 → L3 → L4
    всередині моделі. Статичні сценарії (табл. A.2) задають незмінні частки
    бюджету на весь горизонт і тому не реалізують послідовності інвестицій.
    Тут порівнюються ДИНАМІЧНІ правила з однаковою інтенсивністю бюджету, які
    відрізняються лише тим, у якому порядку обирається фокусний шар.
EN: Measures the cost of departing from the layer order (3)
    C → L1 → L2 → L3 → L4 inside the model. The static scenarios (Table A.2)
    keep fixed budget shares over the whole horizon and therefore do not
    implement an investment sequence. Here DYNAMIC rules with identical budget
    intensity are compared; they differ only in the order in which the focal
    layer is chosen.

Правила / Rules:
  inner_first   — UA: найвнутрішніший шар нижче поточної цілі (аксіома 1)
                  EN: innermost layer below the current target (Axiom 1)
  weakest_first — UA: найслабший шар незалежно від порядку (слабка ланка)
                  EN: weakest layer regardless of order (weakest link)
  outer_first   — UA: найзовнішніший шар нижче цілі (дзеркало аксіоми 1)
                  EN: outermost layer below the target (mirror of Axiom 1)
  uniform       — UA: статичний рівномірний розподіл (референс, табл. A.2)
                  EN: static uniform allocation (reference, Table A.2)
  S2_core       — UA: статична концентрація на ядрі й персоналі (табл. A.2)
                  EN: static focus on core and personnel (Table A.2)

UA: Фокусний шар отримує FOCAL_SHARE бюджету, решта операційних шарів порівну
    ділять OTHER_SHARE, зв'язність I і готовність S мають фіксовані частки
    (як у uniform). Ціль динамічних правил піднімається сходами LADDER:
    спочатку всі шари доводяться до порога θ, потім до 0,60, потім до 0,80.
EN: The focal layer receives FOCAL_SHARE of the budget, the other operational
    layers split OTHER_SHARE equally, connectivity I and readiness S keep
    fixed shares (as in uniform). The target of the dynamic rules rises along
    LADDER: first all layers reach θ, then 0.60, then 0.80.

UA: Парний дизайн: ті самі підприємства, спільні випадкові числа (зерно шуму
    залежить від підприємства, а не від правила), 10 повторів.
EN: Paired design: the same enterprises, common random numbers (the noise
    seed depends on the enterprise, not on the rule), 10 replications.

UA: Важливо: експеримент НЕ перевіряє аксіому 1 (вона закладена в множник
    F_k), а вимірює величину ефекту порядку за припущень моделі.
EN: Note: the experiment does NOT test Axiom 1 (it is built into the
    multiplier F_k); it measures the size of the order effect under the
    model's assumptions.

Запуск / Usage (з кореня репозиторію / from the repo root, ≈ 2 min):
    python3 generate_report.py --lang uk --sequence-only
    python3 generate_report.py --lang en --sequence      # повний звіт + S5 / full report + S5
    python3 src/sequence_experiment.py --lang uk         # окремий запуск / standalone

Вихід / Outputs (results/):
    sequence_experiment.json     — UA: сирі результати (не залежать від мови)
                                   EN: raw results (language-independent)
    sequence_experiment.xlsx     — EN: tables and charts
    sequence_experiment.uk.xlsx  — UA: таблиці й графіки
    sequence_experiment.md       — EN: the same tables in Markdown
    sequence_experiment.uk.md    — UA: ті самі таблиці в Markdown

UA: Обидві мовні версії пишуться завжди, як README.md / README.uk.md;
    --lang визначає лише мову повідомлень у консолі.
EN: Both language versions are always written, like README.md / README.uk.md;
    --lang only sets the language of console messages.

UA: Код моделі (onion_s_simulation.py) не змінюється, тому всі числа v1.1.0
    лишаються чинними.
EN: The model code (onion_s_simulation.py) is unchanged, so all v1.1.0
    numbers remain valid.
============================================================================
"""

from __future__ import annotations
import argparse
import json
import math
import os
import sys
from datetime import datetime
from typing import Callable, Dict, List, Optional

import numpy as np

# UA: Робимо `src/` імпортованим і при окремому запуску цього файлу.
# EN: Make `src/` importable when this file is run standalone.
_SRC = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_SRC)
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from onion_s_simulation import (  # noqa: E402
    CONFIG, LAYER_NAMES, generate_enterprises, sd_step,
    compute_admi, compute_system_output, classify_maturity,
)


# ═══════════════════════════════════════════════════════════════════════════
# 1. ПАРАМЕТРИ ЕКСПЕРИМЕНТУ / EXPERIMENT PARAMETERS
# ═══════════════════════════════════════════════════════════════════════════

# UA: Відкалібровані α і δ (= θ) з основного прогону v1.1.0.
# EN: Calibrated α and δ (= θ) from the main v1.1.0 run.
ALPHA, THETA = 0.40, 0.375

# UA: Сходи цілі для динамічних правил: θ → 0,60 → 0,80.
# EN: Target ladder for the dynamic rules: θ → 0.60 → 0.80.
LADDER = [THETA, 0.60, 0.80]

# UA: Частки бюджету: фокусний шар, решта операційних шарів (разом), I, S.
# EN: Budget shares: focal layer, other operational layers (total), I, S.
FOCAL_SHARE, OTHER_SHARE, I_SHARE, S_SHARE = 0.55, 0.20, 0.15, 0.10

# UA: Розмір вибірки й кількість повторів (зерна популяції 1000 + 97·k).
# EN: Sample size and number of replications (population seeds 1000 + 97·k).
N_ENTERPRISES, N_SEEDS = 200, 10

# UA: Горизонти звітування (роки) і кількість кроків моделі на рік.
# EN: Reporting horizons (years) and model steps per year.
HORIZONS = [5, 10, 15]
STEPS_PER_YEAR = int(round(1.0 / CONFIG["dt"]))

# UA: Порівнювані правила; два перші — статичні сценарії з CONFIG.
# EN: Rules compared; the first two are static scenarios from CONFIG.
STRATEGIES = ["uniform", "S2_core", "inner_first", "weakest_first", "outer_first"]
INNER_ORDER = list(LAYER_NAMES)           # C, L1, L2, L3, L4
OUTER_ORDER = list(reversed(LAYER_NAMES))

# UA: Пари для парних різниць «ліве − праве».
# EN: Pairs for the paired differences "left − right".
COMPARISONS = [("inner_first", "outer_first"), ("inner_first", "weakest_first"),
               ("inner_first", "uniform"), ("weakest_first", "outer_first"),
               ("S2_core", "uniform")]

# UA: Метрики, для яких рахуються парні різниці.
# EN: Metrics used for the paired differences.
METRICS = ("admi", "dm_i", "output")


# ═══════════════════════════════════════════════════════════════════════════
# 2. ПРАВИЛА РОЗПОДІЛУ БЮДЖЕТУ / BUDGET ALLOCATION RULES
# ═══════════════════════════════════════════════════════════════════════════

def current_target(dm: Dict[str, float]) -> float:
    """
    UA: Повертає поточну сходинку цілі: найнижчу, якої ще не досяг хоча б
        один операційний шар.
    EN: Returns the current target rung: the lowest one that at least one
        operational layer has not reached yet.
    """
    for rung in LADDER:
        if any(dm[layer] < rung for layer in LAYER_NAMES):
            return rung
    return LADDER[-1]


def focal_layer(dm: Dict[str, float], strategy: str) -> str:
    """
    UA: Обирає фокусний шар для динамічного правила.
    EN: Chooses the focal layer for a dynamic rule.
    """
    # UA: Слабка ланка: мінімум DM серед операційних шарів.
    # EN: Weakest link: minimum DM among the operational layers.
    if strategy == "weakest_first":
        return min(LAYER_NAMES, key=lambda layer: dm[layer])
    # UA: Інакше перший шар нижче цілі в прямому або зворотному порядку.
    # EN: Otherwise the first layer below target in direct or reverse order.
    target = current_target(dm)
    order = INNER_ORDER if strategy == "inner_first" else OUTER_ORDER
    for layer in order:
        if dm[layer] < target:
            return layer
    return order[0]


def allocation_for(dm: Dict[str, float], strategy: str) -> Dict[str, float]:
    """
    UA: Частки бюджету на поточний квартал. Статичні сценарії беруться з
        CONFIG без змін; динамічні будуються навколо фокусного шару.
    EN: Budget shares for the current quarter. Static scenarios are taken
        from CONFIG unchanged; dynamic ones are built around the focal layer.
    """
    if strategy in CONFIG["scenarios"]:
        return CONFIG["scenarios"][strategy]
    focal = focal_layer(dm, strategy)
    shares = {layer: OTHER_SHARE / 4 for layer in LAYER_NAMES}
    shares[focal] = FOCAL_SHARE
    shares["I"], shares["S"] = I_SHARE, S_SHARE
    return shares


# ═══════════════════════════════════════════════════════════════════════════
# 3. СИМУЛЯЦІЯ ТА СТАТИСТИКА / SIMULATION AND STATISTICS
# ═══════════════════════════════════════════════════════════════════════════

def kendall_tau(first: List[float], second: List[float]) -> float:
    """
    UA: τ Кендалла (тип a) між двома рядами однакової довжини.
    EN: Kendall's τ (type a) between two sequences of equal length.
    """
    concordant = discordant = 0
    for first_index in range(len(first)):
        for second_index in range(first_index + 1, len(first)):
            sign = ((first[first_index] - first[second_index])
                    * (second[first_index] - second[second_index]))
            if sign > 0:
                concordant += 1
            elif sign < 0:
                discordant += 1
    pairs = len(first) * (len(first) - 1) / 2
    return (concordant - discordant) / pairs if pairs else float("nan")


def simulate(dm_start: Dict[str, float], strategy: str, n_steps: int, seed: int) -> Dict:
    """
    UA: Прогін одного підприємства за одним правилом. Зберігає стани на кінець
        кожного року, крок перетину θ кожним шаром і τ між фактичним порядком
        перетину та порядком (3).
    EN: Runs one enterprise under one rule. Stores the state at the end of each
        year, the step at which each layer crosses θ, and τ between the actual
        crossing order and the order (3).
    """
    rng = np.random.default_rng(seed)        # UA: спільні випадкові числа між правилами / EN: common random numbers across rules
    dm = dict(dm_start)
    crossing_step = {layer: (0 if dm[layer] >= THETA else None) for layer in LAYER_NAMES}
    snapshots = {}
    for step in range(1, n_steps + 1):
        # UA: Зовнішній тиск у цьому експерименті дорівнює нулю.
        # EN: External pressure is zero in this experiment.
        dm = sd_step(dm, allocation_for(dm, strategy), 0.0, rng)
        for layer in LAYER_NAMES:
            if crossing_step[layer] is None and dm[layer] >= THETA:
                crossing_step[layer] = step
        if step % STEPS_PER_YEAR == 0:
            snapshots[step // STEPS_PER_YEAR] = dict(dm)
    # UA: τ рахується лише для підприємств, у яких θ перетнули ≥ 3 шари.
    # EN: τ is computed only for enterprises where ≥ 3 layers crossed θ.
    crossed = [layer for layer in LAYER_NAMES if crossing_step[layer] is not None]
    tau = (kendall_tau([crossing_step[layer] for layer in crossed],
                       [LAYER_NAMES.index(layer) for layer in crossed])
           if len(crossed) >= 3 else float("nan"))
    return {"snapshots": snapshots, "tau": tau, "n_crossed": len(crossed)}


def summarise(values: List[float]) -> Dict[str, float]:
    """
    UA: Середнє, вибіркове SD і n без урахування NaN.
    EN: Mean, sample SD and n, ignoring NaN.
    """
    arr = np.array([value for value in values if not (isinstance(value, float) and math.isnan(value))])
    if arr.size == 0:
        return {"mean": float("nan"), "sd": float("nan"), "n": 0}
    return {"mean": float(arr.mean()), "sd": float(arr.std(ddof=1)) if arr.size > 1 else 0.0, "n": int(arr.size)}


def run(progress: Optional[Callable[[int, int], None]] = None) -> Dict:
    """
    UA: Повний експеримент: N_SEEDS повторів × N_ENTERPRISES підприємств ×
        усі правила. `progress(k, n)` (необов'язково) викликається після
        кожного повтору й на результат не впливає.
    EN: Full experiment: N_SEEDS replications × N_ENTERPRISES enterprises ×
        all rules. `progress(k, n)` (optional) is called after each
        replication and does not affect the results.
    """
    n_steps = max(HORIZONS) * STEPS_PER_YEAR
    per_seed = []
    for seed_index in range(N_SEEDS):
        # UA: Та сама популяція й те саме зерно шуму для всіх правил (парний дизайн).
        # EN: The same population and noise seed for every rule (paired design).
        population_seed = 1000 + seed_index * 97
        enterprises = generate_enterprises(N_ENTERPRISES, np.random.default_rng(population_seed))
        runs = {strategy: [simulate(enterprise.dm, strategy, n_steps, population_seed * 1000 + enterprise.id)
                           for enterprise in enterprises] for strategy in STRATEGIES}
        # UA: Метрики на кінець кожного горизонту для кожного підприємства.
        # EN: Per-enterprise metrics at the end of each horizon.
        metrics = {}
        for strategy in STRATEGIES:
            metrics[strategy] = {}
            for horizon in HORIZONS:
                states = [run_result["snapshots"][horizon] for run_result in runs[strategy]]
                admi = [compute_admi(state, ALPHA, THETA) for state in states]
                metrics[strategy][horizon] = {
                    "admi": admi,
                    "dm_i": [state["I"] for state in states],
                    "output": [compute_system_output(state) for state in states],
                    "level4_share": float(np.mean([classify_maturity(value) >= 4 for value in admi])),
                    "layers": {layer: float(np.mean([state[layer] for state in states])) for layer in LAYER_NAMES},
                }
            metrics[strategy]["tau"] = [run_result["tau"] for run_result in runs[strategy]]
        per_seed.append(metrics)
        if progress is not None:
            progress(seed_index + 1, N_SEEDS)

    report = {"design": {"n_enterprises": N_ENTERPRISES, "n_seeds": N_SEEDS, "alpha": ALPHA, "theta": THETA,
                         "ladder": LADDER, "focal_share": FOCAL_SHARE, "other_share": OTHER_SHARE,
                         "i_share": I_SHARE, "s_share": S_SHARE, "horizons": HORIZONS,
                         "strategies": STRATEGIES, "external_pressure": 0.0},
              "strategies": {}, "paired_differences": {}}

    # UA: Зведення по правилах: середнє й SD середніх між повторами.
    # EN: Per-rule summary: mean and SD of replication means.
    for strategy in STRATEGIES:
        entry = {"tau": summarise([tau for metrics in per_seed for tau in metrics[strategy]["tau"]])}
        for horizon in HORIZONS:
            seed_means = {key: [float(np.mean(metrics[strategy][horizon][key])) for metrics in per_seed]
                          for key in METRICS}
            entry[str(horizon)] = {
                key: summarise(seed_means[key]) for key in seed_means}
            entry[str(horizon)]["admi_sd_within"] = float(np.mean(
                [np.std(metrics[strategy][horizon]["admi"]) for metrics in per_seed]))
            entry[str(horizon)]["level4_share"] = float(np.mean(
                [metrics[strategy][horizon]["level4_share"] for metrics in per_seed]))
            entry[str(horizon)]["layers"] = {layer: float(np.mean(
                [metrics[strategy][horizon]["layers"][layer] for metrics in per_seed])) for layer in LAYER_NAMES}
        report["strategies"][strategy] = entry

    # UA: Парні різниці по підприємствах; 95% ДІ за нормальним наближенням.
    # EN: Paired per-enterprise differences; 95% CI by normal approximation.
    for left, right in COMPARISONS:
        key = "%s_minus_%s" % (left, right)
        report["paired_differences"][key] = {}
        for horizon in HORIZONS:
            for metric in METRICS:
                diffs = np.concatenate([np.array(metrics[left][horizon][metric]) - np.array(metrics[right][horizon][metric])
                                        for metrics in per_seed])
                seed_level = [float(np.mean(np.array(metrics[left][horizon][metric]) - np.array(metrics[right][horizon][metric])))
                              for metrics in per_seed]
                half_width = 1.96 * diffs.std(ddof=1) / math.sqrt(diffs.size)
                report["paired_differences"][key]["%s_%d" % (metric, horizon)] = {
                    "mean": float(diffs.mean()), "ci95": [float(diffs.mean() - half_width), float(diffs.mean() + half_width)],
                    "sd_between_seeds": float(np.std(seed_level, ddof=1)), "n_pairs": int(diffs.size)}
    return report


# ═══════════════════════════════════════════════════════════════════════════
# 4. ВИВІД У MARKDOWN / MARKDOWN OUTPUT
# ═══════════════════════════════════════════════════════════════════════════

def fmt(value: float, digits: int = 3, lang: str = "uk") -> str:
    """
    UA: Число з фіксованою кількістю знаків; для uk десяткова кома.
    EN: Fixed-digit number; decimal comma for uk, point for en.
    """
    if math.isnan(value):
        return "—"
    text = "%%.%df" % digits % value
    return text.replace(".", ",") if lang == "uk" else text


def write_markdown(report: Dict, path: str, lang: str = "uk") -> None:
    """
    UA: Ті самі результати, що й у JSON, таблицями Markdown (мова uk або en).
        Для uk вивід побайтово збігається з версією v1.2.0.
    EN: The same results as in the JSON, as Markdown tables (uk or en).
        For uk the output is byte-identical to the v1.2.0 version.
    """
    from i18n import get_labels
    L = get_labels(lang)
    design = report["design"]
    lines = ["# " + L["seq_md_title"], "",
             L["seq_md_design"].format(n=design["n_enterprises"], k=design["n_seeds"],
                                       a=fmt(design["alpha"], 2, lang), t=fmt(design["theta"], 3, lang)), ""]
    for horizon in design["horizons"]:
        lines += ["## " + L["seq_md_horizon"].format(h=horizon), "",
                  "| %s |" % " | ".join([L["seq_col_rule"], L["seq_col_admi_sd"], "DM_I", L["seq_col_output"],
                                         L["seq_col_level4"], "C", "L₁", "L₂", "L₃", "L₄"]),
                  "|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for strategy in design["strategies"]:
            entry = report["strategies"][strategy][str(horizon)]
            lines.append("| %s | %s ± %s | %s | %s | %s | %s |" % (
                strategy, fmt(entry["admi"]["mean"], lang=lang), fmt(entry["admi"]["sd"], lang=lang),
                fmt(entry["dm_i"]["mean"], lang=lang), fmt(entry["output"]["mean"], lang=lang),
                fmt(entry["level4_share"], 2, lang),
                " | ".join(fmt(entry["layers"][layer], 2, lang) for layer in LAYER_NAMES)))
        lines.append("")
    lines += ["## " + L["seq_md_tau_title"], "",
              "| %s | %s | SD | %s |" % (L["seq_col_rule"], L["seq_col_tau_mean"], L["seq_col_tau_n"]),
              "|:---|---:|---:|---:|"]
    for strategy in design["strategies"]:
        tau = report["strategies"][strategy]["tau"]
        lines.append("| %s | %s | %s | %d |" % (strategy, fmt(tau["mean"], 2, lang), fmt(tau["sd"], 2, lang), tau["n"]))
    lines += ["", "## " + L["seq_md_diff_title"], "",
              "| %s | %s | ΔADMI | ΔDM_I | %s |" % (L["seq_col_comparison"], L["seq_col_horizon"], L["seq_col_delta_output"]),
              "|:---|---:|---:|---:|---:|"]
    for key, entry in report["paired_differences"].items():
        for horizon in design["horizons"]:
            cells = []
            for metric in METRICS:
                item = entry["%s_%d" % (metric, horizon)]
                cells.append("%s [%s; %s]" % (fmt(item["mean"], lang=lang), fmt(item["ci95"][0], lang=lang),
                                              fmt(item["ci95"][1], lang=lang)))
            lines.append("| %s | %d | %s |" % (key.replace("_minus_", " − "), horizon, " | ".join(cells)))
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


# ═══════════════════════════════════════════════════════════════════════════
# 5. ЗАПУСК І ЗБЕРЕЖЕННЯ / RUN AND SAVE
# ═══════════════════════════════════════════════════════════════════════════

def run_and_save(output_dir: str, lang: str = "uk",
                 timestamp: Optional[str] = None, verbose: bool = True) -> Dict[str, str]:
    """
    UA: Запускає експеримент один раз і зберігає JSON, а також xlsx і md
        обома мовами (i18n.OUTPUT_LANGS) у `output_dir`. `lang` задає лише мову
        консолі. Повертає шляхи до файлів. Викликається з generate_report.py.
    EN: Runs the experiment once and saves the JSON plus xlsx and md in both
        languages (i18n.OUTPUT_LANGS) to `output_dir`. `lang` only sets the console
        language. Returns the file paths. Called from generate_report.py.
    """
    # UA: OUTPUT_LANGS — спільна для всього пакета мапа «мова → суфікс імені».
    # EN: OUTPUT_LANGS is the package-wide map "language → file-name suffix".
    from i18n import get_labels, OUTPUT_LANGS
    import export_to_xlsx as xlsx_exporter
    L = get_labels(lang)

    def _progress(done: int, total: int) -> None:
        if verbose:
            print("    " + L["seq_progress"].format(k=done, n=total), flush=True)

    report = run(progress=_progress)
    os.makedirs(output_dir, exist_ok=True)
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    base = os.path.join(output_dir, "sequence_experiment")
    paths = {"json": base + ".json"}
    # UA: Формат JSON не змінено відносно v1.2.0.
    # EN: The JSON format is unchanged from v1.2.0.
    with open(paths["json"], "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    for out_lang, suffix in OUTPUT_LANGS.items():
        paths[f"xlsx ({out_lang})"] = base + suffix + ".xlsx"
        paths[f"md ({out_lang})"] = base + suffix + ".md"
        xlsx_exporter.export_sequence_to_xlsx(report, paths[f"xlsx ({out_lang})"],
                                              timestamp=timestamp, lang=out_lang)
        write_markdown(report, paths[f"md ({out_lang})"], lang=out_lang)
    return paths


def main() -> None:
    """
    UA: Окремий запуск без generate_report.py.
    EN: Standalone run without generate_report.py.
    """
    from i18n import get_labels, prompt_language
    parser = argparse.ArgumentParser(
        description="IM Onion-S — S5 sequence experiment (json + xlsx + md)")
    parser.add_argument("--lang", choices=["uk", "en"], default=None,
                        help="Console language (files are written in both); omit to prompt")
    parser.add_argument("--output-dir", default=os.path.join(_ROOT, "results"),
                        help="Folder for JSON, xlsx and md in uk + en (default: ./results)")
    args = parser.parse_args()
    lang = args.lang if args.lang else prompt_language()
    L = get_labels(lang)
    print(f"  {L['lang_confirmed']}")
    print(f"\n{L['step_seq']}...")
    paths = run_and_save(args.output_dir, lang=lang)
    for kind, path in paths.items():
        print(f"    {kind}: {path}")


if __name__ == "__main__":
    main()
