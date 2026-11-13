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
  to 27), in mixed `HH:MM` and `HH:MM:SS` formats.
- Some values appear to have been altered by a spreadsheet: one line value
  reads `02-avr`, and year/month is stored as text such as `janv-19`.
- The incidents file contains a duration column (`Incident en minutes`) that
  the data dictionary does not describe.

These notes come from a first look at the files and are verified in the
exploratory analysis.

## Limitations

_To be completed._

## Approach

_To be completed._

## Results

_To be completed._

## Recommendations

_To be completed._

## Repository layout

```
brief/            data dictionaries (saved portal pages, in French)
data/raw/         original files, read-only
data/processed/   cleaned tables written by the code (committed, rebuilt from raw)
notebooks/        one narrative notebook
src/              reusable Python modules
PLAN.md           work plan and decision log
requirements.txt  pinned dependencies
```

## How to run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

_Commands to rebuild the processed data and run the notebook: to be completed._

## Use of AI

_To be completed._
