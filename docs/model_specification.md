# Specification of the IM Onion-S simulation model

*Ukrainian version: [`model_specification.uk.md`](model_specification.uk.md).*

This document describes the model in full: variables, equations, parameters, the synthetic sample, the calibration of the aggregation rule, scenario results, the sensitivity analysis and the sequence experiment. Articles based on the model reproduce in their appendices only the equations and results their conclusions require, and refer to this document for the rest.

All figures below are reproduced by the standard deterministic run (`python3 generate_report.py --lang en --quick --export-pngs`) and by the sequence experiment (`python3 generate_report.py --lang en --sequence-only`, code in `src/sequence_experiment.py`). The model code is in `src/onion_s_simulation.py`, and the parameters are in the `CONFIG` dictionary.

## 1. Purpose and status

The model implements Axioms 1–3 of the Onion-S model as system dynamics equations and shows which quantitative implications follow from them. The parameters were set by the author on the basis of the logic of the axioms and were not estimated on empirical data. Only the two parameters of the aggregation rule, $\alpha$ and $\delta$, are calibrated. The results are therefore illustrative and are not a forecast. The parameters must be recalibrated after the first field survey.

## 2. State variables

The state of an enterprise is described by seven stocks with values from 0 to 1. The five operational layers $DM_{C}, DM_{L_{1}}, \dots, DM_{L_{4}}$ enter the index $ADMI$ through an aggregation rule with a weakest-link penalty:

$$ADMI = \frac{1}{5}\sum_{k} DM_{k} \cdot \Big[1 - \alpha \cdot \max\big(0,\ \delta - DM_{\min}\big)\Big]$$

Connectivity $DM_{I}$ and strategic readiness $DM_{S}$ are diagnostic indicators and do not enter the index. The integration step is one quarter ($\Delta t = 0.25$ year, Euler method). In the code these are the functions `compute_admi_base`, `compute_penalty` and `compute_admi`.

## 3. Equations

The increment of stock $k$ per step (function `sd_step`) is:

$$\Delta DM_{k} = \big(EI_{k} - d_{k}\, DM_{k} + \varepsilon_{k}\big)\, \Delta t,\qquad \varepsilon_{k} \sim N(0;\ 0.005^{2}) \tag{1}$$

A positive increment slows down near the upper bound, $\Delta DM_{k} \leftarrow \Delta DM_{k}\,(1 - DM_{k})^{0.6}$. Values are bounded to the interval from 0.001 to 0.999.

The effective investment in an operational layer is:

$$EI_{k} = B\, w_{k}\, \eta\; F_{k}\; A\; \Phi,\qquad k \in \{C, L_{1}, \dots, L_{4}\} \tag{2}$$

where $B$ is the quarterly budget, $w_{k}$ the budget share of the layer under the scenario and $\eta$ the investment efficiency. The axioms are implemented by the following multipliers.

The inner-layer multiplier implements Axiom 1:

$$F_{k} = 0.3 + 0.7\,\big(0.7\,\overline{DM}_{inner(k)} + 0.3\, DM_{\min,\,inner(k)}\big),\qquad F_{C} = 1 \tag{3}$$

where $inner(k)$ is the set of layers preceding $k$ in the order $C \prec L_{1} \prec L_{2} \prec L_{3} \prec L_{4}$.

The absorptive capacity of staff is:

$$A = \min\big(1;\ DM_{L_{1}} / \sigma\big) \tag{4}$$

The multiplier $A$ applies to all operational layers, including the core. This expresses the dual role of staff, both as a layer and as a cross-cutting constraint.

The connectivity multiplier implements Axiom 2:

$$\Phi = 0.5 + 0.5\, DM_{I}^{\beta} \tag{5}$$

Investment in connectivity depends on the evenness of the profile, $EI_{I} = B\, w_{I}\, \eta\, H$, where $H = \max\big(0.2;\ 1 - 2\,\mathrm{sd}(DM_{C}, \dots, DM_{L_{4}})\big)$. For strategic readiness, $EI_{S} = 0.8\, B\, w_{S}\, \eta$.

Axiom 3 is implemented in the market scenario. From the second year, $0.5\, e\, \Delta t$ is added to $EI_{L_{4}}$, where $e = 0.15$ is the magnitude of external regulatory pressure (`external_shock_year`, `external_shock_magnitude`).

Integral efficiency (function `compute_system_output`) is the power mean of the layers with exponent −0.5, multiplied by $DM_{I}^{\beta}$ and by $(1 + 0.2\, DM_{S})$. It is used only to compare rules and scenarios and is not an estimate of actual production output.

