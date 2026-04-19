#!/usr/bin/env python3
"""
============================================================================
IM Onion-S — simulation model of digital transformation
System Dynamics backbone with Markov-chain cross-validation
============================================================================

Calibrates α (penalty strength) and δ (critical weakness threshold) of the
ADMI penalised index via a grid search over 10 runs × 1000 virtual enterprises.

Experimental design:
  - 10 runs × 1000 virtual enterprises
  - Horizon: 5 years (20 quarters, dt = 0.25)
  - Grid search: α ∈ [0.10, 1.00], δ ∈ [0.10, 0.40]
  - Combined adequacy criterion:
      C1 (0.4): Spearman correlation ADMI ↔ SD trajectory quality
      C2 (0.3): Shannon entropy of the maturity-level distribution
      C3 (0.3): misclassification rate

Part of a PhD research project. Depends only on NumPy for computation
(orchestration / exports are in the parent package).
============================================================================
"""

import numpy as np
import json
import os
import csv
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Tuple, Optional


# ═══════════════════════════════════════════════════════════════════════════
# 1. CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

CONFIG = {
    # General parameters
    "n_enterprises": 1000,       # enterprises per run
    "n_runs": 10,                # independent calibration runs
    "n_years": 5,                # simulation horizon (years)
    "dt": 0.25,                  # integration step (one quarter)
    "n_steps": 20,               # n_years / dt

    # Calibration grids for α and δ
    "alpha_range": np.arange(0.10, 1.05, 0.05),  # [0.10, 0.15, ..., 1.00]
    "delta_range": np.arange(0.10, 0.425, 0.025),  # [0.10, 0.125, ..., 0.40]

    # Weights of the combined criterion
    "w_correlation": 0.4,        # weight of trajectory-quality correlation
    "w_entropy": 0.3,            # weight of distribution entropy
    "w_misclass": 0.3,           # weight of misclassification minimisation

    # SD model parameters
    "base_depreciation": 0.025,    # base quarterly depreciation
    "investment_efficiency": 0.55, # baseline investment efficiency η
    "absorptive_saturation": 0.4,  # DM_L1 at which absorptive capacity = 1.0
    "integration_power": 0.5,      # exponent for φ(DM_I)
    "budget_total": 0.40,          # total quarterly budget (fraction of 1.0)

    # Per-layer depreciation coefficients (quarterly)
    "depreciation_by_layer": {
        "C": 0.015, "L1": 0.020, "L2": 0.025,
        "L3": 0.030, "L4": 0.025, "I": 0.020, "S": 0.010
    },

    # Budget-allocation scenarios (should sum to ≈ 1.0 each)
    "scenarios": {
        "baseline":        {"C": 0.0,  "L1": 0.0,  "L2": 0.0,  "L3": 0.0,  "L4": 0.0,  "I": 0.0,  "S": 0.0},
        "uniform":         {"C": 0.15, "L1": 0.15, "L2": 0.15, "L3": 0.15, "L4": 0.15, "I": 0.15, "S": 0.10},
        "S2_core":         {"C": 0.35, "L1": 0.25, "L2": 0.10, "L3": 0.05, "L4": 0.05, "I": 0.15, "S": 0.05},
        "S3_integration":  {"C": 0.10, "L1": 0.10, "L2": 0.10, "L3": 0.10, "L4": 0.10, "I": 0.40, "S": 0.10},
        "S4_market":       {"C": 0.05, "L1": 0.05, "L2": 0.10, "L3": 0.15, "L4": 0.30, "I": 0.20, "S": 0.15},
    },

    # External pressure (used only by the S4 scenario)
    "external_shock_year": 2,          # year at which the external shock hits
    "external_shock_magnitude": 0.15,  # extra pressure on layer L4

    # Five-level maturity scale (ADMI bucket edges)
    "maturity_thresholds": [0.0, 0.20, 0.40, 0.60, 0.80, 1.0],

    # Sensitivity (one-at-a-time)
    "sensitivity_variation": 0.20,  # ±20% perturbation

    # Legacy output dir (kept for backward compatibility; orchestrator overrides)
    "output_dir": "/tmp/simulation_results",
}

LAYER_NAMES = ["C", "L1", "L2", "L3", "L4"]
ALL_COMPONENTS = ["C", "L1", "L2", "L3", "L4", "I", "S"]

# Inner-layer hierarchy for Axiom 1 (functional reinforcement).
# Investment into layer k is bounded by the maturity of its inner layers.
INNER_LAYERS = {
    "C": [],
    "L1": ["C"],
    "L2": ["C", "L1"],
    "L3": ["C", "L1", "L2"],
    "L4": ["C", "L1", "L2", "L3"],
}


# ═══════════════════════════════════════════════════════════════════════════
# 2. ENTERPRISE GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Enterprise:
    """Virtual agri-food enterprise with a digital-maturity profile."""
    id: int
    dm: Dict[str, float] = field(default_factory=dict)  # DM_C, DM_L1, ..., DM_I, DM_S
    profile_type: str = "random"

    def dm_layers(self) -> List[float]:
        """Returns only the 5 operational layers."""
        return [self.dm[k] for k in LAYER_NAMES]

    def dm_min(self) -> float:
        """Minimum DM among the operational layers."""
        return min(self.dm_layers())

    def dm_min_layer(self) -> str:
        """Name of the layer with the lowest DM."""
        vals = {k: self.dm[k] for k in LAYER_NAMES}
        return min(vals, key=vals.get)


