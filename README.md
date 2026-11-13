# DS_challenge: predicting major metro service interruptions (STM)

> The full analysis is in [notebooks/analysis.ipynb](notebooks/analysis.ipynb).
> The step-by-step plan and the log of decisions (D1 to D8), with the options
> considered for each, are in [PLAN.md](PLAN.md).

## Summary

- **Question.** The STM wants to improve how metro incidents are escalated
  and prioritised. The question answered here: when a train incident starts,
  will it become a major interruption? Alongside it: how should reliability
  be measured, and what data should be collected?
- **Approach.** A major interruption is defined as a train incident of 15
  minutes or more (3.8% of train incidents); a model using only what is
  plausibly known at the start is trained on past years and tested on later
  ones, with 2025 held out.
- **Headline result.** On 2025, the final model (logistic regression) reaches
  a PR-AUC of 0.096 against 0.048 for a symptom-only rule and 0.033 by chance.
  Escalating the 10% highest-scored incidents would have caught 32 of 99 major
  incidents, about a third. Its probabilities are reliable on average but
  almost never high.
- **A leak found and handled.** A first run scored 0.287 on 2025. That came
  from incidents whose location names a whole line instead of a place, a
  code that may be updated as an incident spreads. They are excluded from
  the model and both results are reported.
- **Most useful findings.**
  - The fields that would predict best (evacuation, emergency team, power cut)
    are recorded without a time, so we can't tell whether they're known early
    enough to help. Used as if known at the start, they make PR-AUC about six
    times higher, an upper bound rather than an achievable result.
    Timestamping them would show how much of that gain is actually reachable,
    which makes it one of the most useful data changes.
  - Deliberate mischief (Méfait volontaire) accounts for 42% of major
    incidents, and customer causes for a rising share.
  - Incidents of 5 minutes or more match the STM's published indicator month
    by month, so that measure can be trusted. Shorter incidents have no such
    check, and their 2025 drop remains unexplained.
  - How incidents are recorded has shifted. Some symptom codes grew or shrank
    several-fold: "Exploitation stations" went from 0.8% of train incidents in
    2019 to 8.8% in 2025, while "Exploitation trains" fell from 12.3% to about
    5%, possibly a change in coding rather than in operations (notebook
    section 3.2, finding 14 in section 4). In 2024, about 350 incidents were
    first labelled as rolling-stock problems before being traced to track.
    Trends by category can't be read reliably without a record of when coding
    rules change.

## Framing: which question this answers

The predictive question chosen here is the one that serves escalation and
prioritisation most directly: **when a train incident starts, will it become
a major interruption?** "Predicting major interruptions" could be framed in
other ways:

| Other framing | Why it is not the main one |
|---|---|
| Forecasting how many major incidents a line will have | Useful for planning, but it needs service volume, and planned km ends in September 2023. Covered descriptively, through rates per million km |
| Predicting the exact duration | Possible in principle from the start and end times. But that elapsed time is the customer-delay window (it may include partial service), disagrees with the published duration bin for 525 train incidents, and is not what the STM reports. The published bin matches the STM's indicator and is the more trustworthy basis, so a threshold on it is used instead (D1, D2) |
| Explaining what causes long incidents | Covered by the driver analysis, which may use the causes assigned after analysis |
| Cost, riders affected and public impact | Not in the data |

Several stakeholder questions cannot be answered with this data yet. The
data collection table under Recommendations lists what would make them
answerable.

## Results

Details are in the notebook, sections 8 (models) and 9 (drivers). Figures are
for the modelling population: 28,887 train incidents, 1,028 of them major (3.6%).

### Predicting major interruptions

