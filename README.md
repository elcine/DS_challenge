# DS_challenge: predicting major metro service interruptions (STM)

> Work in progress. Sections marked _To be completed_ are filled in as the
> analysis advances. The step-by-step plan and the decision log are in
> [PLAN.md](PLAN.md).

## Summary

_To be completed._

## Data

Two open datasets published by the Société de transport de Montréal (STM) on
the Ville de Montréal open data portal.

| Dataset | Raw file in `data/raw/` | Portal page |
|---|---|---|
| Metro network incidents | `Incidents métro_20260707.xls` | [Incidents du réseau du métro](https://donnees.montreal.ca/dataset/incidents-du-reseau-du-metro) |
| Planned metro kilometres | `Kilométrage métro planifé_20260707.xls` | [Kilométrage métro des périodes de service](https://donnees.montreal.ca/dataset/stm-kilometrage-metro-des-periodes-de-service) |

- **Publisher:** Société de transport de Montréal, Centre de compétences en
  intelligence d'affaires.
- **Snapshot date:** 7 July 2026, taken from the file names (`_20260707`). The
  portal updates the incidents dataset monthly, so a later download will differ.
- **Licence:** the portal's
  [terms of use](https://donnees.montreal.ca/pages/licence-d-utilisation)
  publish the City's open data under
  [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).
  The two dataset pages do not show a licence field of their own, and the
  terms note that data from other organisations can carry a different licence,
  so CC BY 4.0 is the portal default rather than a licence stated on these
  pages. The data is credited to the STM here, and all changes made to it are
  described in this repository.
- **Data dictionaries:** saved copies of both portal pages (in French) are in
  [brief/](brief/).

### File format notes

The raw files are kept exactly as received and are never modified. A few
things about them are unusual:

- Both files have an `.xls` extension but are plain-text CSV, not Excel workbooks.
- The two files use different conventions:

| | Incidents | Planned km |
|---|---|---|
| Delimiter | `;` | `,` |
| Encoding | UTF-8 with byte-order mark | UTF-8 |
| Decimal separator | n/a | `,` (e.g. `16315,92`) |

- Incident times are on a service-day clock that runs past midnight (hours 24
  to 29), in mixed `HH:MM` and `HH:MM:SS` formats.
- Some values appear to have been altered by a spreadsheet: one line value
  reads `02-avr`, and year/month is stored as text such as `janv-19`.
- The incidents file contains a duration column (`Incident en minutes`) that
  the data dictionary does not describe.

These notes were verified in the exploratory analysis (notebook section 1);
five first-look observations were corrected there.

## Limitations

_To be completed._

## Approach

Each choice below is recorded, with the options that were considered, in the
[decision log in PLAN.md](PLAN.md#decision-log). Further choices are added
here as they are made.

### Data cleaning: keep every row, flag the doubtful ones (D1)

No row is dropped or corrected. Cleaning flagged 584 of 45,561 incidents: one
corrupted line value (treated as an unknown line), 525 train incidents whose
end time minus start time falls outside their duration bin, and 60 whose
calendar date and start time disagree. Excluding rows would rest on a rule
that cannot be verified, and guessing values would be invention.
[Options considered: D1](PLAN.md#d1-treatment-of-flagged-rows-step-1).

### Target: train incidents lasting 15 minutes or more (D2)

- **Population.** Train incidents only (29,167). All 16,394 station incidents
  are in the lowest duration bin, so they can never be positive. A later
  check (D7, below) also removes 280 train incidents with no single place.
- **Definition.** A major interruption is a train incident of 15 minutes or
  more: 1,103 incidents, 3.8%. This is the lowest threshold that can be
  defended as "major" in front of stakeholders. Incidents of 30 minutes or
  more (524) are reported as a secondary view on the same model scores.
  Thirty minutes or more is used as a proxy for rare severe events; severity
  for Public Affairs / Safety is also covered descriptively, through
  evacuations and fire or smoke incidents, including station incidents.
- **Measured on the published bin, not on computed time.** The target is
  defined on the published duration bin (`Incident en minutes`), not on end
  time minus start time. The bin is the STM's own measure of the service
  delay, and counts based on it match the STM's published indicator (see the
  notebook, section 2.6.4). The computed time disagrees with the bin for 525
  train incidents (1.8%), mostly by being longer than the bin, and the data
  cannot say which of the two is right. A sensitivity run in the modelling
  step excludes those 525 rows, from training and test, to show whether the
  choice matters.

[Options considered: D2](PLAN.md#d2-target-definition-and-modelling-population-step-3).

### Features: what is plausibly known when an incident starts (D3)

- **Headline set.** Fields documented or inherent at the start (symptom,
  line, location, hour, weekday, month) plus three that describe the
  triggering event and are plausibly in the first report (train run attached,
  door involved, emergency brake). The timing of those three is a reading of
  the fields, not something the data dictionary states.
- **Two brackets around it.** A strict set with only the documented fields
  is reported as a lower bound. A set that adds the response indicators
  (traction power cut, emergency team, evacuation, material damage, several
  lines) is reported only as an upper bound, "if these indicators were known
  in the first minutes": they are mostly consequences of a long incident, so
  that is not a usable model. Its gap over the headline set shows what
  timestamping response actions would be worth.
- **Left out on purpose.** Causes and rolling stock type (set by analysis
  after the incident), end time, year, and features built from past
  incidents (no relation to the target, and a leakage risk). Multi-line
  incidents are assigned their first listed line, and line lists are removed
  from location codes, so the model cannot learn "the incident spread"
  through the back door.
- **No automated feature selection.** Features were chosen by whether they
  are available when an incident starts. The main risk here is leakage, and
  no selection algorithm can detect it: it would pick the evacuation flag
  first. The set is small (7 to 10 fields), and a statistical search on a few
  hundred positives would risk fitting noise and would have to be repeated
  inside every training fold. Instead, regularised logistic regression
  shrinks weak features, and the three nested feature sets are compared
  explicitly.
- **Associations, not causes.** Feature effects describe which incidents
  tend to be long, not what makes them long.

[Options considered: D3](PLAN.md#d3-feature-sets-step-4).

### Validation and metrics: train on the past, test on what comes next (D4)

- **Model comparison.** Four yearly folds (test years 2021 to 2024), each
  trained on all earlier years. Results are shown per fold and pooled: the
  pooled test folds hold 652 major incidents (after D7), against 99 to 195
  in any single year. No random splits.
- **Final holdout.** 2025 (January to September, 99 major incidents after D7),
  scored once by a model trained on 2019 to 2024, and never used to choose
  between models. It is the most recent period, and for incidents of 5
  minutes or more its counts match the STM's published rate.
- **Metrics.** PR-AUC as the primary metric, read against the base rate of
  about 4%. For operations: how many major incidents fall among the 5% and
  10% highest-scored incidents. For confidence: calibration (Brier score
  against a constant-rate baseline, and predicted against observed rates).
  ROC-AUC as a familiar secondary reference.
- **Baselines and uncertainty.** Two baselines a model must beat: a constant
  rate, and a symptom-only rate table (the rule of thumb available without a
  model). Intervals on the holdout come from a bootstrap that resamples
  whole service days, because incidents on the same day are not independent.

[Options considered: D4](PLAN.md#d4-validation-scheme-metrics-and-baselines-step-5).

### Models: a simple model first, a complex one only if it earns its place (D6)

- **Two models.** A regularised logistic regression (one-hot encoded fields,
  regularisation strength chosen on the validation folds) and gradient
  boosting with fixed, conservative settings and no tuning. Neither uses
  class weights, which would inflate predicted probabilities.
- **Rule fixed in advance.** Logistic regression is the final model unless
  gradient boosting's pooled PR-AUC is more than about 0.01 higher and ahead
  in most folds. Its coefficients are easier to explain and defend.
- **Scope.** Gradient boosting is run on the headline feature set only;
  logistic regression on all three sets. The reduced scope of the modelling
  step is recorded as [D5](PLAN.md#d5-scope-of-step-6-reduced-time-budget).

[Options considered: D6](PLAN.md#d6-models-and-final-model-rule-step-6).

### A check that changed the population: incidents with no single place (D7)

- **How it was found.** In the first run the model scored far higher on the
  2025 holdout (PR-AUC 0.287) than on the validation folds (0.168). Every one
  of the 17 highest-scored holdout incidents had a location code that is only
  a line or a list of lines ("Ligne 1, 2"), together with a fire or smoke
  symptom.
- **Leak or not: the data cannot say.** The code names no place and is
  concentrated on major incidents (26.8% major, against 3.6% of the others),
  which suggests it is updated as an incident spreads. But some incidents may
  affect a whole line from the first minute (a power or signalling problem),
  and then the code is legitimate start-time information.
- **Choice.** These 280 incidents are excluded from the headline model,
  training and test, as the cautious choice, and both results are reported.
  For gradient boosting, the model of the first run, the holdout PR-AUC is
  0.122 without them and 0.287 with them. If the STM confirms the
  code is recorded at the start, the higher result applies to those incidents.
- **Cost.** 6.8% of major incidents (75 of 1,103) are outside the model's
  scope. In use, incidents logged without a specific place would need a
  separate rule, for example escalating fire or smoke by default. A timestamp
  for when the location is recorded or updated would settle the question.
- **Honest caveat.** This decision was triggered by looking at holdout
  results, so the 2025 figures are a little less independent than planned.
  It lowers the reported score, and the choice between models was re-made on
  the validation folds only (D8).

[Options considered: D7](PLAN.md#d7-incidents-with-no-single-place-removed-from-the-modelling-population-step-6).

### Final model: logistic regression, overriding the pre-set rule (D8)

- **What the rule said.** Gradient boosting, by a thin margin: pooled PR-AUC
  0.131 against 0.108, ahead in 3 of 4 folds.
- **Why it was overridden.** Fold by fold, the difference is not robust
  where it matters operationally: at a 10% alert budget the two models catch
  almost the same number of major incidents over four years (217 for
  logistic regression, 215 for gradient boosting). Logistic regression is
  preferred because every prediction can be traced to a short list of
  coefficients.
- **What it costs.** A lower headline holdout PR-AUC (0.096 against 0.122),
  and fewer major incidents caught at a 5% budget (118 against 137 on the
  folds). A rule fixed in advance was overridden after seeing results; the
  override goes towards the simpler, lower-scoring model, was made on the
  folds, and gradient boosting stays reported alongside.

[Options considered: D8](PLAN.md#d8-logistic-regression-as-the-final-model-overriding-the-d6-rule-step-6).

## Results

Full results are in the notebook, [sections 8 and 9](notebooks/analysis.ipynb).
Figures below are for the modelling population after decision D7: 28,887
train incidents, 1,028 of them major (3.6%).

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
- **Which model is better depends on the STM's escalation budget.** The
  share of incidents the control room can escalate decides it:

  | Major incidents caught | Logistic regression | Gradient boosting |
  |---|---|---|
  | Four folds, 5% budget (of 652) | 118 | 137 |
  | Four folds, 10% budget (of 652) | 217 | 215 |
  | 2025 holdout, 5% budget (of 99) | 16 | 21 |
  | 2025 holdout, 10% budget (of 99) | 32 | 31 |

  At a 10% budget logistic regression matches gradient boosting, is steadier
  across years (PR-AUC 0.099 to 0.118 per fold, against 0.109 to 0.153) and
  can be explained to operators, so it is the final model (D8, above). At a
  tight 5% budget gradient boosting catches about 16% more major incidents
  (137 against 118 over the four folds). If the STM's capacity is that
  limited, piloting gradient boosting would be worth it.
- **The upper bound is the main message for data collection.** Adding the
  response indicators (power cut, emergency team, evacuation, damage,
  several lines) multiplies PR-AUC by about six. They are mostly
  consequences of a long incident, so this is not achievable at the start,
  but it shows what timestamping those actions could be worth.
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

## Further analysis (not done in the time available)

Checks that were planned and then cut to keep the modelling step focused.
Each would test how far the results depend on one choice.

| Analysis | What it would show |
|---|---|
| Ablation: headline set without "train run attached" | How much of the headline set's gain over the strict set comes from that one field, whose recording drifts and which may partly overlap with the outcome. The most important missing check: this field has the largest coefficient (odds ratio 6.3) |
| Sliding training window (previous 3 years only) | Whether older years, with different reporting practice, help or hurt |
| Target at 10 minutes or more | Whether conclusions hold under a looser definition of "major" |
| Permutation importance on the validation folds | Each feature's contribution, measured without relying on model coefficients |
| Error analysis | Where the model fails: which major incidents it scores low, and which short incidents it scores high |

## Recommendations

_To be completed._

## Repository layout

```
brief/            data dictionaries (saved portal pages, in French)
data/raw/         original files, read-only
data/processed/   cleaned tables written by the code (committed, rebuilt from raw)
data/external/    small reference values from STM publications (source noted in each file)
notebooks/        one narrative notebook
src/              reusable Python modules
  data.py           load and clean the raw files
  eda.py            summaries used in the exploration
  verify.py         checks of the first-look observations
  features.py       targets and feature sets (decisions D2 and D3)
  validation.py     yearly train/test folds (decision D4)
  model.py          baselines and models (decision D6)
  evaluate.py       metrics, calibration table, bootstrap
  drivers.py        driver analysis of past major incidents
PLAN.md           work plan and decision log
requirements.txt  pinned dependencies
```

## How to run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Rebuild the cleaned tables in `data/processed/` from the raw files:

```bash
python -m src.data
```

Re-run the notebook from the command line (or open
`notebooks/analysis.ipynb` in an editor and run all cells):

```bash
jupyter nbconvert --to notebook --execute --inplace notebooks/analysis.ipynb
```

## Use of AI

_To be completed._