def generate_enterprises(n: int, rng: np.random.Generator) -> List[Enterprise]:
    """
    Generates n enterprises with a mixture of maturity profiles.

    Profile-type distribution:
      30% — balanced (all DM_i roughly equal)
      25% — single gap (one DM_i << the rest)
      20% — strong core, weak periphery
      15% — inverse (strong periphery, weak core)
      10% — fully random
    """
    enterprises = []

    type_distribution = [
        ("balanced", int(n * 0.30)),
        ("single_gap", int(n * 0.25)),
        ("strong_core", int(n * 0.20)),
        ("inverse", int(n * 0.15)),
    ]
    n_random = n - sum(count for _, count in type_distribution)
    type_distribution.append(("random", n_random))

    idx = 0
    for profile_type, count in type_distribution:
        for _ in range(count):
            dm = _generate_profile(profile_type, rng)
            enterprises.append(Enterprise(id=idx, dm=dm, profile_type=profile_type))
            idx += 1

    rng.shuffle(enterprises)
    return enterprises


def _generate_profile(profile_type: str, rng: np.random.Generator) -> Dict[str, float]:
    """Generates a DM profile for the given enterprise type."""
    dm = {}

    if profile_type == "balanced":
        base = rng.uniform(0.10, 0.70)
        noise = 0.08
        for k in ALL_COMPONENTS:
            dm[k] = np.clip(base + rng.normal(0, noise), 0.01, 0.95)

    elif profile_type == "single_gap":
        base = rng.uniform(0.25, 0.65)
        gap_layer = rng.choice(LAYER_NAMES)
        for k in ALL_COMPONENTS:
            if k == gap_layer:
                dm[k] = rng.uniform(0.01, 0.12)
            else:
                dm[k] = np.clip(base + rng.normal(0, 0.10), 0.10, 0.90)

    elif profile_type == "strong_core":
        for i, k in enumerate(LAYER_NAMES):
            # Core is strong; values decline outward
            max_val = 0.85 - i * 0.12
            min_val = max(0.05, 0.60 - i * 0.15)
            dm[k] = rng.uniform(min_val, max_val)
        dm["I"] = rng.uniform(0.15, 0.45)
        dm["S"] = rng.uniform(0.20, 0.55)

    elif profile_type == "inverse":
        for i, k in enumerate(LAYER_NAMES):
            # Weak core, strong periphery
            min_val = 0.05 + i * 0.10
            max_val = 0.30 + i * 0.15
            dm[k] = rng.uniform(min_val, max_val)
        dm["I"] = rng.uniform(0.05, 0.25)
        dm["S"] = rng.uniform(0.10, 0.40)

    elif profile_type == "random":
        for k in ALL_COMPONENTS:
            dm[k] = rng.uniform(0.02, 0.90)

    return dm


# ═══════════════════════════════════════════════════════════════════════════
# 3. ADMI CALCULATOR
# ═══════════════════════════════════════════════════════════════════════════

def compute_admi_base(dm: Dict[str, float]) -> float:
    """Step 3: base ADMI = arithmetic mean of the 5 operational layers."""
    return np.mean([dm[k] for k in LAYER_NAMES])


def compute_penalty(dm: Dict[str, float], alpha: float, delta: float) -> float:
    """Step 4: weakest-link penalty. Formula (2.5)."""
    dm_min = min(dm[k] for k in LAYER_NAMES)
    penalty = 1.0 - alpha * max(0.0, delta - dm_min)
    return max(0.0, penalty)


def compute_admi(dm: Dict[str, float], alpha: float, delta: float) -> float:
    """Full penalised ADMI. Formula (2.6)."""
    admi_base = compute_admi_base(dm)
    penalty = compute_penalty(dm, alpha, delta)
    return admi_base * penalty


def classify_maturity(admi: float) -> int:
    """Maps ADMI to a maturity level (1..5)."""
    thresholds = CONFIG["maturity_thresholds"]
    if admi <= thresholds[1]:
        return 1
    elif admi <= thresholds[2]:
        return 2
    elif admi <= thresholds[3]:
        return 3
    elif admi <= thresholds[4]:
        return 4
    else:
        return 5


# ═══════════════════════════════════════════════════════════════════════════
# 4. SYSTEM DYNAMICS MODEL
# ═══════════════════════════════════════════════════════════════════════════

def compute_system_output(dm: Dict[str, float]) -> float:
    """
    "True" integral performance of an enterprise.

    Uses a generalised mean with p = -0.5 (between the harmonic and
    geometric means). This is a softer bottleneck than the geometric mean:
    an enterprise with a "hole" in one layer performs worse but is not
    driven to zero.
    """
    layer_values = [max(dm[k], 0.001) for k in LAYER_NAMES]

    # Generalised mean with p = -0.5
    p = -0.5
    power_mean = (np.mean([v ** p for v in layer_values])) ** (1.0 / p)

    # Information-integration multiplier φ(DM_I)
    phi = dm["I"] ** CONFIG["integration_power"]

    # Strategic-readiness bonus
    strategy_bonus = 1.0 + 0.2 * dm["S"]

    return power_mean * phi * strategy_bonus