| Model | PR-AUC, 4 folds pooled | PR-AUC, 2025 holdout (95% interval) | Major incidents caught in the top 5% / 10%, 2025 |
|---|---|---|---|
| Constant rate (baseline) | 0.038 | 0.033 (0.027 to 0.039) | 4 / 9 of 99 |
| Symptom only (baseline) | 0.072 | 0.048 (0.037 to 0.065) | 12 / 21 of 99 |
| Logistic regression, strict set (lower bound) | 0.086 | 0.071 (0.053 to 0.111) | 11 / 23 of 99 |
| **Logistic regression, headline set (final model)** | **0.108** | **0.096 (0.071 to 0.143)** | **16 / 32 of 99** |
| Gradient boosting, headline set | 0.131 | 0.122 (0.085 to 0.190) | 21 / 31 of 99 |
| Logistic regression, upper bound (not usable) | 0.634 | 0.614 (0.502 to 0.722) | 69 / 78 of 99 |

- **The model works, modestly.** It has about three times the PR-AUC of a
  constant rate and beats the symptom-only rule in every bootstrap resample.
  Escalating the 10% highest-scored incidents would have caught 32 of the 99
  major incidents of 2025, against 21 for the symptom rule and 9 by chance.
  Two thirds of major incidents would still be missed.
- **Which model is better depends on the STM's escalation budget**, the
  share of incidents the control room can escalate:

  | Major incidents caught | Logistic regression | Gradient boosting |
  |---|---|---|
  | Four folds, 5% budget (of 652) | 118 | 137 |
  | Four folds, 10% budget (of 652) | 217 | 215 |
  | 2025 holdout, 5% budget (of 99) | 16 | 21 |
  | 2025 holdout, 10% budget (of 99) | 32 | 31 |

  At a 10% budget logistic regression matches gradient boosting, is steadier
  across years (PR-AUC 0.099 to 0.118 per fold, against 0.109 to 0.153) and
  can be explained to operators, so it is the final model (D8). At a tight
  5% budget gradient boosting catches about 16% more major incidents (137
  against 118 over the four folds). If the STM's capacity is that limited,
  piloting gradient boosting would be worth it.
- **The upper bound is the main message for data collection.** Adding the
  response indicators (power cut, emergency team, evacuation, damage,
  several lines) multiplies PR-AUC by about six. They are mostly
  consequences of a long incident, so this is not achievable at the start,
  but it timestamps would show how much of that gain is actually reachable.
- **Probabilities are calibrated but rarely confident.** Predicted and
  observed rates agree in every score band, yet only 9 of 3,004 holdout
  incidents get a probability above 20%. The scores rank incidents; they
  seldom say "this one will be major".
- **"Train run attached" has the largest effect** (odds ratio 6.3 in the
  logistic regression). Its recording drifts over time and it may partly
  overlap with the outcome, which makes the run-attached ablation listed
  under Further analysis the most important missing check.
- **Rare severe events (30 minutes or more).** The same scores keep an edge
  over the symptom rule (holdout PR-AUC 0.053 against 0.025), but on only 41
  events.
- **Robustness.** Excluding the 525 time/bin mismatches changes PR-AUC by
  less than 0.01. Planned km as a feature and statutory holidays add nothing.

### What drives major incidents, looking back

This part explains past incidents and may therefore use the causes assigned
after analysis, which the predictive model may not. Results are associations,
not causes, and cause coding can drift over time.

- **Customer-related causes are 60% of major incidents** (661 of 1,103):
  "Méfait volontaire" alone is 42%, "Blessée ou malade" 14%. Their share rose
  from about half in 2019 to about two thirds from 2022.
- **Fixed equipment is 20%**, half of it track ("Service de la voie").
  Rolling stock is 9%.
- **Busy stations have many incidents but few long ones.** Interchange and
  terminal stations hold 15% of major incidents; their rate of becoming major
  is 2.2% and 1.1%, against 5.0% elsewhere.
- **Per million planned km, lines diverge.** From 2019 to 2023 the green
  line's rate of major incidents rises from 1.2 to 3.5 while the orange
  line's falls from 1.4 to 0.8.
- Delay minutes are estimated from the duration bins (lower edge; 49 minutes
  for "30 min et plus", the median elapsed time of those incidents) and rank
  the causes in the same order as counts.

