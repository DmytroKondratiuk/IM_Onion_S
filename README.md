> **English** · [Українська](README.uk.md)

 [![DOI](https://zenodo.org/badge/1215136888.svg)](https://doi.org/10.5281/zenodo.19979159)

# IM Onion-S — Simulation Model of Digital Transformation of Agri-food Enterprises

Strategic management simulation of digital transformation based on **System Dynamics** + **Markov chains**. The model generates synthetic enterprises (3 runs × 200 in the default reproducible run; up to 10 × 1000 in full mode), calibrates the penalty parameters α and δ of the ADMI formula, performs scenario analysis of 5 strategies over horizons of 5/10/15 years, cross-validates SD results against Markov transition matrices, and runs a parameter sensitivity analysis.

Outputs are a structured xlsx report with 20 sheets (tables + embedded charts + conditional-formatting heatmaps) and a set of PNG charts ready for publications.

Part of a PhD research project (Economics, specialty 051). Every report file is written in both languages in one run: English without a suffix, Ukrainian with `.uk` before the extension (e.g. `onion_s_simulation.xlsx` and `onion_s_simulation.uk.xlsx`).

---

## Quick start

```bash
# 1. Install dependencies (once)
pip3 install -r requirements.txt

# 2. Run the full pipeline
python3 generate_report.py
```

The script asks which language (`uk` / `en`) to use for console messages, then runs the simulation and saves outputs in both languages to:
- `results/simulation_report.json` — raw data (language-independent)
- `results/onion_s_simulation.xlsx`, `results/onion_s_simulation.uk.xlsx` — full xlsx report, English / Ukrainian
- `figures/stock_flow{,.uk}.png`, `figures/stock_flow{,.uk}.dot` — Stock-and-Flow diagram, English / Ukrainian

---

## CLI flags

| Flag | Description |
|---|---|
| `--lang uk` / `--lang en` | Console language (skips interactive prompt); files are always written in both languages |
| `--quick` | Quick mode: 200 enterprises × 3 runs (≈8 s instead of ≈3–5 min) |
| `--no-multi` | Skip multi-horizon analysis (10 / 15 years) |
| `--export-pngs` | Generate PNGs for all 5 main charts + 4 heatmaps |
| `--output-dir PATH` | Custom folder for JSON / xlsx (default: `./results`) |
| `--figures-dir PATH` | Custom folder for PNG / .dot (default: `./figures`) |
| `--sequence` | Also run the sequence experiment S5 after the main pipeline (≈ 20 s – 2 min) |
| `--sequence-only` | Run only the sequence experiment S5 and skip the main pipeline |

### Examples

```bash
# Quick pipeline test, Ukrainian
python3 generate_report.py --quick --lang uk

# Full cycle with all PNGs, English
python3 generate_report.py --lang en --export-pngs

# Without 10 / 15-year horizons (faster)
python3 generate_report.py --lang en --no-multi --export-pngs

# Sequence experiment S5 only
python3 generate_report.py --lang en --sequence-only
```

---

## Outputs

### `results/simulation_report.json`
Structured JSON with all raw data: calibration, ADMI trajectories, per-component DM, Markov transition matrices, stationary distributions, hitting times, parameter sensitivity, multi-horizon results.

### `results/onion_s_simulation.xlsx` (English) and `results/onion_s_simulation.uk.xlsx` (Ukrainian)
20 sheets, split into 2 groups:

**Data tables (15 sheets):**
- Metadata (run details)
- Calibration (α*, δ*, J, C₁, C₂, C₃ across 10 runs)
- Heatmap J(α,δ) with conditional formatting
- Depreciation d_k
- Scenario ADMI (mean / std / median / p25 / p75 trajectories)
- Per-component DM (DM_i by year × scenario)
- Level distribution (enterprise distribution across 5 maturity levels)
- 3× Markov matrices (S-1 / S-2 / S-3) with conditional-formatting heatmap
- Stationary distributions π
- Hitting times
- Multi-horizon (ΔADMI 5 / 10 / 15)
- Cross-validation (SD vs Markov)
- Sensitivity (OAT ±20%)

**Chart sheets (5 sheets, openpyxl charts without titles):**
- ADMI trajectories (LineChart)
- DM profiles (RadarChart)
- Multi-horizon (BarChart)
- Cross-validation (BarChart)
- Sensitivity (Tornado BarChart)

### `figures/` (with `--export-pngs`)

| File | Description |
|---|---|
| `stock_flow.png` | Stock-and-Flow diagram (matplotlib, always generated) |
| `stock_flow.dot` | Graphviz source for **draw.io** import (always) |
| `trajectories_admi.png` | Line chart of ADMI trajectories per scenario |
| `profiles_radar.png` | Radar chart of DM profiles at year 5 |
| `multi_horizon_bar.png` | Grouped bar chart ΔADMI × 5 / 10 / 15 years |
| `cross_validation_bar.png` | SD vs Markov (Uniform strategy) |
| `sensitivity_tornado.png` | Tornado chart of parameter sensitivity |
| `heatmap_uniform.png` | Markov transition matrix — S-1 Uniform |
| `heatmap_S2_core.png` | Transition matrix — S-2 Core |
| `heatmap_S3_integration.png` | Transition matrix — S-3 Integration |
| `heatmap_calibration.png` | J(α, δ) heatmap with optimum marker |

Each file also has a Ukrainian version with `.uk` before the extension (e.g. `trajectories_admi.uk.png`, `stock_flow.uk.dot`). None of the PNGs have an overlaid title — the caption is added in the publication text.

### `results/sequence_experiment.*` (with `--sequence` / `--sequence-only`)

Results of the sequence experiment S5 (see below). The experiment runs once and always writes both language versions, whatever `--lang` is set to:

| File | Content |
|---|---|
| `sequence_experiment.json` | raw data (language-independent) |
| `sequence_experiment.xlsx` / `sequence_experiment.uk.xlsx` | tables and charts, English / Ukrainian |
| `sequence_experiment.md` / `sequence_experiment.uk.md` | the same tables in Markdown, English / Ukrainian |

The xlsx has 6 sheets: About (design parameters), Results by horizon (ADMI, DM_I, output, share at level ≥ 4, layer states), Kendall τ, Paired differences with 95 % CI, and two chart sheets (ADMI by rule and horizon, paired ΔADMI). The md files repeat the same tables in Markdown; the Ukrainian one uses decimal commas.

---

## Runtime

| Mode | Time |
|---|---|
| `--quick` (200 × 3, 5 years) | ≈ 4–5 s |
| `--quick` + multi-horizon | ≈ 8–10 s |
| Full (1000 × 10, 5 years) | ≈ 1–2 min |
| Full + multi-horizon | ≈ 3–5 min |

---

## Reproducibility of published results

The committed `results/` and `figures/` (both language versions) are produced by the **default deterministic run**:

```bash
python3 generate_report.py --lang en --quick --export-pngs
```

This run uses the fixed dissertation seeds (`DEFAULT_SEEDS` in `generate_report.py`) and the quick design of **3 independent runs × 200 synthetic enterprises** (600 in total), plus the multi-horizon block (5/10/15 years). All figures quoted in the dissertation and in the related journal article (calibrated α = 0.40, δ = 0.375; baseline ADMI 0.393 → 0.348 over 5 years and −0.121 over 15 years; +0.029 for the core strategy; 3.5× relative growth for the integration strategy) are reproduced exactly by this command. The full mode (10 runs × 1000 enterprises, run without `--quick`) is available for robustness checks but is not the source of the published numbers. Passing `--seed N` derives a different seed bundle and therefore yields different values.

### Sequence experiment (v1.2.0)

The static budget scenarios keep fixed shares over the whole horizon and therefore do not implement an investment *sequence*. The sequence experiment (`src/sequence_experiment.py`) measures the cost of departing from the layer order C → L1 → L2 → L3 → L4 inside the model:

```bash
python3 generate_report.py --lang en --sequence-only   # ≈ 20 s – 2 min, writes results/sequence_experiment.* (uk + en)
python3 src/sequence_experiment.py --lang en           # the same, standalone
```

Three dynamic rules with identical budget intensity re-select a focal layer every quarter (55 % of the budget; other operational layers 5 % each, integration 15 %, strategic readiness 10 %). The target rises in steps δ = 0.375 → 0.60 → 0.80. *inner_first* picks the innermost layer below target, *weakest_first* the weakest layer regardless of order, *outer_first* the outermost layer below target; static *uniform* and *S2_core* are included for reference. Paired design: the same 200 enterprises and the same noise seed for every rule, 10 replications (seeds 1000 + 97·k), no external pressure.

Key 15-year results: inner_first − outer_first ΔADMI +0.031 (95 % CI 0.030–0.032), Δoutput +0.023; inner_first − weakest_first ΔADMI +0.011, Δoutput −0.003; S2_core − uniform ΔADMI +0.005, Δoutput −0.035. The experiment does **not** test Axiom 1 — it is built into the inner-layer multiplier — it quantifies the size of the order effect under the model's assumptions.

---

## Model specification

The full model description (variables, equations, parameters, synthetic sample, calibration of α and δ, scenario results, sensitivity, sequence experiment) is given in [`docs/model_specification.md`](docs/model_specification.md) (Ukrainian version: [`docs/model_specification.uk.md`](docs/model_specification.uk.md)). Articles based on the model cite this document and reproduce only the parts they need in their appendices.

---

## Importing `.dot` into draw.io

The Stock-and-Flow diagram is saved in two formats: PNG (ready for publication) and **.dot** (Graphviz), which can be imported into draw.io for further editing:

1. Open <https://app.diagrams.net> (or the desktop app).
2. **File → Import → Device…**
3. Select `figures/stock_flow.dot`.
4. If prompted — choose «Graphviz (.dot)» in the import dialog.

---

## Configuration

All model parameters live in `src/onion_s_simulation.py`, dictionary `CONFIG`:

```python
CONFIG = {
    "n_enterprises": 1000,            # sample size
    "n_runs": 10,                     # independent calibration runs
    "n_years": 5,                     # horizon
    "dt": 0.25,                       # quarterly step
    "alpha_range": np.arange(...),    # grid for α
    "delta_range": np.arange(...),    # grid for δ
    "budget_total": 0.40,             # budget per quarter
    "investment_efficiency": 0.55,    # η
    "absorptive_saturation": 0.4,     # σ (absorptive capacity)
    "integration_power": 0.5,         # β (integration power fn.)
    "scenarios": { ... },             # 5 budget allocation vectors
    ...
}
```

New scenarios are added to `CONFIG["scenarios"]` + translations in `src/i18n.py` (`SCENARIO_KEY_MAP` + UK / EN dictionaries). Parameters of the sequence experiment (budget shares, target ladder, replications) are constants at the top of `src/sequence_experiment.py`; its labels are the `seq_*` keys in `src/i18n.py`.

---

## Citation

If you use this software in your research, please cite it. Machine-readable
metadata is in [`CITATION.cff`](CITATION.cff); GitHub renders a "Cite this
repository" button in the sidebar automatically.

**Recommended citation (APA-like):**

> Kondratiuk, D. (2026). *IM Onion-S — Simulation Model of Digital
> Transformation of Agri-food Enterprises* (Version 1.2.0) [Computer software].
> Zenodo. https://doi.org/10.5281/zenodo.19979159

**BibTeX:**

```bibtex
@software{kondratiuk_im_onion_s_2026,
  author       = {Kondratiuk, Dmytro},
  title        = {{IM Onion-S — Simulation Model of Digital
                   Transformation of Agri-food Enterprises}},
  year         = {2026},
  version      = {1.2.0},
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.19979159},
  url          = {https://doi.org/10.5281/zenodo.19979159}
}
```

**ДСТУ 8302:2015 (Ukrainian academic standard):**

> Кондратюк Д. IM Onion-S — Simulation Model of Digital Transformation of
> Agri-food Enterprises: комп'ютерна програма. Версія 1.2.0. Zenodo, 2026.
> DOI: 10.5281/zenodo.19979159. URL:
> https://github.com/DmytroKondratiuk/im_onion_s

---

## License

Apache-2.0 (see `LICENSE` and `CITATION.cff`). The code is released
for reproducibility of the dissertation results; if you build on it, please
cite as shown above.

---

## Author

Dmytro Kondratiuk — PhD research in Economics (specialty 051), thesis «Strategic management of digital transformation of agri-food enterprises: theory, methodology, implementation».
