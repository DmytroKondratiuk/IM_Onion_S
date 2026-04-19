> [English](README.md) · **Українська**

# ІМ Onion-S — Імітаційна модель цифрової трансформації агропродовольчих підприємств

Імітаційне моделювання стратегічного управління цифровою трансформацією на базі **System Dynamics** + **ланцюги Маркова**. Модель генерує ~10 000 віртуальних підприємств, калібрує штрафні параметри α та δ формули ADMI, проводить сценарний аналіз 5 стратегій на горизонтах 5/10/15 років, крос-валідує SD-результати через матриці Маркова та виконує аналіз чутливості параметрів.

Результати — структурований xlsx-звіт із 20 листів (таблиці + вбудовані графіки + conditional-formatting heatmap-и) і набір PNG-графіків для вставки у публікації.

Частина дисертаційного дослідження (PhD Economics, спеціальність 051). Код виконаний українською та англійською мовами з перемиканням у runtime.

---

## Швидкий старт

```bash
# 1. Встановити залежності (один раз)
pip3 install -r requirements.txt

# 2. Запустити повний цикл
python3 generate_report.py
```

Скрипт запитає мову виводу (`uk` / `en`), запустить моделювання і збереже результати у:
- `results/simulation_report.json` — сирі дані
- `results/onion_s_simulation.xlsx` — повний xlsx-звіт
- `figures/stock_flow.png`, `figures/stock_flow.dot` — Stock-and-Flow діаграма

---

## CLI-прапорці

| Прапор | Опис |
|---|---|
| `--lang uk` / `--lang en` | Мова виводу (без інтерактивного запиту) |
| `--quick` | Швидкий режим: 200 підприємств × 3 запуски (≈8 с замість ≈3–5 хв) |
| `--no-multi` | Пропустити багатогоризонтний аналіз (10/15 років) |
| `--export-pngs` | Згенерувати PNG для всіх 5 основних графіків + 4 теплових карт |
| `--output-dir PATH` | Альтернативна папка для JSON/xlsx (default: `./results`) |
| `--figures-dir PATH` | Альтернативна папка для PNG/.dot (default: `./figures`) |

### Приклади

```bash
# Швидкий тест pipeline, українською
python3 generate_report.py --quick --lang uk

# Повний цикл з усіма PNG, англійською
python3 generate_report.py --lang en --export-pngs

# Без 10/15 років (швидше)
python3 generate_report.py --lang uk --no-multi --export-pngs
```

---

## Що генерується

### `results/simulation_report.json`
Структурований JSON з усіма сирими даними: калібрація, траєкторії ADMI, покомпонентні DM, матриці переходу Маркова, стаціонарні розподіли, час досягнення рівнів, чутливість параметрів, багатогоризонтні результати.

### `results/onion_s_simulation.xlsx`
20 листів, розділені на 2 групи:

**Таблиці-результати (15 листів):**
- Про звіт (метадані запуску)
- Калібрація (α*, δ*, J, C₁, C₂, C₃ по 10 запусках)
- Теплова карта J(α,δ) з conditional formatting
- Деградація d_k
- Сценарії ADMI (траєкторії mean/std/median/p25/p75)
- Сценарії DM компоненти (покомпонентні DM_i по роках)
- Рівні розподіл (розподіл підприємств по 5 рівнях зрілості)
- 3× Матриці Маркова (С-1/С-2/С-3) з heatmap через conditional formatting
- Стаціонарні розподіли π
- Час досягнення рівня (hitting times)
- Багатогоризонтний (ΔADMI 5/10/15)
- Крос-валідація (SD vs Маркова)
- Чутливість (OAT ±20%)

**Листи з графіками (5 листів, openpyxl-charts без заголовків):**
- Траєкторії ADMI (LineChart)
- Профілі DM (RadarChart)
- Багатогоризонтний (BarChart)
- Крос-валідація (BarChart)
- Чутливість (Tornado BarChart)

### `figures/` (з `--export-pngs`)