def sd_step(dm: Dict[str, float], budget_allocation: Dict[str, float],
            external_pressure: float, rng: np.random.Generator) -> Dict[str, float]:
    """
    One System Dynamics step (dt = 0.25 year = one quarter).

    For every component:
      dDM_k / dt = effective_investment_k - depreciation_k + noise

    Axiom 1: investment efficacy bounded by inner-layer maturity.
    Axiom 2: multiplier φ(DM_I).
    Absorptive capacity: C(DM_L1).
    """
    dt = CONFIG["dt"]
    budget = CONFIG["budget_total"]
    new_dm = {}

    # Absorptive capacity
    absorptive = min(1.0, dm["L1"] / CONFIG["absorptive_saturation"])

    # Integration multiplier
    phi = dm["I"] ** CONFIG["integration_power"]

    for k in ALL_COMPONENTS:
        # === Investment inflow ===
        raw_inv = budget * budget_allocation.get(k, 0.0) * CONFIG["investment_efficiency"]

        # Axiom 1: inner-layer constraint
        if k in INNER_LAYERS:
            inner = INNER_LAYERS[k]
            if inner:
                inner_mean = np.mean([dm[layer] for layer in inner])
                inner_min = min(dm[layer] for layer in inner)
                # 70% mean + 30% min (softer weakest-link effect)
                inner_factor = 0.3 + 0.7 * (0.7 * inner_mean + 0.3 * inner_min)
            else:
                inner_factor = 1.0
        else:
            # I and S are not directly bounded by the layer hierarchy
            inner_factor = 1.0

        # Axiom 2 + absorptive capacity (for operational layers)
        if k in LAYER_NAMES:
            effective_inv = raw_inv * inner_factor * absorptive * (0.5 + 0.5 * phi)
        elif k == "I":
            # Integration grows faster when layers are already developed
            harmony = 1.0 - np.std([dm[l] for l in LAYER_NAMES]) * 2
            harmony = max(0.2, harmony)
            effective_inv = raw_inv * harmony
        elif k == "S":
            # Strategic readiness depends less on technical factors
            effective_inv = raw_inv * 0.8
        else:
            effective_inv = raw_inv

        # External pressure forces extra investment into L4
        if k == "L4":
            effective_inv += external_pressure * dt * 0.5

        # === Depreciation outflow ===
        depreciation = CONFIG["depreciation_by_layer"].get(k, 0.05) * dm[k]

        # === Stochastic noise ===
        noise = rng.normal(0, 0.005)

        # === Integration step ===
        delta_dm = (effective_inv - depreciation + noise) * dt

        # Logistic ceiling: growth slows near 1.0.
        # Softer S-curve instead of a hard (1-dm) cap.
        growth_limiter = (1.0 - dm[k]) ** 0.6
        if delta_dm > 0:
            delta_dm *= growth_limiter

        new_dm[k] = np.clip(dm[k] + delta_dm, 0.001, 0.999)

    return new_dm


def simulate_enterprise(enterprise: Enterprise, scenario: str,
                        n_steps: int, rng: np.random.Generator) -> List[Dict[str, float]]:
    """
    Full SD simulation of one enterprise across n_steps quarters.
    Returns the per-step list of DM states.
    """
    allocation = CONFIG["scenarios"][scenario]
    trajectory = [enterprise.dm.copy()]
    dm = enterprise.dm.copy()

    for step in range(n_steps):
        year = step * CONFIG["dt"]

        # External pressure (S4 scenario)
        if scenario == "S4_market" and year >= CONFIG["external_shock_year"]:
            ext_pressure = CONFIG["external_shock_magnitude"]
        else:
            ext_pressure = 0.0

        dm = sd_step(dm, allocation, ext_pressure, rng)
        trajectory.append(dm.copy())

    return trajectory


# ═══════════════════════════════════════════════════════════════════════════
# 5. MARKOV CHAINS
# ═══════════════════════════════════════════════════════════════════════════

def estimate_transition_matrix(trajectories: List[List[int]], n_states: int = 5) -> np.ndarray:
    """
    Estimates a Markov transition matrix from observed level trajectories.

    Args:
        trajectories: list of level sequences (1..5) per enterprise
        n_states: number of states (5 maturity levels)

    Returns:
        Transition matrix P [n_states × n_states]
    """
    counts = np.zeros((n_states, n_states))

    for traj in trajectories:
        for t in range(len(traj) - 1):
            i = traj[t] - 1
            j = traj[t + 1] - 1
            counts[i, j] += 1

    # Row normalisation with epsilon floor to avoid absorbing states
    P = np.zeros((n_states, n_states))
    epsilon = 0.005  # minimum transition probability
    for i in range(n_states):
        row_sum = counts[i].sum()
        if row_sum > 0:
            P[i] = counts[i] / row_sum
        else:
            P[i, i] = 1.0

    # Add epsilon to neighbour transitions for ergodicity
    for i in range(n_states):
        if i > 0 and P[i, i-1] < epsilon:
            P[i, i-1] = epsilon
        if i < n_states - 1 and P[i, i+1] < epsilon:
            P[i, i+1] = epsilon
        # Renormalise
        P[i] /= P[i].sum()

    return P


def compute_stationary_distribution(P: np.ndarray) -> np.ndarray:
    """
    Stationary distribution π for transition matrix P.
    Solves πP = π subject to Σπᵢ = 1.
    """
    n = P.shape[0]
    # Find left eigenvector for eigenvalue 1
    A = P.T - np.eye(n)
    A[-1] = np.ones(n)  # replace last row with normalisation constraint
    b = np.zeros(n)
    b[-1] = 1.0

    try:
        pi = np.linalg.solve(A, b)
        pi = np.maximum(pi, 0)  # enforce non-negativity
        pi /= pi.sum()
    except np.linalg.LinAlgError:
        # Iterative fallback for singular systems
        pi = np.ones(n) / n
        for _ in range(10000):
            pi = pi @ P
        pi /= pi.sum()

    return pi


def compute_hitting_time(P: np.ndarray, start: int, target: int) -> float:
    """Expected first-hitting time from `start` to `target`."""
    n = P.shape[0]
    if start == target:
        return 0.0

    # Linear system: T_i = 1 + Σ_j P_ij * T_j for j ≠ target
    # Drop row and column for `target`
    indices = [i for i in range(n) if i != target]
    m = len(indices)
    idx_map = {old: new for new, old in enumerate(indices)}

    A = np.zeros((m, m))
    b = np.ones(m)

    for new_i, old_i in enumerate(indices):
        for new_j, old_j in enumerate(indices):
            A[new_i, new_j] = -P[old_i, old_j]
        A[new_i, new_i] += 1.0

    try:
        T = np.linalg.solve(A, b)
        if start in idx_map:
            return max(0, T[idx_map[start]])
        return 0.0
    except np.linalg.LinAlgError:
        return float('inf')


# ═══════════════════════════════════════════════════════════════════════════
# 6. CALIBRATION OF α AND δ
# ═══════════════════════════════════════════════════════════════════════════