## Recommendations

**VP Operations: earlier escalation**

- Use the model as a prioritisation aid, not an automatic trigger: it misses
  about two thirds of major incidents at a 10% budget and rarely gives a
  high probability.
- Choose the model by escalation capacity (budget table in Results):
  logistic regression at about 10%, a gradient boosting pilot if capacity is
  closer to 5%.
- Keep a simple rule for incidents logged with no specific place, which are
  outside the model and 27% major: escalate fire or smoke by default.
- In practice, score each train incident when it is logged; set the alert
  threshold from the control room's escalation capacity; run it alongside
  current practice first (a pilot) before acting on it; retrain each year as
  new data arrives, allowing for incidents that are recorded late; and
  monitor calibration and symptom coding over time, since both drift.

**CFO: prioritisation and confidence**

- Measure reliability as major incidents per million km, by line. Raw counts
  hide the trend: from 2019 to 2023 the green line rises from 1.23 to 3.50
  per million planned km while the orange line falls from 1.43 to 0.80.
- Prioritise with the driver analysis: deliberate mischief is 42% of major
  incidents, and customer causes are a rising share.
- Prioritise spending by whether a line needs fewer incidents or shorter ones.
  Split major incidents per million km into frequency (incidents per million
  km) and severity (share that become major): prevention budgets address the
  first, response and escalation the second. On the green line, both rose: the
  share becoming major jumped in 2020 (2.1% to 4.8%) and stayed between about
  4% and 5% through 2023, while incidents per million planned km kept rising
  (47.3 to 69.8 from 2020). The lasting rise in severity, not seen on the
  orange line, is worth investigating before deciding where to invest.

**Public Affairs / Safety: severe events and user impact**

- Prepare communication for the incidents most likely to become severe. Of the
  524 train incidents of 30 minutes or more since 2019 (54 to 102 a year), 78%
  involved an evacuation and 26% started with a fire or smoke symptom. Fire or
  smoke at the start is the strongest warning sign among fields known at the start.
- Track evacuations and fire or smoke directly, including in stations:
  462 station fire or smoke incidents since 2019, open for a median of 36
  minutes, and invisible in service indicators (notebook section 10).
- Record riders affected and impact type before relying on this data for
  public statements. The data can't say how many people were affected, whether
  service stopped or slowed, or which segment was affected.

**Trend reliability**

- Incidents of 5 minutes or more can be trusted: month by month their count
  follows the STM's published indicator (correlation 0.995 for 2024, 0.977
  for 2025).
- Shorter incidents have no such check: their count depends on logging
  practice, and their 2025 decline has no confirmed explanation.

**Data collection**

| Add | Why |
|---|---|
| Timestamps for response actions (evacuation, emergency team, power cut) | Shows which actions are known early enough to improve escalation; the upper bound is about six times the headline PR-AUC |
| A timestamp for when the location is recorded or updated | Settles the line-list location question |
| A reliable delay measure in minutes | Replaces the eight bins; the start and end times give only an upper bound. Allows cost and severity analysis |
| Impact type (full stop or slowdown) and segment affected | User impact and communication |
| Ridership by line and time | People affected; rates per rider |
| Km actually run, up to date | Reliability rates after September 2023 |
| Km and fleet in service by train model | Separates fewer old trains from better reliability |
| A changelog of classification rules | Tells real trends from coding changes |
| Definitions of each cause category (e.g. "méfait volontaire") | The largest category of major incidents is not defined, so targeted action needs to know what it covers |

## Approach

