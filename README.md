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
  are in the lowest duration bin, so they can never be positive.
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
  pooled test folds hold 693 major incidents, against 121 to 222 in any
  single year. No random splits.
- **Final holdout.** 2025 (January to September, 121 major incidents),
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

## Results

_To be completed._

## Further analysis (not done in the time available)

Checks that were planned and then cut to keep the modelling step focused.
Each would test how far the results depend on one choice.

| Analysis | What it would show |
|---|---|
| Ablation: headline set without "train run attached" | How much of the headline set's gain over the strict set comes from that one field, whose recording drifts and which may partly overlap with the outcome |
| Sliding training window (previous 3 years only) | Whether older years, with different reporting practice, help or hurt |
| Target at 10 minutes or more | Whether conclusions hold under a looser definition of "major" |
| Excluding the 280 rows whose location is a line list | Whether the residual leak accepted in the location grouping drives performance |
| Permutation importance on the validation folds | Each feature's contribution, measured without relying on model coefficients |

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