def precompute_trajectory_quality(enterprises: List[Enterprise],
                                   rng: np.random.Generator) -> Dict[int, float]:
    """
    Pre-computes "trajectory quality" per enterprise by running SD under the
    uniform strategy.

    Trajectory quality = ADMI_base(year 5) — independent of α and δ. It
    captures real growth potential under all SD feedback loops (axioms 1–4).

    This metric breaks circularity: the ground truth does not depend on
    the very penalty mechanism we are calibrating.
    """
    quality = {}
    for e in enterprises:
        traj = simulate_enterprise(e, "uniform", CONFIG["n_steps"], rng)
        final_dm = traj[-1]
        # α,δ-independent metric: base ADMI + integration bonus
        admi_base_final = compute_admi_base(final_dm)
        integration_bonus = final_dm["I"] * 0.15
        quality[e.id] = admi_base_final + integration_bonus
    return quality


def criterion_correlation(enterprises: List[Enterprise], alpha: float, delta: float,
                          trajectory_quality: Dict[int, float]) -> float:
    """
    C1: Spearman correlation between initial ADMI(α, δ) and SD trajectory quality.

    Answers: does the penalised ADMI correctly predict which enterprises will
    perform better over a 5-year horizon?
    """
    admi_values = []
    quality_values = []

    for e in enterprises:
        if e.id not in trajectory_quality:
            continue
        admi = compute_admi(e.dm, alpha, delta)
        admi_values.append(admi)
        quality_values.append(trajectory_quality[e.id])

    # Spearman (rank) correlation
    admi_ranks = _rank_array(np.array(admi_values))
    quality_ranks = _rank_array(np.array(quality_values))

    n = len(admi_values)
    if n < 3:
        return 0.0
    d_sq = np.sum((admi_ranks - quality_ranks) ** 2)
    rho = 1.0 - (6.0 * d_sq) / (n * (n**2 - 1))

    return rho


def criterion_entropy(enterprises: List[Enterprise], alpha: float, delta: float) -> float:
    """
    C2: normalised Shannon entropy of the enterprise distribution across
    maturity levels. Maximum entropy = log2(5) ≈ 2.322, rescaled to [0, 1].
    """
    counts = np.zeros(5)
    for e in enterprises:
        admi = compute_admi(e.dm, alpha, delta)
        level = classify_maturity(admi)
        counts[level - 1] += 1

    probs = counts / counts.sum()
    probs = probs[probs > 0]
    entropy = -np.sum(probs * np.log2(probs))
    max_entropy = np.log2(5)

    return entropy / max_entropy


def criterion_misclassification(enterprises: List[Enterprise],
                                alpha: float, delta: float,
                                trajectory_quality: Dict[int, float]) -> float:
    """
    C3: share of misclassifications, verified against SD trajectories.

    A misclassification = a gap enterprise (DM_min < δ) that has WORSE
    trajectory quality than balanced peers, yet falls into the same or
    higher maturity level.

    Uses SD trajectories as ground truth instead of a static comparison.
    """
    gap_enterprises = [e for e in enterprises
                       if e.profile_type == "single_gap" and e.id in trajectory_quality]
    balanced_enterprises = [e for e in enterprises
                           if e.profile_type == "balanced" and e.id in trajectory_quality]

    if not gap_enterprises or not balanced_enterprises:
        return 0.0

    # For balanced enterprises: compute ADMI and trajectory quality
    balanced_data = []
    for be in balanced_enterprises:
        admi = compute_admi(be.dm, alpha, delta)
        quality = trajectory_quality[be.id]
        level = classify_maturity(admi)
        balanced_data.append((admi, quality, level, be))

    balanced_data.sort(key=lambda x: x[0])  # sort by ADMI

    misclass_count = 0
    total_comparisons = 0

    for ge in gap_enterprises:
        ge_admi = compute_admi(ge.dm, alpha, delta)
        ge_level = classify_maturity(ge_admi)
        ge_quality = trajectory_quality[ge.id]

        # Find the nearest balanced peer by ADMI
        best_match = None
        best_diff = float('inf')
        for b_admi, b_quality, b_level, be in balanced_data:
            diff = abs(b_admi - ge_admi)
            if diff < best_diff:
                best_diff = diff
                best_match = (b_admi, b_quality, b_level)

        if best_match and best_diff < 0.12:
            total_comparisons += 1
            b_admi, b_quality, b_level = best_match

            # Misclassification: gap enterprise has worse trajectory quality
            # BUT sits at the same or higher maturity level
            if ge_quality < b_quality * 0.92 and ge_level >= b_level:
                misclass_count += 1

    if total_comparisons == 0:
        return 0.0

    return misclass_count / total_comparisons


def combined_criterion(enterprises: List[Enterprise], alpha: float, delta: float,
                       trajectory_quality: Dict[int, float]) -> Tuple[float, float, float, float]:
    """Combined criterion: w1·C1 + w2·C2 − w3·C3. Maximised in the grid search."""
    c1 = criterion_correlation(enterprises, alpha, delta, trajectory_quality)
    c2 = criterion_entropy(enterprises, alpha, delta)
    c3 = criterion_misclassification(enterprises, alpha, delta, trajectory_quality)

    score = (CONFIG["w_correlation"] * c1
             + CONFIG["w_entropy"] * c2
             - CONFIG["w_misclass"] * c3)

    return score, c1, c2, c3


def _rank_array(arr: np.ndarray) -> np.ndarray:
    """Ranks an array (used for Spearman correlation)."""
    temp = arr.argsort()
    ranks = np.empty_like(temp, dtype=float)
    ranks[temp] = np.arange(len(arr), dtype=float)
    return ranks


# ═══════════════════════════════════════════════════════════════════════════
# 7. SENSITIVITY ANALYSIS (one-at-a-time, ±20%)
# ═══════════════════════════════════════════════════════════════════════════

