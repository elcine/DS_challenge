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
  more (524) are reported as a secondary view on the same model scores, and
  one sensitivity run uses 10 minutes or more.
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
  step excludes those 525 rows to show whether the choice matters.

[Options considered: D2](PLAN.md#d2-target-definition-and-modelling-population-step-3).

## Results

_To be completed._

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
