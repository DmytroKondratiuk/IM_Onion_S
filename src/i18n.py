"""
Centralised labels and translations (uk / en) for the whole pipeline.

Usage:
    from i18n import get_labels
    L = get_labels("uk")   # or "en"
    print(L["step_1_calibration"])

Adding a new language: copy one of the dictionaries below, translate the
values, and register it in `_LABELS` at the bottom of this file.
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────
# Ukrainian labels (user-facing; do not translate values into English)
# ─────────────────────────────────────────────────────────────────────

UK = {
    # ── Console messages ──
    "lang_prompt":        "Оберіть мову виводу / Select output language "
                          "[uk / en] (default: uk): ",
    "lang_invalid":       "Невідомий код мови. Використовую 'uk'.",
    "lang_confirmed":     "Мова: українська",
    "quick_mode":         "⚡ Швидкий режим: n_enterprises=200, n_runs=3",
    "pipeline_title":     "ІМІТАЦІЙНЕ МОДЕЛЮВАННЯ ІМ ONION-S — повний звіт",
    "step_1_calibration": "[1/5] Калібрація α, δ",
    "step_2_scenarios":   "[2/5] Сценарний аналіз",
    "step_3_crossval":    "[3/5] Крос-валідація SD vs Маркова",
    "step_4_sensitivity": "[4/5] Аналіз чутливості (OAT ±20%)",
    "step_5_multihorizon": "[5/5] Багатогоризонтний аналіз (5/10/15 років)",
    "step_5_skipped":     "[5/5] Багатогоризонтний аналіз пропущено (--no-multi)",
    "final_alpha_delta":  "→ Фінальне: α={a:.2f}, δ={d:.3f}",
    "cycle_done":         "Основний цикл завершено за {t:.1f} с",
    "report_complete":    "ЗВІТ ЗАВЕРШЕНО",
    "sf_generating":      "Генерація Stock-and-Flow діаграми...",
    "heatmap_exporting":  "Експорт heatmap-ів у PNG...",
    "charts_exporting":   "Експорт основних графіків у PNG...",
    "xlsx_exporting":     "Експорт xlsx...",
    "json_saved":         "JSON: {path}",
    "xlsx_saved":         "xlsx: {path}",
    "horizons_years":     "Горизонт {h} років...",

    # ── Scenarios ──
    "scenario_baseline":        "Бездіяльність",
    "scenario_uniform":         "Рівномірна",
    "scenario_S2_core":         "С-2 Ядро",
    "scenario_S3_integration":  "С-3 Інтеграція",
    "scenario_S4_market":       "С-4 Ринкова",

    # ── Maturity level names ──
    "level_1_short": "1\nаналог.",
    "level_2_short": "2\nфрагм.",
    "level_3_short": "3\nінтегр.",
    "level_4_short": "4\nадапт.",
    "level_5_short": "5\nінтел.",
    "level_1_full":  "1 (аналоговий)",
    "level_2_full":  "2 (фрагментарний)",
    "level_3_full":  "3 (інтегрований)",
    "level_4_full":  "4 (адаптивний)",
    "level_5_full":  "5 (інтелектуальний)",
    "level_prefix":  "Рівень",

    # ── Chart axes and legends ──
    "ax_year":            "Рік",
    "ax_admi":            "ADMI",
    "ax_delta_admi":      "Δ ADMI",
    "ax_scenario":        "Сценарій",
    "ax_level":           "Рівень",
    "ax_parameter":       "Параметр",
    "ax_sensitivity":     "Чутливість (варіація метрики)",
    "ax_from_level":      "З рівня",
    "ax_to_level":        "На рівень",
    "ax_transition_prob": "Ймовірність переходу",
    "ax_enterprise_share": "Частка підприємств",
    "ax_alpha":           "α (сила штрафу)",
    "ax_delta":           "δ (поріг критичної слабкості)",
    "legend_sd_empirical":    "SD (емпіричний)",
    "legend_markov_predicted": "Маркова (прогноз)",
    "legend_horizon_years":    "{h} років",

    # ── xlsx sheet names ──
    "sheet_metadata":          "Про звіт",
    "sheet_calibration":       "Калібрація",
    "sheet_calib_heatmap":     "Теплова карта J(α,δ)",
    "sheet_degradation":       "Деградація",
    "sheet_scenarios_admi":    "Сценарії ADMI",
    "sheet_scenarios_dm":      "Сценарії DM компоненти",
    "sheet_level_dist":        "Рівні розподіл",
    "sheet_markov_uniform":    "Матриця Маркова С-1",
    "sheet_markov_S2_core":    "Матриця Маркова С-2",
    "sheet_markov_S3_integration": "Матриця Маркова С-3",
    "sheet_markov_S4_market":  "Матриця Маркова С-4",
    "sheet_stationary":        "Стаціонарні розподіли",
    "sheet_hitting_times":     "Час досягнення рівня",
    "sheet_multihorizon":      "Багатогоризонтний",
    "sheet_crossval":          "Крос-валідація",
    "sheet_sensitivity":       "Чутливість",
    "sheet_fig_trajectories":  "Рис. Траєкторії ADMI",
    "sheet_fig_profiles":      "Рис. Профілі DM",
    "sheet_fig_multihorizon":  "Рис. Багатогоризонтний",
    "sheet_fig_crossval":      "Рис. Крос-валідація",
    "sheet_fig_sensitivity":   "Рис. Чутливість",

    # ── Sheet / table titles ──
    "title_metadata":    "Про звіт імітаційного моделювання ІМ Onion-S",
    "title_calibration": "Табл. 2.10. Калібрація α та δ (10 запусків × 1000 підприємств)",
    "title_calib_heatmap": "Теплова карта J(α, δ) — середнє по 10 запусках",
    "title_degradation": "Табл. 2.9. Коефіцієнти деградації компонентів (за квартал)",
    "title_scenarios_admi": "Траєкторії ADMI за сценаріями (5 років, mean/std/median/p25/p75)",
    "title_scenarios_dm":   "Покомпонентні DM за сценаріями (середнє, по роках)",
    "title_level_dist":     "Розподіл підприємств по рівнях (за сценаріями та роками)",
    "title_markov":         "Матриця переходу Маркова — {scenario} (річна)",
    "title_stationary":     "Стаціонарні розподіли π за сценаріями",
    "title_hitting_times":  "Табл. 2.16. Очікуваний час досягнення рівня (роки)",
    "title_multihorizon":   "Табл. 2.13. ΔADMI за горизонтами та сценаріями (повні дані)",
    "title_crossval":       "Табл. 2.14. Крос-валідація SD vs Ланцюги Маркова (рік 5)",
    "title_sensitivity":    "Табл. 2.17. Аналіз чутливості (OAT ±20%)",
    "title_fig_trajectories":  "Рис. 2.3.2. Траєкторії ADMI за сценаріями (5 років)",
    "title_fig_profiles":      "Рис. 2.3.3. Профілі DM за сценаріями (рік 5, radar)",
    "title_fig_multihorizon":  "Рис. 2.3.4. ΔADMI за горизонтами (5/10/15 років)",
    "title_fig_crossval":      "Рис. 2.3.5. Крос-валідація SD vs Маркова (Рівномірна, рік 5)",
    "title_fig_sensitivity":   "Рис. 2.3.7. Аналіз чутливості (tornado, OAT ±20%)",

    # ── Column headers ──
    "col_run":              "Запуск",
    "col_seed":             "seed",
    "col_mean":             "Середнє",
    "col_stdev":            "Ст. відхилення",
    "col_alpha_delta":      "α \\ δ",
    "col_component":        "Компонент",
    "col_dk":               "d_k",
    "col_justification":    "Обґрунтування",
    "col_sd_empirical":     "SD (емпіричний)",
    "col_markov_predicted": "Маркова (прогноз)",
    "col_difference_pp":    "Різниця (в.п.)",
    "col_transition":       "Перехід",
    "col_from_to_level":    "З рівня / На рівень",
    "col_start":            "Старт",
    "col_base_value":       "Базове",
    "col_metric_low":       "Метрика @ -20%",
    "col_metric_high":      "Метрика @ +20%",
    "col_sensitivity":      "Чутливість",
    "col_delta_admi_5":     "ΔADMI(5)",
    "col_delta_admi_10":    "ΔADMI(10)",
    "col_delta_admi_15":    "ΔADMI(15)",
    "col_ratio_15_5":       "Кратність 15/5",
    "col_admi_start":       "ADMI(0)",
    "col_admi_end_5":       "ADMI(5)",
    "col_level_change":     "Рівень(0) → Рівень(5)",
    "col_horizon_5":        "5 років",
    "col_horizon_10":       "10 років",
    "col_horizon_15":       "15 років",
    "col_l1_deviation":     "L1-відхилення",

    # ── Metadata fields (for the "About" sheet) ──
    "meta_run_date":        "Дата запуску",
    "meta_final_alpha":     "Фінальне α",
    "meta_final_delta":     "Фінальне δ",
    "meta_mean_alpha":      "Середнє α (10 запусків)",
    "meta_mean_delta":      "Середнє δ (10 запусків)",
    "meta_n_enterprises":   "Кількість підприємств",
    "meta_n_runs":          "Кількість запусків",
    "meta_horizon":         "Горизонт (років)",
    "meta_step":            "Крок (років)",
    "meta_exec_time":       "Час виконання (с)",

    # ── Source attribution ──
    "source_simulation":    "Джерело: імітаційне моделювання, {ts}",
    "source_developed":     "Джерело: розроблено автором; {ts}",
    "source_multihorizon":  "Джерело: багатогоризонтне моделювання, {ts}",
    "source_crossval":      "Джерело: імітаційне моделювання, {ts}. "
                            "L1-відхилення: {l1:.4f}",
    "source_crossval_full": "Джерело: імітаційне моделювання, {ts}",
    "source_hitting":       "Джерело: імітаційне моделювання, {ts}. "
                            "«–» означає очікуваний час > 100 років.",

    # ── Rationales for d_k coefficients ──
    "reason_C":  "Виробнича компетенція змінюється повільно",
    "reason_L1": "Плинність кадрів, втрата компетенцій",
    "reason_L2": "Застарівання облікових систем",
    "reason_L3": "Швидка зміна технологій GPS/IoT",
    "reason_L4": "Зміна вимог ринку та регуляторів",
    "reason_I":  "Накопичення несумісностей між системами",
    "reason_S":  "Стратегічна свідомість зберігається довше",
    "comp_name_C":  "C (ядро)",
    "comp_name_L1": "L₁ (HR)",
    "comp_name_L2": "L₂ (матеріали)",
    "comp_name_L3": "L₃ (логістика)",
    "comp_name_L4": "L₄ (збут)",
    "comp_name_I":  "I (інтеграція)",
    "comp_name_S":  "S (стратегія)",

    # ── Stock-and-Flow diagram ──
    "sf_stock_C":  "DM_C\n(ядро)",
    "sf_stock_L1": "DM_L₁\n(HR)",
    "sf_stock_L2": "DM_L₂\n(матеріали)",
    "sf_stock_L3": "DM_L₃\n(логістика)",
    "sf_stock_L4": "DM_L₄\n(збут)",
    "sf_stock_I":  "DM_I\n(інтеграція)",
    "sf_stock_S":  "DM_S\n(стратегія)",
    "sf_modif_F":   "F_k^inner\nаксіома 1",
    "sf_modif_A":   "A(t)\nпоглин. зд.",
    "sf_modif_Phi": "Φ(t)\nаксіома 2",
    "sf_modif_G":   "G_k(t)\nлогіст. обмеж.",
    "sf_modif_E":   "E(t)\nзовн. тиск",
    "sf_legend_stock":    "Запас (DM_k)",
    "sf_legend_inflow":   "Інфлов (EI_k)",
    "sf_legend_outflow":  "Аутфлов (D_k)",
    "sf_legend_modifier": "Модифікатор",
    "sf_loops_title":     "Контури зворотного звʼязку:",
    "sf_loop_R1":         "R1 (+): DM_I → Φ → EI_k → DM_k → ... → DM_I",
    "sf_loop_B1":         "B1 (−): DM_k → G(DM_k) → EI_k (обмеж. росту)",
    "sf_loop_B2":         "B2 (−): DM_L1 → A → EI_k (поглин. зд.)",
    "sf_loop_B3":         "B3 (−): внутр. шари → F → EI зовн. шарів",

    # ── Misc ──
    "n_a":                  "n/a",
    "dash":                 "–",
}


# ─────────────────────────────────────────────────────────────────────
# English labels
# ─────────────────────────────────────────────────────────────────────

EN = {
    # ── Console ──
    "lang_prompt":        "Оберіть мову виводу / Select output language "
                          "[uk / en] (default: uk): ",
    "lang_invalid":       "Unknown language code. Using 'uk'.",
    "lang_confirmed":     "Language: English",
    "quick_mode":         "⚡ Quick mode: n_enterprises=200, n_runs=3",
    "pipeline_title":     "ONION-S SIMULATION MODEL — full report",
    "step_1_calibration": "[1/5] Calibration of α, δ",
    "step_2_scenarios":   "[2/5] Scenario analysis",
    "step_3_crossval":    "[3/5] Cross-validation SD vs Markov",
    "step_4_sensitivity": "[4/5] Sensitivity analysis (OAT ±20%)",
    "step_5_multihorizon": "[5/5] Multi-horizon analysis (5/10/15 years)",
    "step_5_skipped":     "[5/5] Multi-horizon analysis skipped (--no-multi)",
    "final_alpha_delta":  "→ Final: α={a:.2f}, δ={d:.3f}",
    "cycle_done":         "Main cycle completed in {t:.1f} s",
    "report_complete":    "REPORT COMPLETED",
    "sf_generating":      "Generating Stock-and-Flow diagram...",
    "heatmap_exporting":  "Exporting heatmaps to PNG...",
    "charts_exporting":   "Exporting main charts to PNG...",
    "xlsx_exporting":     "Exporting xlsx...",
    "json_saved":         "JSON: {path}",
    "xlsx_saved":         "xlsx: {path}",
    "horizons_years":     "Horizon {h} years...",

    # ── Scenarios ──
    "scenario_baseline":        "Inactivity",
    "scenario_uniform":         "Uniform",
    "scenario_S2_core":         "S-2 Core",
    "scenario_S3_integration":  "S-3 Integration",
    "scenario_S4_market":       "S-4 Market",

    # ── Maturity levels ──
    "level_1_short": "1\nanalog",
    "level_2_short": "2\nfragm.",
    "level_3_short": "3\nintegr.",
    "level_4_short": "4\nadapt.",
    "level_5_short": "5\nintell.",
    "level_1_full":  "1 (analog)",
    "level_2_full":  "2 (fragmented)",
    "level_3_full":  "3 (integrated)",
    "level_4_full":  "4 (adaptive)",
    "level_5_full":  "5 (intelligent)",
    "level_prefix":  "Level",

    # ── Axes & legends ──
    "ax_year":            "Year",
    "ax_admi":            "ADMI",
    "ax_delta_admi":      "Δ ADMI",
    "ax_scenario":        "Scenario",
    "ax_level":           "Level",
    "ax_parameter":       "Parameter",
    "ax_sensitivity":     "Sensitivity (metric variation)",
    "ax_from_level":      "From level",
    "ax_to_level":        "To level",
    "ax_transition_prob": "Transition probability",
    "ax_enterprise_share": "Enterprise share",
    "ax_alpha":           "α (penalty strength)",
    "ax_delta":           "δ (critical weakness threshold)",
    "legend_sd_empirical":    "SD (empirical)",
    "legend_markov_predicted": "Markov (predicted)",
    "legend_horizon_years":    "{h} years",

    # ── xlsx sheet names ──
    "sheet_metadata":          "Metadata",
    "sheet_calibration":       "Calibration",
    "sheet_calib_heatmap":     "Heatmap J(α,δ)",
    "sheet_degradation":       "Degradation",
    "sheet_scenarios_admi":    "Scenarios ADMI",
    "sheet_scenarios_dm":      "Scenarios DM",
    "sheet_level_dist":        "Level distribution",
    "sheet_markov_uniform":    "Markov S-1",
    "sheet_markov_S2_core":    "Markov S-2",
    "sheet_markov_S3_integration": "Markov S-3",
    "sheet_markov_S4_market":  "Markov S-4",
    "sheet_stationary":        "Stationary distrib.",
    "sheet_hitting_times":     "Hitting times",
    "sheet_multihorizon":      "Multi-horizon",
    "sheet_crossval":          "Cross-validation",
    "sheet_sensitivity":       "Sensitivity",
    "sheet_fig_trajectories":  "Fig. ADMI trajectories",
    "sheet_fig_profiles":      "Fig. DM profiles",
    "sheet_fig_multihorizon":  "Fig. Multi-horizon",
    "sheet_fig_crossval":      "Fig. Cross-validation",
    "sheet_fig_sensitivity":   "Fig. Sensitivity",

    # ── Sheet / table titles ──
    "title_metadata":    "Onion-S simulation model report",
    "title_calibration": "Table 2.10. Calibration of α and δ (10 runs × 1000 enterprises)",
    "title_calib_heatmap": "Heatmap J(α, δ) — averaged over 10 runs",
    "title_degradation": "Table 2.9. Depreciation coefficients d_k (per quarter)",
    "title_scenarios_admi": "ADMI trajectories by scenario (5 years, mean/std/median/p25/p75)",
    "title_scenarios_dm":   "Per-component DM by scenario (mean, by year)",
    "title_level_dist":     "Enterprise distribution by level (by scenario and year)",
    "title_markov":         "Markov transition matrix — {scenario} (annual)",
    "title_stationary":     "Stationary distributions π by scenario",
    "title_hitting_times":  "Table 2.16. Expected time to reach level (years)",
    "title_multihorizon":   "Table 2.13. ΔADMI by horizons and scenarios (full data)",
    "title_crossval":       "Table 2.14. Cross-validation SD vs Markov chains (year 5)",
    "title_sensitivity":    "Table 2.17. Sensitivity analysis (OAT ±20%)",
    "title_fig_trajectories":  "Fig. 2.3.2. ADMI trajectories by scenario (5 years)",
    "title_fig_profiles":      "Fig. 2.3.3. DM profiles by scenario (year 5, radar)",
    "title_fig_multihorizon":  "Fig. 2.3.4. ΔADMI by horizons (5/10/15 years)",
    "title_fig_crossval":      "Fig. 2.3.5. Cross-validation SD vs Markov (Uniform, year 5)",
    "title_fig_sensitivity":   "Fig. 2.3.7. Sensitivity analysis (tornado, OAT ±20%)",

    # ── Column headers ──
    "col_run":              "Run",
    "col_seed":             "seed",
    "col_mean":             "Mean",
    "col_stdev":            "StDev",
    "col_alpha_delta":      "α \\ δ",
    "col_component":        "Component",
    "col_dk":               "d_k",
    "col_justification":    "Justification",
    "col_sd_empirical":     "SD (empirical)",
    "col_markov_predicted": "Markov (predicted)",
    "col_difference_pp":    "Difference (pp)",
    "col_transition":       "Transition",
    "col_from_to_level":    "From / To level",
    "col_start":            "Start",
    "col_base_value":       "Base",
    "col_metric_low":       "Metric @ -20%",
    "col_metric_high":      "Metric @ +20%",
    "col_sensitivity":      "Sensitivity",
    "col_delta_admi_5":     "ΔADMI(5)",
    "col_delta_admi_10":    "ΔADMI(10)",
    "col_delta_admi_15":    "ΔADMI(15)",
    "col_ratio_15_5":       "Ratio 15/5",
    "col_admi_start":       "ADMI(0)",
    "col_admi_end_5":       "ADMI(5)",
    "col_level_change":     "Level(0) → Level(5)",
    "col_horizon_5":        "5 years",
    "col_horizon_10":       "10 years",
    "col_horizon_15":       "15 years",
    "col_l1_deviation":     "L1-deviation",

    # ── Metadata fields ──
    "meta_run_date":        "Run date",
    "meta_final_alpha":     "Final α",
    "meta_final_delta":     "Final δ",
    "meta_mean_alpha":      "Mean α (10 runs)",
    "meta_mean_delta":      "Mean δ (10 runs)",
    "meta_n_enterprises":   "Number of enterprises",
    "meta_n_runs":          "Number of runs",
    "meta_horizon":         "Horizon (years)",
    "meta_step":            "Step (years)",
    "meta_exec_time":       "Execution time (s)",

    # ── Source attribution ──
    "source_simulation":    "Source: simulation results, {ts}",
    "source_developed":     "Source: developed by the author; {ts}",
    "source_multihorizon":  "Source: multi-horizon simulation, {ts}",
    "source_crossval":      "Source: simulation results, {ts}. "
                            "L1-deviation: {l1:.4f}",
    "source_crossval_full": "Source: simulation results, {ts}",
    "source_hitting":       "Source: simulation results, {ts}. "
                            "«–» means expected time > 100 years.",

    # ── Depreciation reasons ──
    "reason_C":  "Production competence changes slowly",
    "reason_L1": "Staff turnover, loss of competencies",
    "reason_L2": "Obsolescence of accounting systems",
    "reason_L3": "Fast changes in GPS/IoT technologies",
    "reason_L4": "Changes in market and regulatory requirements",
    "reason_I":  "Accumulating incompatibilities between systems",
    "reason_S":  "Strategic awareness persists longer",
    "comp_name_C":  "C (core)",
    "comp_name_L1": "L₁ (HR)",
    "comp_name_L2": "L₂ (materials)",
    "comp_name_L3": "L₃ (logistics)",
    "comp_name_L4": "L₄ (sales)",
    "comp_name_I":  "I (integration)",
    "comp_name_S":  "S (strategy)",

    # ── Stock-and-Flow diagram ──
    "sf_stock_C":  "DM_C\n(core)",
    "sf_stock_L1": "DM_L₁\n(HR)",
    "sf_stock_L2": "DM_L₂\n(materials)",
    "sf_stock_L3": "DM_L₃\n(logistics)",
    "sf_stock_L4": "DM_L₄\n(sales)",
    "sf_stock_I":  "DM_I\n(integration)",
    "sf_stock_S":  "DM_S\n(strategy)",
    "sf_modif_F":   "F_k^inner\naxiom 1",
    "sf_modif_A":   "A(t)\nabsorptive cap.",
    "sf_modif_Phi": "Φ(t)\naxiom 2",
    "sf_modif_G":   "G_k(t)\nlogistic limit",
    "sf_modif_E":   "E(t)\nexternal pressure",
    "sf_legend_stock":    "Stock (DM_k)",
    "sf_legend_inflow":   "Inflow (EI_k)",
    "sf_legend_outflow":  "Outflow (D_k)",
    "sf_legend_modifier": "Modifier",
    "sf_loops_title":     "Feedback loops:",
    "sf_loop_R1":         "R1 (+): DM_I → Φ → EI_k → DM_k → ... → DM_I",
    "sf_loop_B1":         "B1 (−): DM_k → G(DM_k) → EI_k (growth limit)",
    "sf_loop_B2":         "B2 (−): DM_L1 → A → EI_k (absorptive cap.)",
    "sf_loop_B3":         "B3 (−): inner layers → F → EI outer layers",

    # ── Misc ──
    "n_a":                  "n/a",
    "dash":                 "–",
}


_LABELS = {"uk": UK, "en": EN}


def get_labels(lang: str = "uk") -> dict:
    """Returns the full labels dict for the given language; fallback to uk."""
    return _LABELS.get(lang, UK)


def prompt_language() -> str:
    """Interactive prompt — returns 'uk' or 'en'."""
    raw = input(UK["lang_prompt"]).strip().lower()
    if raw in ("en", "english", "e"):
        return "en"
    if raw in ("uk", "ua", "ukrainian", "українська", "u", ""):
        return "uk"
    print(UK["lang_invalid"])
    return "uk"


SCENARIO_KEY_MAP = {
    "baseline":        "scenario_baseline",
    "uniform":         "scenario_uniform",
    "S2_core":         "scenario_S2_core",
    "S3_integration":  "scenario_S3_integration",
    "S4_market":       "scenario_S4_market",
}


def scenario_label(key: str, labels: dict) -> str:
    """Translates a scenario key (baseline, uniform, ...) via labels dict."""
    return labels.get(SCENARIO_KEY_MAP.get(key, ""), key)


LEVEL_FULL_KEYS = ["level_1_full", "level_2_full", "level_3_full",
                   "level_4_full", "level_5_full"]
LEVEL_SHORT_KEYS = ["level_1_short", "level_2_short", "level_3_short",
                    "level_4_short", "level_5_short"]


def levels_full(labels: dict) -> list:
    return [labels[k] for k in LEVEL_FULL_KEYS]


def levels_short(labels: dict) -> list:
    return [labels[k] for k in LEVEL_SHORT_KEYS]
