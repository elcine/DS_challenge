# Work plan

Working plan for the STM metro incidents challenge. It is followed one step at a
time: each step ends with a plain-language summary and a set of checks, and the
next step starts only after explicit approval.

Decisions about the target, the features, the validation scheme and the models
are deliberately left open. They are taken after the exploratory analysis, and
each one is recorded in the [Decision log](#decision-log).

## Ground rules

- `data/raw/` is read-only. Cleaned and derived data go to `data/processed/`.
- Code lives in `src/` modules, with one notebook for the narrative.
- Code stays simple and commented: every line must be explainable in the interview.
- One commit per step, with a clear message.
- The challenge instructions (`brief/*.docx`) stay local and are not copied into the repo.
- Each step has a rough time estimate. If a step is running over, I flag it
  before continuing, with what is left and what could be cut.

## Initial observations (to verify in exploration)

First read-only look at the two raw files and their data dictionaries. These
are provisional: nothing here is a decision or a confirmed finding. Each
observation is re-checked in step 2, where it is either confirmed or corrected.

### File formats

- Both `.xls` files are plain-text CSV, not Excel workbooks.
  - Incidents: `;` delimiter, UTF-8 with BOM, CRLF line endings, 45,561 rows × 26 columns.
  - Planned km: `,` delimiter, decimal commas in the km column (e.g. `16315,92`), 8,472 rows × 11 columns.
- Signs of a spreadsheet round trip in the incidents file:
  - one `Ligne` value reads `02-avr` (a list of lines converted to a date);
  - `Année civile/mois` is stored as `janv-19`, `févr-19`, etc.
- Incident times follow the service day, not the clock: hours run from 02:00 to
  27:41, in mixed `HH:MM` and `HH:MM:SS` formats. `Jour calendaire` is the real
  calendar date, while `Jour du mois` and `Année civile` follow the service day
  (an incident at 24:00 on service day 1 August has `Jour calendaire` 2 August).
- Dictionary and file do not match exactly: `Incident en minutes` is in the file
  but not in the dictionary; `Date du jour (Alpha)` is in the dictionary but not
  in the file.

### Coverage

- Incidents: 2019-01-01 to 2025-09-30, although the snapshot is dated 2026-07-07.
- Planned km: 2019-01-01 to 2023-09-30 only. There is no service-volume
  denominator for the last two years of incidents.
- Planned km, 2019: every line/day appears twice, once with real km and once as
  a zero-km `Non affecté` row. `Tournée` is always `001`.
- The dictionary states that train incidents can appear more than 30 days late
  because cause analysis takes time, so the most recent months may be incomplete.

### Duration and incident type

- Duration is published only as eight bins (`Incident en minutes`), from
  `02 min et moins` to an open-ended `30 min et plus`. There is no exact duration field.
- Counts by type: 29,167 train incidents (`T`) and 16,394 station incidents (`S`).
- Every station incident is in the lowest bin. The dictionary says station
  incidents do not affect metro service.
- Train incidents by bin:

| Bin | Train incidents |
|---|---|
| 02 min et moins | 16,450 |
| 03 à 04 min | 6,304 |
| 05 à 09 min | 4,377 |
| 10 à 14 min | 933 |
| 15 à 19 min | 299 |
| 20 à 24 min | 173 |
| 25 à 29 min | 107 |
| 30 min et plus | 524 |

- For train incidents, `Heure de l'incident` is the start of the customer delay,
  not the start of the incident itself.
- `Heure de reprise` minus `Heure de l'incident` does not always agree with the
  bin (some rows in the lowest bin show gaps of several hours).
- The dictionary notes that industry indicators ignore interruptions under 5 minutes.

### When each field becomes known

- `Symptome` is described as the cause attributed at the time of the incident.
- `Cause primaire` and `Cause secondaire` are determined by analysis after the incident.
- `Type de matériel` appears to be derived from `Cause secondaire` (2,915 rows
  with `73` and 2,915 rows with `MR-73`).
- `CAT`, `Urgence métro`, `Évacuation` and `Dommage matériel` have no documented
  timing. They are strongly associated with long incidents, which could mean
  they are early signals or consequences of a long incident.
- `Ligne` has 22 values: the four lines, `Non affecté`, and multi-line
  combinations such as `Ligne 1, 2, 4`, which may reflect how far an incident spread.

### Missing values and placeholders

- `Cause primaire` / `Cause secondaire`: about 1% missing, all on train incidents.
- `Symptome`: under 1% missing overall, rising from 2022 onward.
- `#` is used as "not applicable" in `Numéro de tournée`, `Véhicule`,
  `Porte de voiture` and `Évacuation`.
- `Code de lieu` has 230 distinct values, mixing stations, technical locations
  and line lists.

## Steps

Time estimates are rough and add up to about 3 hours (180 minutes).

### Step 0: Setup (~10 min)

**Goal.** A reproducible project skeleton that a reviewer can clone and run.

**What I'll do.**
- Create a project virtual environment and a pinned `requirements.txt`.
- Create `src/`, `notebooks/` and `data/processed/`.
- Write a README skeleton with the data section: source links, snapshot date,
  licence (to be confirmed on the open data portal), and the format quirks above.

**Checks I'll show.**
- Folder tree and `git status`.
- Python and package versions from the new environment.
- The licence text and the URL where it was confirmed.

**Decision needed.** Whether `data/processed/` is committed or gitignored
(regenerated by code).

### Step 1: Load and clean (~20 min)

**Goal.** Two tidy tables that reproduce the raw data faithfully, with types
fixed and nothing silently dropped.

**What I'll do.**
- `src/data.py`: read both raw files with explicit delimiter, encoding and
  decimal settings.
- Rename columns to short English names, with the mapping kept in one place.
- Parse dates and service-day times; convert `#` and `Non affecté` placeholders
  to explicit missing values or categories.
- Flag, rather than fix, the suspicious rows (the `02-avr` line, time gaps that
  contradict the duration bin).
- Handle the duplicate zero-km rows in the 2019 km data.
- Write the cleaned tables to `data/processed/`.

**Checks I'll show.**
- Row counts in equal row counts out, for both files.
- Duration-bin and incident-type totals match the raw counts above.
- Date ranges, and counts of unparsed dates and times (expected: zero).
- Annual km per line before and after removing the zero-km rows (expected: identical).
- A list of every row flagged as suspicious, with the reason.

**Decision needed.** How to treat the flagged rows: keep as is, correct, or exclude.

### Step 2: Exploratory analysis (~45 min)

**Goal.** Understand what the data can and cannot support before choosing a
target or features, and separate real reliability changes from service volume,
reporting practice and classification effects.

**Scope.** Capped at about 45 minutes. Every analysis here must inform the
target decision (step 3) or the feature decision (step 4); anything else is
left out or noted as a possible follow-up.

**What I'll do.** In the notebook, with helpers in `src/`:
- Verify the initial observations: for each one listed above, show the check
  that confirms or corrects it, and update that section of this plan with the result.
- For the target decision:
  - Duration: bin distribution by year and by line, and how stable the bin
    shares are over time (reporting and classification consistency).
  - Volume over time: train incidents per month, with the COVID period and the
    last months of the data marked, to judge which periods are usable.
  - Reliability view: train incidents per million planned km, by line and year,
    for the period where km exists (2019 to September 2023), next to raw counts.
- For the feature decision:
  - Field timing: for each candidate predictor, how it relates to duration and
    what the dictionary says about when it is recorded.
  - Data quality of candidate predictors: missingness and category shares by year.
  - Time and location: duration by hour of service day, day of week and location,
    in one compact view each.

**Checks I'll show.**
- A verification table with one row per initial observation: the observation,
  the check run, the result, and a status of confirmed or corrected.
- Each figure with the table behind it.
- Totals in every breakdown reconcile to the cleaned table.
- Km join coverage: share of incidents with a matching km denominator.
- A short written list of findings, each tagged as solid, tentative or not
  answerable with this data.

**Decision needed.** None yet. This step produces the evidence for steps 3 and 4.

### Step 3: Target decision (~10 min)

**Goal.** Define "major interruption" in a way the data supports and the
stakeholders would recognise.

**What I'll do.**
- Lay out the candidate definitions that the eight duration bins allow, and the
  candidate modelling populations (all incidents or train incidents only).
- For each: number of positives overall and per year, stability over time,
  and the business meaning.
- State the trade-offs side by side.

**Checks I'll show.**
- Positives and rates per year for every candidate.
- Number of positives that would fall in a typical test period, as an
  indication of how noisy evaluation would be.

**Decision needed.** Target definition and modelling population. Recorded in
the Decision log.

### Step 4: Feature decision (~20 min)

**Goal.** Fix the list of predictors that are legitimately available when an
incident starts, with leakage reasoning for every field.

**What I'll do.**
- Classify each column as: known at incident start, known later, or timing unknown.
- Present feature-set options with trade-offs, using the step 2 evidence.
- After the decision, implement `src/features.py`.

**Checks I'll show.**
- A table with one row per raw column: status, reason, in or out.
- An automated check that no excluded column reaches the feature matrix.
- For any feature built from past incidents, a check that it uses earlier rows only.
- Feature matrix shape and missing-value counts.

**Decision needed.** Feature set, including the treatment of fields with
unknown timing. Recorded in the Decision log.

### Step 5: Validation and metrics decision (~10 min)

**Goal.** Agree how performance will be measured before any model is fitted.

**What I'll do.**
- Propose temporal validation schemes that fit the chosen target (no random
  splits), with the number of positives per fold.
- Propose metrics tied to the stakeholders' questions and to the class balance
  of the chosen target.
- Propose the baselines a model must beat.

**Checks I'll show.**
- Fold boundaries, rows and positives per fold.
- Confirmation that no test period overlaps or precedes its training period.

**Decision needed.** Validation scheme, metrics and baselines. Recorded in the
Decision log.

### Step 6: Modelling (~35 min)

**Goal.** A predictive framework evaluated honestly under the agreed scheme.

**What I'll do.**
- Propose candidate models only now, with trade-offs, given the decided target
  and features.
- After the decision: implement `src/model.py` and `src/evaluate.py`, fit, and
  evaluate against the baselines.

**Checks I'll show.**
- Metrics per fold and on the final holdout, with uncertainty.
- Comparison against baselines.
- Which features drive predictions, and whether that is plausible.
- Error analysis: where the model fails.

**Decision needed.** Model choice. Recorded in the Decision log.

### Step 7: Recommendations and README (~25 min)

**Goal.** Turn the analysis into recommendations for the three stakeholder
groups, and a README that reviewers can read on its own.

**What I'll do.**
- Write recommendations on measuring reliability, prioritising action and
  improving data collection, stating clearly what the data cannot answer.
- Complete the README: summary, data, limitations, approach, results,
  recommendations, repo layout and how to run, note on AI use.

**Checks I'll show.**
- Every number in the README traced to a notebook cell or script output.
- The full README for review.

**Decision needed.** Approval of wording and emphasis.

### Step 8: Final pass (~5 min)

**Goal.** A clean, reproducible public repo.

**What I'll do.**
- Re-run everything from raw data in a fresh environment.
- Remove dead code, check comments, confirm nothing from the brief text is in the repo.

**Checks I'll show.**
- Notebook runs top to bottom without errors.
- Raw files unchanged (checksums match the first commit).
- Final `git status` and commit log.

**Decision needed.** Go-ahead to push to GitHub.

## Decision log

Each entry records the options considered, the choice made and the reason.

_No decisions recorded yet._