Each decision is recorded in [PLAN.md](PLAN.md#decision-log) with the options
considered.

| Decision | Choice | Reason |
|---|---|---|
| [D1](PLAN.md#d1-treatment-of-flagged-rows-step-1) Flagged rows | Keep every row; trust the published duration bin over end minus start time | The two disagree for 525 train incidents and the data cannot say which is right; a sensitivity run shows it makes little difference (PR-AUC changes by less than 0.01) |
| [D2](PLAN.md#d2-target-definition-and-modelling-population-step-3) Target | Train incidents of 15 minutes or more; 30 minutes or more as a secondary view | Station incidents can never be positive; 15 minutes is the lowest threshold defensible as "major" |
| [D3](PLAN.md#d3-feature-sets-step-4) Features | Headline set: fields known at the start plus three first-report fields; a strict set and an upper-bound set as brackets | Chosen by availability at the start, not by a selection algorithm, because the main risk is leakage |
| [D4](PLAN.md#d4-validation-scheme-metrics-and-baselines-step-5) Validation | Four yearly folds (2021 to 2024), each trained on earlier years; 2025 held out; PR-AUC, alert budgets, calibration; bootstrap by service day | Train on the past, test on what comes next; pooled folds give 652 major incidents for model comparison |
| [D5](PLAN.md#d5-scope-of-step-6-reduced-time-budget) Scope | Core evaluation kept; extra checks listed as further analysis | Time budget |
| [D6](PLAN.md#d6-models-and-final-model-rule-step-6) Models | Regularised logistic regression and gradient boosting, no class weights; rule fixed in advance for choosing between them | A simple model first; class weights would break calibration |
| [D7](PLAN.md#d7-incidents-with-no-single-place-removed-from-the-modelling-population-step-6) Population | Remove 280 incidents whose location names no single place | Possible leak; the cautious choice, with both results reported |
| [D8](PLAN.md#d8-logistic-regression-as-the-final-model-overriding-the-d6-rule-step-6) Final model | Logistic regression, overriding the D6 rule | Same catch as gradient boosting at a 10% budget, and explainable |

**D7: incidents with no single place.** In the first run, gradient boosting
scored far higher on the 2025 holdout (PR-AUC 0.287) than on the folds
(0.168). All 17 highest-scored holdout incidents had a location code that is
only a line or a list of lines ("Ligne 1, 2"), with a fire or smoke symptom.
Whether this is a leak cannot be settled: the code is concentrated on major
incidents (26.8% major, against 3.6% of the others), which suggests it is
updated as an incident spreads, but an incident may also affect a whole line
from the first minute. These 280 incidents are excluded as the cautious
choice and both results are reported (0.122 without them, 0.287 with them,
for gradient boosting). The cost: 6.8% of major incidents are outside the
model, and the holdout was looked at before this decision.

**D8: overriding the pre-set rule.** The rule pointed to gradient boosting
by a thin margin (pooled PR-AUC 0.131 against 0.108, ahead in 3 of 4 folds).
Fold by fold, the two catch almost the same number of major incidents at a
10% budget (217 and 215), and logistic regression can be explained through
its coefficients. The cost: a lower headline holdout PR-AUC (0.096 against
0.122), fewer major incidents caught at a 5% budget, and a rule overridden
after seeing results. The choice was made on the folds, and gradient
boosting stays reported alongside.

## Limitations

**About the data**

- The official duration exists only as eight bins, the top one open-ended.
  Start and end times give an elapsed time, but it is a less reliable
  measure (D1), so delay minutes are estimates.
- Elapsed time is an upper bound on disruption: the delay window may include
  partial service.
- Durations reflect how the STM responds today; acting on predictions would
  change future data.
- Service volume is planned km, not km actually run, and ends in September 2023.
- No ridership and no cost data.
- Classification drifts: the mix of symptom codes changes (Summary; notebook
  section 3.2, finding 14 in section 4); in August and September 2024 about
  350 incidents were first recorded as rolling-stock problems and later traced
  to track; short incidents fall sharply in 2025.
- The data dictionary does not say when most fields are recorded.
- Station incidents carry no service-delay duration, so they are described,
  not modelled.

**About the analysis**

- Few major incidents: 99 in the 2025 holdout (41 of 30 minutes or more), so
  intervals are wide.
- COVID years (2020 and 2021) are in the training data.
- The holdout was looked at before decision D7, and D8 overrode a rule fixed
  in advance.
- The line-list location question is open; 6.8% of major incidents are outside
  the model.
- Results are associations, not causes.

## Further analysis (not done in the time available)

| Analysis | What it would show |
|---|---|
| Ablation: headline set without "train run attached" | How much of the gain over the strict set comes from that one field (odds ratio 6.3). The most important missing check |
| Sliding training window (previous 3 years only) | Whether older years, with different reporting practice, help or hurt |
| Target at 10 minutes or more | Whether conclusions hold under a looser definition of "major" |
| Permutation importance on the validation folds | Each feature's contribution, measured without relying on model coefficients |
| Error analysis | Which major incidents the model scores low, and which short ones it scores high |

## Data

Two open datasets published by the Société de transport de Montréal (STM) on
the Ville de Montréal open data portal. Snapshot of 7 July 2026 (from the
file names); the portal updates the incidents dataset monthly.

| Dataset | Raw file in `data/raw/` | Portal page |
|---|---|---|
| Metro network incidents | `Incidents métro_20260707.xls` | [Incidents du réseau du métro](https://donnees.montreal.ca/dataset/incidents-du-reseau-du-metro) |
| Planned metro kilometres | `Kilométrage métro planifé_20260707.xls` | [Kilométrage métro des périodes de service](https://donnees.montreal.ca/dataset/stm-kilometrage-metro-des-periodes-de-service) |

- **Licence:** [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), the
  portal's default ([terms of use](https://donnees.montreal.ca/pages/licence-d-utilisation));
  the dataset pages state no licence of their own. Data credited to the STM.
- **Data dictionaries:** saved copies of both portal pages (in French) are in [brief/](brief/).
- **File formats:** both `.xls` files are plain-text CSV with different
  conventions. The details and their verification are in notebook section 1
  and in [PLAN.md](PLAN.md#initial-observations-to-verify-in-exploration).
- **External reference:** monthly values of the STM's published incident
  indicator, transcribed by hand, in `data/external/` (source noted in the
  file).

## Repository layout and how to run

```
brief/            data dictionaries (saved portal pages, in French)
data/raw/         original files, read-only
data/processed/   cleaned tables written by the code (committed, rebuilt from raw)
data/external/    small reference values from STM publications
notebooks/        analysis.ipynb, the narrative notebook
src/              reusable Python modules
  data.py           load and clean the raw files
  eda.py            summaries used in the exploration
  verify.py         checks of the first-look observations
  features.py       targets and feature sets (D2, D3, D7)
  validation.py     yearly train/test folds (D4)
  model.py          baselines and models (D6)
  evaluate.py       metrics, calibration table, bootstrap
  drivers.py        driver analysis of past major incidents
PLAN.md           work plan and decision log
requirements.txt  pinned dependencies
```

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Rebuild the cleaned tables in data/processed/ from the raw files
python -m src.data

# Re-run the notebook (or open it in an editor and run all cells)
jupyter nbconvert --to notebook --execute --inplace notebooks/analysis.ipynb
```

## Use of AI

- **Understanding the problem.** Before starting, I used Claude to work
  through the brief, understand the data and research context. Several
  hypotheses tested here came from that, such as the 2025 strikes, the
  Saint-Michel closure and the STM's published reliability indicator.
- **Plan first, then step by step.** With Claude Code, I started by agreeing a
  plan (PLAN.md) before writing any code, then worked through it one step at a
  time. At each step it proposed options with trade-offs, I made the decision
  (logged as D1 to D8), it ran the checks, and I reviewed them before
  committing.
- **Checking.** Verification went both ways. I confirmed the STM figures
  against the source document and tightened claims the data didn't fully
  support; Claude Code corrected some of my hypotheses and flagged the
  location-code leak (D7).
- **Record.** Tools: Claude (preparation) and Claude Code in VS Code (build).
  Apart from the challenge instructions, only the public datasets and
  documents were shared. The step-by-step process is visible in PLAN.md and
  the commit history.