def sensitivity_analysis(enterprises: List[Enterprise], optimal_alpha: float,
                         optimal_delta: float, rng: np.random.Generator,
                         trajectory_quality: Dict[int, float]) -> Dict[str, Dict[str, float]]:
    """
    Sensitivity analysis:
    - α and δ: vary ±20%, impact on the combined criterion
    - SD parameters: vary ±20%, impact on final ADMI via full SD simulation
    """
    base_score, _, _, _ = combined_criterion(enterprises, optimal_alpha, optimal_delta,
                                              trajectory_quality)

    # Baseline ADMI post-SD (for SD parameters)
    sample = enterprises[:100]  # limit for speed
    base_final_admis = _run_sd_sample(sample, optimal_alpha, optimal_delta, rng)
    base_admi_mean = float(np.mean(base_final_admis))

    results = {}
    var = CONFIG["sensitivity_variation"]

    # 1. α and δ sensitivity (via combined criterion)
    for param_name, param_value in [("alpha", optimal_alpha), ("delta", optimal_delta)]:
        low_val = param_value * (1 - var)
        high_val = param_value * (1 + var)

        if param_name == "alpha":
            score_low, _, _, _ = combined_criterion(enterprises, low_val, optimal_delta,
                                                     trajectory_quality)
            score_high, _, _, _ = combined_criterion(enterprises, high_val, optimal_delta,
                                                      trajectory_quality)
        else:
            score_low, _, _, _ = combined_criterion(enterprises, optimal_alpha, low_val,
                                                     trajectory_quality)
            score_high, _, _, _ = combined_criterion(enterprises, optimal_alpha, high_val,
                                                      trajectory_quality)

        results[param_name] = {
            "base_value": param_value,
            "low_value": low_val,
            "high_value": high_val,
            "metric": "combined_criterion",
            "base_metric": base_score,
            "metric_at_low": score_low,
            "metric_at_high": score_high,
            "sensitivity": abs(score_high - score_low) / (2 * var * abs(base_score)) if base_score != 0 else 0,
        }

    # 2. SD-parameter sensitivity (via final ADMI)
    sd_params = {
        "base_depreciation": CONFIG["base_depreciation"],
        "investment_efficiency": CONFIG["investment_efficiency"],
        "absorptive_saturation": CONFIG["absorptive_saturation"],
        "integration_power": CONFIG["integration_power"],
        "budget_total": CONFIG["budget_total"],
    }

    for param_name, param_value in sd_params.items():
        original = CONFIG[param_name]

        CONFIG[param_name] = param_value * (1 - var)
        low_admis = _run_sd_sample(sample, optimal_alpha, optimal_delta, rng)
        low_mean = float(np.mean(low_admis))

        CONFIG[param_name] = param_value * (1 + var)
        high_admis = _run_sd_sample(sample, optimal_alpha, optimal_delta, rng)
        high_mean = float(np.mean(high_admis))

        CONFIG[param_name] = original

        results[param_name] = {
            "base_value": param_value,
            "low_value": param_value * (1 - var),
            "high_value": param_value * (1 + var),
            "metric": "final_admi_mean",
            "base_metric": base_admi_mean,
            "metric_at_low": low_mean,
            "metric_at_high": high_mean,
            "sensitivity": abs(high_mean - low_mean) / (2 * var * abs(base_admi_mean)) if base_admi_mean != 0 else 0,
        }

    return results


def _run_sd_sample(enterprises: List[Enterprise], alpha: float, delta: float,
                   rng: np.random.Generator) -> List[float]:
    """Runs SD for a sample and returns final ADMI values."""
    final_admis = []
    for e in enterprises:
        traj = simulate_enterprise(e, "uniform", CONFIG["n_steps"], rng)
        final_dm = traj[-1]
        admi = compute_admi(final_dm, alpha, delta)
        final_admis.append(admi)
    return final_admis


# ═══════════════════════════════════════════════════════════════════════════
# 8. CROSS-VALIDATION (SD vs Markov)
# ═══════════════════════════════════════════════════════════════════════════