## 4. Parameters

| Parameter | Value | Key in `CONFIG` |
|:---|---:|:---|
| Quarterly budget $B$ | 0.40 | `budget_total` |
| Investment efficiency $\eta$ | 0.55 | `investment_efficiency` |
| Absorptive capacity saturation $\sigma$ | 0.4 | `absorptive_saturation` |
| Connectivity exponent $\beta$ | 0.5 | `integration_power` |
| External pressure $e$ | 0.15 | `external_shock_magnitude` |

The quarterly depreciation rates $d_{k}$ (`depreciation_by_layer`) are 0.015 for C, 0.020 for L₁, 0.025 for L₂, 0.030 for L₃, 0.025 for L₄, 0.020 for I and 0.010 for S.

**Table 1.** Budget shares by scenario (`scenarios`).

| Scenario | C | L₁ | L₂ | L₃ | L₄ | I | S |
|:---|---:|---:|---:|---:|---:|---:|---:|
| Inaction | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Uniform | 0.15 | 0.15 | 0.15 | 0.15 | 0.15 | 0.15 | 0.10 |
| Core and staff | 0.35 | 0.25 | 0.10 | 0.05 | 0.05 | 0.15 | 0.05 |
| Integration breakthrough | 0.10 | 0.10 | 0.10 | 0.10 | 0.10 | 0.40 | 0.10 |
| Market under pressure | 0.05 | 0.05 | 0.10 | 0.15 | 0.30 | 0.20 | 0.15 |

## 5. Synthetic sample

Each run generates 200 enterprises of five profile types (function `generate_enterprises`). Balanced profiles make up 30%, profiles with one failing layer 25%, profiles with a strong core and weak periphery 20%, inverted profiles with a weak core and strong periphery 15%, and random profiles 10%. The mean initial values are C 0.448, L₁ 0.432, L₂ 0.418, L₃ 0.413, L₄ 0.409, I 0.353 and S 0.405. With $\alpha = 0.40$ and $\delta = 0.375$, the mean initial $ADMI$ is 0.393.

## 6. Calibration of $\alpha$ and $\delta$

A grid search over $\alpha$ from 0.10 to 1.00 in steps of 0.05 and over $\delta$ from 0.10 to 0.40 in steps of 0.025 maximises the criterion (function `combined_criterion`):

$$J = 0.4\, C_{1} + 0.3\, C_{2} - 0.3\, C_{3} \tag{6}$$

The component $C_{1}$ is Spearman's rank correlation between the initial $ADMI$ and the trajectory quality of the enterprise. Trajectory quality is its $ADMI_{base}$ after five years of the uniform strategy plus $0.15\, DM_{I}$. It does not depend on $\alpha$ and $\delta$, which removes circularity. The component $C_{2}$ is the normalised Shannon entropy of the distribution of enterprises across maturity levels. The component $C_{3}$ is the share of misclassifications. A classification counts as wrong when an enterprise with a failing layer has a trajectory quality at least 8% worse than a balanced enterprise with a similar $ADMI$ but receives a level that is not lower.

Three independent runs gave $\alpha$ = 0.35, 0.40 and 0.50 and $\delta$ = 0.40, 0.35 and 0.35 (mean $\delta$ 0.367, standard deviation 0.024). The final values are the grid nodes closest to the means, that is, $\alpha = 0.40$ and $\delta = 0.375$. One of the three values of $\delta$ coincides with the upper bound of the grid, so the grid should be extended to 0.50 in the next version of the code. The criterion is least sensitive to $\delta$ of all parameters (Section 8), so this will have little effect on the final values.

## 7. Scenario results

The change in mean $ADMI$ relative to the initial value is given in Table 2. The horizons of five, ten and fifteen years were run with separate generator seeds. The initial values therefore differ by 0.01–0.02, and changes rather than levels should be compared.

**Table 2.** Change in mean $ADMI$ by scenario and horizon.

| Scenario | 5 years | 10 years | 15 years | Ratio 15/5 |
|:---|---:|---:|---:|---:|
| Inaction | −0.045 | −0.082 | −0.121 | 2.7 |
| Uniform | +0.025 | +0.046 | +0.071 | 2.9 |
| Core and staff | +0.029 | +0.054 | +0.074 | 2.6 |
| Integration breakthrough | +0.005 | +0.009 | +0.016 | 3.5 |
| Market under pressure | +0.021 | +0.035 | +0.048 | 2.3 |

