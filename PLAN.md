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
- One commit per step, with a clear message, made only after the step has been
  reviewed and the commit approved.
- The challenge instructions (`brief/*.docx`) stay local and are not copied into the repo.
- Each step has a rough time estimate. If a step is running over, I flag it
  before continuing, with what is left and what could be cut.

## Initial observations (to verify in exploration)

First read-only look at the two raw files and their data dictionaries. These
were provisional when written. Step 2 re-checked each one (notebook section 1,
code in `src/verify.py`): 23 confirmed, 5 corrected, 5 taken from the
dictionary and not testable with the data. Corrections are marked
**Corrected** in place, and summarised under
[Verification results](#verification-results-step-2).

### File formats

- Both `.xls` files are plain-text CSV, not Excel workbooks.
  - Incidents: `;` delimiter, UTF-8 with BOM, CRLF line endings, 45,561 rows × 26 columns.
  - Planned km: `,` delimiter, decimal commas in the km column (e.g. `16315,92`), 8,472 rows × 11 columns.
- Signs of a spreadsheet round trip in the incidents file:
  - one `Ligne` value reads `02-avr` (a list of lines converted to a date);
  - `Année civile/mois` is stored as `janv-19`, `févr-19`, etc.
- Incident times follow the service day, not the clock: hours run from 02:00 to
  27:41, in mixed `HH:MM` and `HH:MM:SS` formats. **Corrected:** end times run
  to 29:30; the first look only covered train incidents. `Jour calendaire` is the real
  calendar date, while `Jour du mois` and `Année civile` follow the service day
  (an incident at 24:00 on service day 1 August has `Jour calendaire` 2 August).
  **Corrected:** this holds for every start time of 24:00 or later, but 60
  incidents starting at exactly `02:00` also carry the next calendar date.
- Dictionary and file do not match exactly: `Incident en minutes` is in the file
  but not in the dictionary; `Date du jour (Alpha)` is in the dictionary but not
  in the file.

### Coverage

- Incidents: 2019-01-01 to 2025-09-30, although the snapshot is dated 2026-07-07.
- Planned km: 2019-01-01 to 2023-09-30 only. There is no service-volume
  denominator for the last two years of incidents.
- Planned km, 2019: every line/day appears twice, once with real km and once as
  a zero-km `Non affecté` row. `Tournée` is always `001`. **Corrected:**
  zero-km duplicates also exist in 2020 (76 rows), and for 868 line/days the
  km sits on the `Non affecté` row while the row with a service period is zero.
  Duplicates are identified by km = 0.
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
  with `73` and 2,915 rows with `MR-73`). **Corrected:** the two agree in all
  but 4 rows (`10` without `MPM-10`).
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

### Verification results (step 2)

- **Status:** 23 confirmed, 5 corrected, 5 from the dictionary only.
- **Corrected:** latest time (29:30), calendar date against start time (60
  rows at `02:00`), zero-km rows in 2020, zero-km rows that have a service
  period (868), rolling stock type against secondary cause (4 rows differ).
- **New observations from the exploration** (details and tags in notebook
  section 4):
  - April to September 2025 has 34% fewer train incidents than the same months of 2024.
  - Planned km per day on the yellow line are about a third higher in 2023 than in 2022.
  - Classification drifts over time: symptom mix, door indicator, and the
    share of train incidents without a run number.
  - Six all-day entries at St-Michel in October 2024 fit a closure logged as
    an incident; most time/bin mismatches do not fit that pattern.
- **Analyst observations** (notebook section 2.6), added after step 2:
  - The 2025 maintenance strikes (official strike days from the STM's
    indicators report) lower incident counts on the June strike days but
    explain only about 30 of the 850 incidents missing in April to September
    2025 against 2024.
  - The August to September 2024 spike is 350 rolling-stock symptoms later
    traced to track (`Service de la voie`) at terminal stations. Incidents of
    5 minutes or more spike in September 2024 only.
  - Incidents of 5 minutes or more per million planned km: 9 to 13 for 2019
    to 2023. The 2023 value (13.2, January to September) equals the STM's
    published 13.2 for 2023.
  - Month by month, the count of incidents of 5 minutes or more follows the
    STM's published monthly rate for 2024 and 2025 (correlation 0.995 and
    0.977), including the September 2024 peak and the 2025 decline. Up to
    September 2025 the dataset is consistent with being complete for
    incidents of 5 minutes or more.
  - 216 train incidents (0.74%) share a date, line and start minute with
    another incident; 12 are exact duplicates.
  - A 15-minute threshold was added to the duration summaries for step 3.

## Limitations to carry into the README

Points to state in the README limitations section (step 7). No analysis needed.

- **Elapsed time is an upper bound on disruption.** The start and end times
  are the customer-delay window, which may include periods of partial service.
  End minus start therefore overstates how long service was fully interrupted.
- **Durations reflect current practice.** How long an incident lasts depends
  on how the STM responds today. A model trained on these durations predicts
  "long under current practice", and acting on its predictions would change
  the data that future versions are trained on.

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
(regenerated by code). Decided: committed, and regenerated from raw in the
final pass (step 8).

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

**Decision needed.** How to treat the flagged rows: keep as is, correct, or
exclude. Decided: see D1 in the Decision log.

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
- Hypothesis to check: some time/bin mismatches are closure periods logged as
  incidents. The all-day Saint-Michel entries in October 2024 coincide with
  that station's closure in fall 2024. Check where and when the all-day
  entries cluster; treat the link as a hypothesis, not a fact.

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
- One sensitivity run that excludes the 525 train incidents whose elapsed time
  disagrees with their duration bin (decision D1), compared with the main run.

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
- Bring station incidents back in one paragraph for Public Affairs / Safety:
  they are left out of the exploration plots, but fire and smoke incidents in
  stations matter for user impact and communication risk. Supported by a
  simple count by symptom and year.
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
- Regenerate `data/processed/` from raw before the last commit, so the
  committed files are exactly what the committed code produces.
- Remove dead code, check comments, confirm nothing from the brief text is in the repo.

**Checks I'll show.**
- Notebook runs top to bottom without errors.
- Raw files unchanged (checksums match the first commit).
- `git status` clean after regenerating `data/processed/` (no difference from
  the committed files).
- Final `git status` and commit log.

**Decision needed.** Go-ahead to push to GitHub.

## Decision log

Each entry records the options considered, the choice made and the reason.

### D1. Treatment of flagged rows (step 1)

Step 1 flagged 584 of 45,561 incident rows without changing them: 1 corrupted
line value (`02-avr`), 525 train incidents whose end minus start time falls
outside their duration bin, and 60 rows whose calendar date and start time
disagree.

- **Options.**
  1. Keep all flagged rows and correct none.
  2. Exclude the 525 time/bin mismatches from modelling.
  3. Correct values by inference (for example, guess the original line behind `02-avr`).
- **Choice.** Option 1. Keep all flagged rows, trust the duration bin over the
  elapsed time, and treat the `02-avr` line as unknown.
- **Reason.** The duration bin is the published measure of service delay.
  Excluding rows would rely on a rule that cannot be verified, and guessing
  values would be invention. The date/time disagreement only matters if hour
  of day becomes a feature, so it is revisited in step 4.
- **Follow-up.** Step 6 includes one sensitivity run that excludes the 525
  time/bin mismatches, to show whether the choice changes the results.