def cross_validate(enterprises: List[Enterprise], alpha: float, delta: float,
                   scenario: str, rng: np.random.Generator) -> Dict:
    """
    Cross-validation: compares SD trajectories with Markov-chain predictions.

    1. SD generates DM_i trajectories per enterprise.
    2. Trajectories are converted to ADMI and classified into levels yearly.
    3. Transition matrix P is estimated.
    4. Stationary distribution is derived.
    5. Year-5 empirical distribution is compared with the Markov prediction.
    """
    n_years = CONFIG["n_years"]
    n_steps = CONFIG["n_steps"]

    # SD simulation
    yearly_levels = []  # [enterprise][year] -> level
    final_dm = []

    for e in enterprises[:200]:  # cap for speed
        traj = simulate_enterprise(e, scenario, n_steps, rng)

        # Maturity level at the end of each year
        levels = []
        for year in range(n_years + 1):
            step_idx = min(year * int(1.0 / CONFIG["dt"]), len(traj) - 1)
            dm_at_year = traj[step_idx]
            admi = compute_admi(dm_at_year, alpha, delta)
            levels.append(classify_maturity(admi))

        yearly_levels.append(levels)
        final_dm.append(traj[-1])

    # Annual transition matrix
    annual_trajectories = []
    for levels in yearly_levels:
        annual_trajectories.append(levels)

    P = estimate_transition_matrix(annual_trajectories, n_states=5)
    stationary = compute_stationary_distribution(P)

    # Year-5 empirical distribution
    final_levels = [levels[-1] for levels in yearly_levels]
    empirical = np.zeros(5)
    for l in final_levels:
        empirical[l - 1] += 1
    empirical /= empirical.sum()

    # Markov prediction (initial distribution → P^5)
    initial_levels = [levels[0] for levels in yearly_levels]
    initial_dist = np.zeros(5)
    for l in initial_levels:
        initial_dist[l - 1] += 1
    initial_dist /= initial_dist.sum()

    markov_predicted = initial_dist.copy()
    for _ in range(n_years):
        markov_predicted = markov_predicted @ P

    # L1 deviation metric
    l1_deviation = np.sum(np.abs(empirical - markov_predicted))
    l1_stationary = np.sum(np.abs(empirical - stationary))

    # Hitting times
    hitting_times = {}
    for start in range(5):
        for target in range(start + 1, 5):
            ht = compute_hitting_time(P, start, target)
            hitting_times[f"{start+1}->{target+1}"] = round(ht, 2)

    return {
        "transition_matrix": P.tolist(),
        "stationary_distribution": stationary.tolist(),
        "empirical_distribution_year5": empirical.tolist(),
        "markov_predicted_year5": markov_predicted.tolist(),
        "initial_distribution": initial_dist.tolist(),
        "l1_deviation_predicted": round(l1_deviation, 4),
        "l1_deviation_stationary": round(l1_stationary, 4),
        "hitting_times": hitting_times,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 9. SCENARIO ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

def run_scenario_analysis(enterprises: List[Enterprise], alpha: float, delta: float,
                          rng: np.random.Generator) -> Dict[str, Dict]:
    """
    Runs all 5 scenarios over the enterprise sample.
    Returns mean ADMI trajectories and level distributions.
    """
    results = {}
    sample = enterprises[:200]  # cap for speed

    for scenario_name in CONFIG["scenarios"]:
        admi_trajectories = []
        output_trajectories = []
        level_trajectories = []
        dm_component_trajectories = {k: [] for k in ALL_COMPONENTS}

        for e in sample:
            traj = simulate_enterprise(e, scenario_name, CONFIG["n_steps"], rng)

            admi_traj = []
            output_traj = []
            level_traj = []
            dm_by_comp = {k: [] for k in ALL_COMPONENTS}

            for year in range(CONFIG["n_years"] + 1):
                step_idx = min(year * int(1.0 / CONFIG["dt"]), len(traj) - 1)
                dm = traj[step_idx]
                admi = compute_admi(dm, alpha, delta)
                output = compute_system_output(dm)
                level = classify_maturity(admi)

                admi_traj.append(admi)
                output_traj.append(output)
                level_traj.append(level)
                for k in ALL_COMPONENTS:
                    dm_by_comp[k].append(dm[k])

            admi_trajectories.append(admi_traj)
            output_trajectories.append(output_traj)
            level_trajectories.append(level_traj)
            for k in ALL_COMPONENTS:
                dm_component_trajectories[k].append(dm_by_comp[k])

        # Statistics
        admi_arr = np.array(admi_trajectories)
        output_arr = np.array(output_trajectories)
        level_arr = np.array(level_trajectories)

        # Level distribution per year
        level_distributions = []
        for year in range(CONFIG["n_years"] + 1):
            dist = np.zeros(5)
            for l in level_arr[:, year]:
                dist[int(l) - 1] += 1
            dist /= dist.sum()
            level_distributions.append(dist.tolist())

        # Per-component DM (mean over sample, per year)
        dm_components_mean = {
            k: np.mean(np.array(dm_component_trajectories[k]), axis=0).tolist()
            for k in ALL_COMPONENTS
        }

        results[scenario_name] = {
            "admi_mean": np.mean(admi_arr, axis=0).tolist(),
            "admi_std": np.std(admi_arr, axis=0).tolist(),
            "admi_median": np.median(admi_arr, axis=0).tolist(),
            "admi_p25": np.percentile(admi_arr, 25, axis=0).tolist(),
            "admi_p75": np.percentile(admi_arr, 75, axis=0).tolist(),
            "output_mean": np.mean(output_arr, axis=0).tolist(),
            "level_distributions": level_distributions,
            "dm_components_mean": dm_components_mean,
        }

    return results


# ═══════════════════════════════════════════════════════════════════════════
# 10. SINGLE-RUN CALIBRATION
# ═══════════════════════════════════════════════════════════════════════════

def run_single_calibration(run_id: int, seed: int) -> Dict:
    """
    One complete run: enterprise generation + SD trajectories + grid search (α, δ).

    Key design choice: the ground truth is computed via SD simulation ONCE
    and reused across all (α, δ) combinations. This breaks the circularity
    between the penalty mechanism and the optimality criterion.
    """
    rng = np.random.default_rng(seed)
    enterprises = generate_enterprises(CONFIG["n_enterprises"], rng)

    # Pre-compute SD trajectories (once, independent of α, δ)
    traj_quality = precompute_trajectory_quality(enterprises, rng)

    alpha_range = CONFIG["alpha_range"]
    delta_range = CONFIG["delta_range"]

    # Grid search
    grid_results = np.zeros((len(alpha_range), len(delta_range)))
    grid_c1 = np.zeros_like(grid_results)
    grid_c2 = np.zeros_like(grid_results)
    grid_c3 = np.zeros_like(grid_results)

    for i, alpha in enumerate(alpha_range):
        for j, delta in enumerate(delta_range):
            score, c1, c2, c3 = combined_criterion(enterprises, alpha, delta, traj_quality)
            grid_results[i, j] = score
            grid_c1[i, j] = c1
            grid_c2[i, j] = c2
            grid_c3[i, j] = c3

    # Locate the optimum
    best_idx = np.unravel_index(np.argmax(grid_results), grid_results.shape)
    best_alpha = float(alpha_range[best_idx[0]])
    best_delta = float(delta_range[best_idx[1]])
    best_score = float(grid_results[best_idx])

    # Statistics per profile type at the optimum
    type_stats = {}
    for ptype in ["balanced", "single_gap", "strong_core", "inverse", "random"]:
        subset = [e for e in enterprises if e.profile_type == ptype]
        if subset:
            admis = [compute_admi(e.dm, best_alpha, best_delta) for e in subset]
            levels = [classify_maturity(a) for a in admis]
            type_stats[ptype] = {
                "count": len(subset),
                "admi_mean": float(np.mean(admis)),
                "admi_std": float(np.std(admis)),
                "level_distribution": [levels.count(l) / len(levels) for l in range(1, 6)],
            }

    return {
        "run_id": run_id,
        "seed": seed,
        "best_alpha": best_alpha,
        "best_delta": best_delta,
        "best_score": best_score,
        "best_c1": float(grid_c1[best_idx]),
        "best_c2": float(grid_c2[best_idx]),
        "best_c3": float(grid_c3[best_idx]),
        "grid_scores": grid_results.tolist(),
        "grid_c1": grid_c1.tolist(),
        "grid_c2": grid_c2.tolist(),
        "grid_c3": grid_c3.tolist(),
        "type_stats": type_stats,
        "n_enterprises": len(enterprises),
    }


# ═══════════════════════════════════════════════════════════════════════════
# 11. LEGACY STANDALONE ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════
#
# The canonical entry point is `generate_report.py` at the repo root.
# `main()` below is kept for minimal backward compatibility (JSON + CSV
# outputs, English console). It does not produce xlsx or figures — use
# the orchestrator for the full report.

def main():
    """Main function: 10 runs with aggregation. Outputs JSON and CSV only."""
    print("=" * 72)
    print("  IM ONION-S — SIMULATION MODEL OF DIGITAL TRANSFORMATION")
    print("  System Dynamics + Markov chains (cross-validation)")
    print("  Calibration of α and δ")
    print("=" * 72)

    os.makedirs(CONFIG["output_dir"], exist_ok=True)
    start_time = time.time()

    # ─────────── STAGE 1: CALIBRATION OF α AND δ ───────────
    print(f"\n{'─' * 60}")
    print(f"  STAGE 1: Calibration ({CONFIG['n_runs']} runs × "
          f"{CONFIG['n_enterprises']} enterprises)")
    print(f"{'─' * 60}")

    all_runs = []
    all_alphas = []
    all_deltas = []

    for run_id in range(CONFIG["n_runs"]):
        seed = 42 + run_id * 137
        print(f"  Run {run_id + 1}/{CONFIG['n_runs']} (seed={seed})...",
              end=" ", flush=True)

        result = run_single_calibration(run_id, seed)
        all_runs.append(result)
        all_alphas.append(result["best_alpha"])
        all_deltas.append(result["best_delta"])

        print(f"α={result['best_alpha']:.3f}, δ={result['best_delta']:.3f}, "
              f"score={result['best_score']:.4f}")

    # Aggregated results
    mean_alpha = float(np.mean(all_alphas))
    std_alpha = float(np.std(all_alphas))
    median_alpha = float(np.median(all_alphas))

    mean_delta = float(np.mean(all_deltas))
    std_delta = float(np.std(all_deltas))
    median_delta = float(np.median(all_deltas))

    # Snap to the nearest grid step
    final_alpha = float(CONFIG["alpha_range"][np.argmin(np.abs(CONFIG["alpha_range"] - mean_alpha))])
    final_delta = float(CONFIG["delta_range"][np.argmin(np.abs(CONFIG["delta_range"] - mean_delta))])

    print(f"\n  ╔══════════════════════════════════════════════════════╗")
    print(f"  ║  CALIBRATION RESULT ({CONFIG['n_runs']} runs)                          ║")
    print(f"  ╠══════════════════════════════════════════════════════╣")
    print(f"  ║  α: mean = {mean_alpha:.4f} ± {std_alpha:.4f}   median = {median_alpha:.4f}     ║")
    print(f"  ║  δ: mean = {mean_delta:.4f} ± {std_delta:.4f}   median = {median_delta:.4f}     ║")
    print(f"  ║                                                      ║")
    print(f"  ║  FINAL VALUES: α = {final_alpha:.2f}, δ = {final_delta:.3f}              ║")
    print(f"  ╚══════════════════════════════════════════════════════╝")

    # ─────────── STAGE 2: SCENARIO ANALYSIS ───────────
    print(f"\n{'─' * 60}")
    print(f"  STAGE 2: Scenario analysis (5 scenarios × 5 years)")
    print(f"{'─' * 60}")

    rng_scenario = np.random.default_rng(12345)
    scenario_enterprises = generate_enterprises(CONFIG["n_enterprises"], rng_scenario)
    scenario_results = run_scenario_analysis(scenario_enterprises, final_alpha,
                                              final_delta, rng_scenario)

    for name, data in scenario_results.items():
        admi_start = data["admi_mean"][0]
        admi_end = data["admi_mean"][-1]
        change = admi_end - admi_start
        print(f"  {name:20s}: ADMI {admi_start:.3f} → {admi_end:.3f} "
              f"(Δ = {change:+.3f})")

    # ─────────── STAGE 3: CROSS-VALIDATION ───────────
    print(f"\n{'─' * 60}")
    print(f"  STAGE 3: Cross-validation SD ↔ Markov chains")
    print(f"{'─' * 60}")

    rng_cv = np.random.default_rng(54321)
    cv_enterprises = generate_enterprises(CONFIG["n_enterprises"], rng_cv)

    # Pre-compute trajectory quality for cross-validation and sensitivity
    print(f"  Computing SD trajectories for cross-validation...", flush=True)
    cv_trajectory_quality = precompute_trajectory_quality(cv_enterprises, rng_cv)

    cv_results = {}
    for scenario_name in ["uniform", "S2_core", "S3_integration"]:
        cv = cross_validate(cv_enterprises, final_alpha, final_delta,
                           scenario_name, rng_cv)
        cv_results[scenario_name] = cv

        print(f"\n  Scenario: {scenario_name}")
        print(f"    Transition matrix (annual):")
        P = np.array(cv["transition_matrix"])
        for row_idx in range(5):
            row_str = "    " + " ".join(f"{P[row_idx, j]:.3f}" for j in range(5))
            print(row_str)

        print(f"    Stationary distribution: {[f'{x:.3f}' for x in cv['stationary_distribution']]}")
        print(f"    Empirical (year 5):      {[f'{x:.3f}' for x in cv['empirical_distribution_year5']]}")
        print(f"    Markov predicted (y 5):  {[f'{x:.3f}' for x in cv['markov_predicted_year5']]}")
        print(f"    L1 deviation (predicted):  {cv['l1_deviation_predicted']:.4f}")
        print(f"    L1 deviation (stationary): {cv['l1_deviation_stationary']:.4f}")

        if cv["hitting_times"]:
            print(f"    Expected hitting times (years):")
            for transition, ht_time in cv["hitting_times"].items():
                if ht_time < 100:
                    print(f"      {transition}: {ht_time:.1f}")

    # ─────────── STAGE 4: SENSITIVITY ANALYSIS ───────────
    print(f"\n{'─' * 60}")
    print(f"  STAGE 4: Sensitivity analysis (OAT ±20%)")
    print(f"{'─' * 60}")

    sensitivity = sensitivity_analysis(cv_enterprises, final_alpha, final_delta,
                                      rng_cv, cv_trajectory_quality)

    print(f"  {'Parameter':30s} {'Base':>8s} {'Metric-':>8s} {'Metric+':>8s} {'Sens.':>8s}")
    print(f"  {'─' * 62}")
    sorted_params = sorted(sensitivity.items(), key=lambda x: x[1]["sensitivity"], reverse=True)
    for param_name, data in sorted_params:
        print(f"  {param_name:30s} {data['base_value']:8.4f} "
              f"{data['metric_at_low']:8.4f} {data['metric_at_high']:8.4f} "
              f"{data['sensitivity']:8.4f}")

    # ─────────── RESULT PERSISTENCE ───────────
    elapsed = time.time() - start_time
    print(f"\n{'─' * 60}")
    print(f"  SAVING RESULTS")
    print(f"{'─' * 60}")

    # Aggregated report
    report = {
        "calibration": {
            "final_alpha": final_alpha,
            "final_delta": final_delta,
            "mean_alpha": mean_alpha,
            "std_alpha": std_alpha,
            "median_alpha": median_alpha,
            "mean_delta": mean_delta,
            "std_delta": std_delta,
            "median_delta": median_delta,
            "all_alphas": all_alphas,
            "all_deltas": all_deltas,
            "individual_runs": [
                {
                    "run_id": r["run_id"],
                    "best_alpha": r["best_alpha"],
                    "best_delta": r["best_delta"],
                    "best_score": r["best_score"],
                    "c1_correlation": r["best_c1"],
                    "c2_entropy": r["best_c2"],
                    "c3_misclass": r["best_c3"],
                    "type_stats": r["type_stats"],
                }
                for r in all_runs
            ],
        },
        "scenarios": scenario_results,
        "cross_validation": cv_results,
        "sensitivity": {k: v for k, v in sensitivity.items()},
        "config": {
            "n_enterprises": CONFIG["n_enterprises"],
            "n_runs": CONFIG["n_runs"],
            "n_years": CONFIG["n_years"],
            "dt": CONFIG["dt"],
            "w_correlation": CONFIG["w_correlation"],
            "w_entropy": CONFIG["w_entropy"],
            "w_misclass": CONFIG["w_misclass"],
        },
        "execution_time_seconds": round(elapsed, 1),
    }

    # JSON
    report_path = os.path.join(CONFIG["output_dir"], "simulation_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    print(f"  Full report: {report_path}")

    # CSV with per-run calibration results
    csv_path = os.path.join(CONFIG["output_dir"], "calibration_runs.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["run_id", "seed", "best_alpha", "best_delta",
                        "best_score", "c1", "c2", "c3"])
        for r in all_runs:
            writer.writerow([r["run_id"], r["seed"], r["best_alpha"],
                           r["best_delta"], f"{r['best_score']:.6f}",
                           f"{r['best_c1']:.6f}", f"{r['best_c2']:.6f}",
                           f"{r['best_c3']:.6f}"])
    print(f"  Calibration CSV: {csv_path}")

    # CSV with heatmap (averaged across runs)
    avg_grid = np.mean([np.array(r["grid_scores"]) for r in all_runs], axis=0)
    heatmap_path = os.path.join(CONFIG["output_dir"], "heatmap_combined.csv")
    with open(heatmap_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        header = ["alpha\\delta"] + [f"{d:.3f}" for d in CONFIG["delta_range"]]
        writer.writerow(header)
        for i, alpha in enumerate(CONFIG["alpha_range"]):
            row = [f"{alpha:.2f}"] + [f"{avg_grid[i, j]:.6f}"
                                       for j in range(len(CONFIG["delta_range"]))]
            writer.writerow(row)
    print(f"  Heatmap CSV: {heatmap_path}")

    # CSV with scenario trajectories
    traj_path = os.path.join(CONFIG["output_dir"], "scenario_trajectories.csv")
    with open(traj_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["scenario", "year", "admi_mean", "admi_std",
                        "admi_median", "admi_p25", "admi_p75",
                        "output_mean", "level_dist_1", "level_dist_2",
                        "level_dist_3", "level_dist_4", "level_dist_5"])
        for sname, sdata in scenario_results.items():
            for year in range(CONFIG["n_years"] + 1):
                ld = sdata["level_distributions"][year]
                writer.writerow([sname, year,
                               f"{sdata['admi_mean'][year]:.6f}",
                               f"{sdata['admi_std'][year]:.6f}",
                               f"{sdata['admi_median'][year]:.6f}",
                               f"{sdata['admi_p25'][year]:.6f}",
                               f"{sdata['admi_p75'][year]:.6f}",
                               f"{sdata['output_mean'][year]:.6f}",
                               ] + [f"{x:.4f}" for x in ld])
    print(f"  Scenarios CSV: {traj_path}")

    print(f"\n  Elapsed: {elapsed:.1f} seconds")
    print(f"\n{'═' * 72}")
    print(f"  SIMULATION COMPLETE")
    print(f"{'═' * 72}")

    return report


if __name__ == "__main__":
    main()
