> **English** · [Українська](README.uk.md)

 [![DOI](https://zenodo.org/badge/1215136888.svg)](https://doi.org/10.5281/zenodo.19979159)

# IM Onion-S — Simulation Model of Digital Transformation of Agri-food Enterprises

Strategic management simulation of digital transformation based on **System Dynamics** + **Markov chains**. The model generates ~10,000 virtual enterprises, calibrates the penalty parameters α and δ of the ADMI formula, performs scenario analysis of 5 strategies over horizons of 5/10/15 years, cross-validates SD results against Markov transition matrices, and runs a parameter sensitivity analysis.

Outputs are a structured xlsx report with 20 sheets (tables + embedded charts + conditional-formatting heatmaps) and a set of PNG charts ready for publications.

Part of a PhD research project (Economics, specialty 051). All output is bilingual (Ukrainian / English) with runtime switching.

---

## Quick start

```bash
# 1. Install dependencies (once)
pip3 install -r requirements.txt

# 2. Run the full pipeline
python3 generate_report.py
```

The script asks which language (`uk` / `en`) to use, then runs the simulation and saves outputs to:
- `results/simulation_report.json` — raw data
- `results/onion_s_simulation.xlsx` — full xlsx report
- `figures/stock_flow.png`, `figures/stock_flow.dot` — Stock-and-Flow diagram

---

## CLI flags

| Flag | Description |
|---|---|
| `--lang uk` / `--lang en` | Output language (skips interactive prompt) |
| `--quick` | Quick mode: 200 enterprises × 3 runs (≈8 s instead of ≈3–5 min) |
| `--no-multi` | Skip multi-horizon analysis (10 / 15 years) |
| `--export-pngs` | Generate PNGs for all 5 main charts + 4 heatmaps |
| `--output-dir PATH` | Custom folder for JSON / xlsx (default: `./results`) |
| `--figures-dir PATH` | Custom folder for PNG / .dot (default: `./figures`) |

### Examples

```bash
# Quick pipeline test, Ukrainian
python3 generate_report.py --quick --lang uk

# Full cycle with all PNGs, English
python3 generate_report.py --lang en --export-pngs

# Without 10 / 15-year horizons (faster)
python3 generate_report.py --lang en --no-multi --export-pngs
```

---

## Outputs

### `results/simulation_report.json`
Structured JSON with all raw data: calibration, ADMI trajectories, per-component DM, Markov transition matrices, stationary distributions, hitting times, parameter sensitivity, multi-horizon results.

### `results/onion_s_simulation.xlsx`
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

None of the PNGs have an overlaid title — the caption is added in the publication text.

---

## Runtime

| Mode | Time |
|---|---|
| `--quick` (200 × 3, 5 years) | ≈ 4–5 s |
| `--quick` + multi-horizon | ≈ 8–10 s |
| Full (1000 × 10, 5 years) | ≈ 1–2 min |
| Full + multi-horizon | ≈ 3–5 min |

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

New scenarios are added to `CONFIG["scenarios"]` + translations in `src/i18n.py` (`SCENARIO_KEY_MAP` + UK / EN dictionaries).

---

## Citation

<!-- TODO: replace DOI placeholder below once Zenodo mints one after the first GitHub release -->

<!-- [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX) -->

If you use this software in your research, please cite it. Machine-readable
metadata is in [`CITATION.cff`](CITATION.cff); GitHub renders a "Cite this
repository" button in the sidebar automatically.

**Recommended citation (APA-like):**

> Kondratiuk, D. (2026). *IM Onion-S — Simulation Model of Digital
> Transformation of Agri-food Enterprises* (Version 1.0.0) [Computer software].
> Zenodo. https://doi.org/10.5281/zenodo.XXXXXXX

**BibTeX:**

```bibtex
@software{kondratiuk_im_onion_s_2026,
  author       = {Kondratiuk, Dmytro},
  title        = {{IM Onion-S — Simulation Model of Digital
                   Transformation of Agri-food Enterprises}},
  year         = {2026},
  version      = {1.0.0},
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.XXXXXXX},
  url          = {https://doi.org/10.5281/zenodo.XXXXXXX}
}
```

**ДСТУ 8302:2015 (Ukrainian academic standard):**

> Кондратюк Д. IM Onion-S — Simulation Model of Digital Transformation of
> Agri-food Enterprises: комп'ютерна програма. Версія 1.0.0. Zenodo, 2026.
> DOI: 10.5281/zenodo.XXXXXXX. URL:
> https://github.com/DmytroKondratiuk/im_onion_s

---

## License

Apache-2.0 (see `CITATION.cff` and forthcoming `LICENSE` file). The code is released
for reproducibility of the dissertation results; if you build on it, please
cite as shown above.

---

## Author

Dmytro Kondratiuk — PhD research in Economics (specialty 051), thesis «Strategic management of digital transformation of agri-food enterprises: theory, methodology, implementation».