*Note.* The initial values are 0.395 (5 years), 0.380 (10 years) and 0.397 (15 years). A separate five-year run starting from 0.393 gives −0.045 for inaction and +0.027 for the "core and staff" scenario. The ratio 15/5 is computed from unrounded values.

The mean stock values at the end of the fifteen-year horizon and the spread of the index across enterprises are given in Table 3. The standard deviation of $ADMI$ across 200 enterprises reflects the heterogeneity of the initial profiles rather than the uncertainty of the scenario. The standard error of the mean for this sample size is about 0.01, and differences between scenarios smaller than this value are not interpreted.

**Table 3.** Mean stock values and standard deviation of $ADMI$ at the end of 15 years by scenario.

| Scenario | C | L₁ | L₂ | L₃ | L₄ | I | SD $ADMI$ |
|:---|---:|---:|---:|---:|---:|---:|---:|
| Inaction | 0.35 | 0.31 | 0.30 | 0.27 | 0.29 | 0.27 | 0.089 |
| Uniform | 0.57 | 0.48 | 0.47 | 0.44 | 0.44 | 0.53 | 0.151 |
| Core and staff | 0.77 | 0.59 | 0.43 | 0.33 | 0.34 | 0.51 | 0.132 |
| Integration breakthrough | 0.52 | 0.44 | 0.42 | 0.39 | 0.40 | 0.80 | 0.136 |
| Market under pressure | 0.43 | 0.37 | 0.41 | 0.42 | 0.67 | 0.59 | 0.143 |

## 8. Sensitivity

Each parameter was changed by 20% in both directions under the uniform strategy on 100 enterprises (function `sensitivity_analysis`). The normalised change in criterion (6) is the absolute difference between its values at the two deviations divided by 0.4 of the baseline value. It is 0.158 for $\eta$, 0.155 for $B$, 0.051 for $\sigma$, 0.041 for $\alpha$, 0.027 for $\beta$ and 0.019 for $\delta$.

## 9. Sequence experiment

The static scenarios in Table 1 do not implement the order of layers, so the cost of deviating from it was measured separately (`src/sequence_experiment.py`). The dynamic rules choose a focal layer every quarter and direct 55% of the budget to it. The other operational layers receive 5% each, connectivity 15% and strategic readiness 10%, as in the uniform scenario. The target for all layers rises in steps of $\delta$, 0.60 and 0.80, and a rule moves to the next step when all layers have reached the previous one.

The order rule chooses the first layer in the order C → L₁ → L₂ → L₃ → L₄ that has not yet reached the target. The weakest-link rule chooses the layer with the lowest value regardless of order. The mirror rule chooses the last layer in this order that has not yet reached the target. External pressure is zero. The design is paired, that is, each rule is applied to the same 200 enterprises with the same noise seed. The run is repeated ten times with different samples (seeds 1000 + 97·k). The static "uniform" and "core and staff" scenarios are added for comparison. The results at the end of fifteen years are given in Table 4.

**Table 4.** Dynamic rules versus static scenarios, 15 years, means over 10 replications.

| Rule | $ADMI$ | $DM_{I}$ | Efficiency | C | L₁ | L₂ | L₃ | L₄ |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| Uniform (static) | 0.459 | 0.525 | 0.360 | 0.57 | 0.48 | 0.45 | 0.42 | 0.43 |
| Core and staff (static) | 0.464 | 0.505 | 0.325 | 0.78 | 0.59 | 0.42 | 0.32 | 0.33 |
| Order of layers | 0.471 | 0.539 | 0.377 | 0.58 | 0.51 | 0.47 | 0.42 | 0.41 |
| Weakest link without hierarchy | 0.460 | 0.552 | 0.381 | 0.51 | 0.45 | 0.45 | 0.45 | 0.46 |
| Mirror | 0.440 | 0.539 | 0.354 | 0.47 | 0.40 | 0.40 | 0.44 | 0.53 |

*Note.* The standard deviation of mean $ADMI$ across replications is 0.009–0.010 for all rules. In paired differences at 15 years, the order rule outperforms the mirror rule by 0.031 in $ADMI$ (95% CI from 0.030 to 0.032) and by 0.023 in integral efficiency. It outperforms the weakest-link rule by 0.011 in $ADMI$ but trails it by 0.003 in integral efficiency. The static "core and staff" scenario outperforms the uniform one by 0.005 in $ADMI$ but trails it by 0.035 in integral efficiency. The standard deviation of these differences across replications does not exceed 0.003. The intervals reflect only simulation noise under common random numbers, not the uncertainty of the model parameters.

The experiment does not test Axiom 1, because it is already built into multiplier (3). It measures the size of the order effect under the assumptions of the model.