| Файл | Опис |
|---|---|
| `stock_flow.png` | Stock-and-Flow діаграма (matplotlib, завжди генерується) |
| `stock_flow.dot` | Graphviz-джерело для імпорту в **draw.io** (завжди) |
| `trajectories_admi.png` | Лінійні траєкторії ADMI за 5 сценаріями |
| `profiles_radar.png` | Radar (пелюсткова) профілів DM на 5-му році |
| `multi_horizon_bar.png` | Групована стовпчикова ΔADMI × 5/10/15 років |
| `cross_validation_bar.png` | SD vs Маркова (рівномірна стратегія) |
| `sensitivity_tornado.png` | Tornado-діаграма чутливості параметрів |
| `heatmap_uniform.png` | Матриця переходу Маркова — С-1 Рівномірна |
| `heatmap_S2_core.png` | Матриця переходу — С-2 Ядро |
| `heatmap_S3_integration.png` | Матриця переходу — С-3 Інтеграція |
| `heatmap_calibration.png` | Теплова карта J(α, δ) з відміченим максимумом |

На жодному з PNG заголовок не накладається — підпис додається у caption публікації.

---

## Тривалість виконання

| Режим | Час |
|---|---|
| `--quick` (200 × 3, 5 років) | ≈ 4–5 с |
| `--quick` + multi-horizon | ≈ 8–10 с |
| Повний (1000 × 10, 5 років) | ≈ 1–2 хв |
| Повний + multi-horizon | ≈ 3–5 хв |

---

## Імпорт `.dot` у draw.io

Stock-and-Flow діаграма зберігається у двох форматах: PNG (готовий для вставки у публікацію) і **.dot** (Graphviz), який можна імпортувати у draw.io для доопрацювання:

1. Відкрити <https://app.diagrams.net> (або десктоп).
2. **File → Import → Device…**
3. Вибрати `figures/stock_flow.dot`.
4. За потреби — у діалозі імпорту вибрати «Graphviz (.dot)».

---

## Конфігурація

Усі параметри моделі зібрані в `src/onion_s_simulation.py`, словник `CONFIG`:

```python
CONFIG = {
    "n_enterprises": 1000,            # розмір вибірки
    "n_runs": 10,                     # незалежних запусків калібрації
    "n_years": 5,                     # горизонт
    "dt": 0.25,                       # квартальний крок
    "alpha_range": np.arange(...),    # грід для α
    "delta_range": np.arange(...),    # грід для δ
    "budget_total": 0.40,             # бюджет за квартал
    "investment_efficiency": 0.55,    # η
    "absorptive_saturation": 0.4,     # σ (поглинальна зд.)
    "integration_power": 0.5,         # β (інтеграційна степ. ф.)
    "scenarios": { ... },             # 5 векторів розподілу бюджету
    ...
}
```

Нові сценарії додаються у `CONFIG["scenarios"]` + переклади у `src/i18n.py` (`SCENARIO_KEY_MAP` + UK/EN словники).

---

## Цитування

<!-- TODO: замінити плейсхолдер DOI нижче після того, як Zenodo видасть DOI при першому GitHub release -->

<!-- [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX) -->

Якщо ви використовуєте це програмне забезпечення у дослідженнях — будь ласка,
цитуйте його. Машиночитана метадата міститься у файлі [`CITATION.cff`](CITATION.cff);
GitHub автоматично показує кнопку «Cite this repository» у бічній панелі
репозиторію.

**Рекомендоване посилання (ДСТУ 8302:2015):**

> Кондратюк Д. IM Onion-S — Simulation Model of Digital Transformation of
> Agri-food Enterprises: комп'ютерна програма. Версія 1.0.0. Zenodo, 2026.
> DOI: 10.5281/zenodo.XXXXXXX. URL:
> https://github.com/DmytroKondratiuk/im_onion_s

**APA-подібний формат (для міжнародних публікацій):**

> Kondratiuk, D. (2026). *IM Onion-S — Simulation Model of Digital
> Transformation of Agri-food Enterprises* (Version 1.0.0) [Computer
> software]. Zenodo. https://doi.org/10.5281/zenodo.XXXXXXX

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

---

## Ліцензія

Apache-2.0 (деталі — у `CITATION.cff` і майбутньому файлі `LICENSE`). Код оприлюднений
для відтворюваності результатів дисертаційного дослідження; якщо ви його
використовуєте — будь ласка, процитуйте як указано вище.

---

## Автор

Дмитро Кондратюк — дисертаційне дослідження зі спеціальності 051 «Економіка», тема «Стратегічне управління цифровою трансформацією агропродовольчих підприємств: теорія, методологія, імплементація».
