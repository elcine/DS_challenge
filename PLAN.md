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
- Each decision is recorded in the Decision log with the options considered.
  The README Approach section then gets two or three lines on what was chosen
  and why, with a link back to the log.
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

## Stakeholder needs vs what the data supports

Based on the step 2 findings (notebook section 4). No new analysis.

| Stakeholder | What they want | What this data can support | What it cannot support | Data that would close the gap |
|---|---|---|---|---|
| **VP Operations** | Earlier escalation, less disruption | Ranking a new train incident by its risk of becoming long, from fields recorded at the start (symptom, time, location, whether a train run is attached). How often incidents become long, by symptom and place. | When the strongest signals (evacuation, emergency team, power cut, damage) become known, so whether they can be used early. Exact durations: only eight bins, the top one open-ended. Whether escalating earlier would shorten an incident, since durations reflect today's response. | A timestamp for each operational indicator and response action. Duration in minutes. A record of what was done and when. |
| **CFO** | Prioritisation, confidence, measurable financial burden | Where incidents of 5 minutes or more concentrate (line, location, symptom). Incidents per million planned km by line for 2019 to September 2023. Confidence: calibrated probabilities from a model, and uncertainty ranges around rates and model results. | Any cost figure. Riders affected. Minutes of delay beyond 30. Rates per km after September 2023. | Ridership by line and time of day. Duration in minutes. A cost per incident or per delay-minute. Km actually run, up to date. |
| **Public Affairs / Safety** | Clarity on user impact, communication risk, rare severe events | Counts of the rarest events: 524 train incidents of 30 minutes or more (54 to 102 per year), evacuations, fire and smoke symptoms, including in stations. | People affected or injured. Severity of station incidents, which all sit in the lowest duration bin. Whether an incident was a full stop or a slowdown, and which segment of the line was affected. Anything about communications. With so few severe events, any rate or model for them is imprecise. | Passengers affected per incident. Impact type (full stop or slowdown) and the segment affected. A severity or injury field. Duration of station incidents. Complaints and communication logs. |
| **Trend reliability** (all three) | To know whether trends reflect reliability, service volume, reporting or classification | For incidents of 5 minutes or more, the counts follow the STM's published indicator month by month, so their trend can be trusted. Service volume explains little of the change in counts. | Trends in incidents under 5 minutes: the 2025 drop, the drift in symptom and indicator coding, and the 2024 episode where the recorded symptom was wrong cannot be separated from logging practice. Rates per rider. | Documented changes to logging rules and code lists, with dates. Km actually run and ridership. A stable symptom coding, or a mapping between versions. |

**What this implies for the target definition (step 3).**

- A target can only be a threshold on the duration bins, and the part of the
  data that is externally validated starts at 5 minutes. Thresholds at or
  above 5 minutes rest on consistent records; anything that depends on the
  count of shorter incidents inherits the logging uncertainty.
- The stakeholders pull in different directions: escalation needs enough
  positive cases to learn and evaluate on, while rare severe events (30
  minutes or more) are what Public Affairs cares about but number only 54 to
  102 a year. Step 3 has to weigh that trade-off explicitly.

## Steps

Time estimates are rough. The original budget was 3 hours (180 minutes); the
driver analysis added to step 6 brings the total to about 190.

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

**Decision needed.** Target definition and modelling population. Decided: see
D2 in the Decision log.

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
unknown timing. Decided: see D3 in the Decision log.

### Step 5: Validation and metrics decision (~10 min)

**Goal.** Agree how performance will be measured before any model is fitted.

**What I'll do.**
- Propose temporal validation schemes that fit the chosen target (no random
  splits), with the number of positives per fold.
- Propose metrics tied to the stakeholders' questions and to the class balance
  of the chosen target.
- Propose the baselines a model must beat.
- Include a calibration check among the metrics. The stakeholder table
  promises the CFO calibrated probabilities; that claim has to be tested.

**Checks I'll show.**
- Fold boundaries, rows and positives per fold.
- Confirmation that no test period overlaps or precedes its training period.

**Decision needed.** Validation scheme, metrics and baselines. Decided: see D4
in the Decision log.

### Step 6: Modelling and driver analysis (~45 min)

**Goal.** A predictive framework evaluated honestly under the agreed scheme.

**Scope.** Reduced to the items below to fit the time budget (decision D5).
The runs that were cut are listed in the README under "Further analysis (not
done in the time available)".

**What I'll do.**
- Propose candidate models, with trade-offs, given the decided target and
  features. After the decision: implement `src/model.py` and
  `src/evaluate.py`.
- Both baselines: constant rate, and symptom-only rate table.
- Headline feature set with logistic regression and with gradient boosting.
- Strict set (lower bound) and upper-bound set ("if these indicators were
  known in the first minutes") with logistic regression.
- Results per fold (expanding window, test years 2021 to 2024) and pooled.
- The 2025 holdout, scored once, with bootstrap intervals (service days,
  1,000 resamples).
- Calibration of the predicted probabilities.
- The secondary view: the same model scores evaluated against 30 minutes or
  more.
- One sensitivity run on the headline set (decision D1): same folds and
  holdout, with the 525 time/bin mismatch rows excluded from training and
  test, compared with the main run. It tests the key assumption behind the
  target: trusting the published duration bin over the computed time.
- **Driver analysis** (about 10 to 15 minutes, after the models). Looking
  back at historical incidents, break down major incidents (15 minutes or
  more) by primary cause, secondary cause, line and location:
  - each cause's share of all major incidents;
  - its rate of becoming major;
  - a ranking by number of major incidents first, and by delay minutes
    second. The data has no exact minutes, so delay minutes are an estimate:
    the lower edge of the bin for closed bins, and for "30 min et plus" the
    median elapsed time of those incidents (end minus start, about 49
    minutes) instead of 30. The assumption is stated with the table.
  - one table comparing interchange stations (Berri-UQAM, Lionel-Groulx,
    Snowdon, Jean-Talon, from a fixed list, not from the line field) and
    terminal stations against the other locations: share of major incidents
    and rate of becoming major. This is description only, not a model feature.

  Post-analysis causes are legitimate here because the aim is to explain past
  incidents, not to predict new ones. That distinction is stated explicitly
  in the notebook and the README. Results are labelled as associations, with
  a note that cause coding can drift (the 2024 episode).

**Checks I'll show.**
- Metrics per fold and on the final holdout, with uncertainty.
- Comparison against baselines.
- Which features drive predictions, read from the logistic regression
  coefficients, and whether that is plausible.
- Calibration of the predicted probabilities. If it is poor, the "calibrated
  probabilities" cell in the stakeholder table is softened.

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
- **Follow-up.** Step 6 includes one sensitivity run on the headline set
  that excludes the 525 time/bin mismatches from training and test, to show
  whether the choice changes the results.

### D2. Target definition and modelling population (step 3)

Evidence: notebook section 5.

- **Population options.**
  1. Train incidents only (29,167 rows).
  2. All incidents (45,561 rows).
- **Population choice.** Train incidents only.
- **Reason.** All 16,394 station incidents are in the lowest duration bin, so
  they can never be positive. Including them would only dilute the rate and
  flatter any model.

- **Target options** (train incidents; positives, rate, positives per year).

| Option | Positives | Rate | Per year | Main argument for | Main argument against |
|---|---|---|---|---|---|
| A. 5 min or more | 6,413 | 22.0% | 736 to 1,121 | The STM's own published indicator; validated against it | One incident in five; not "major" |
| B. 10 min or more | 2,036 | 7.0% | 229 to 396 | Selective, with a few hundred positives per year | No external definition; highest share of time/bin mismatches |
| C. 15 min or more | 1,103 | 3.8% | 121 to 222 | Defensible as "major"; evacuation in over half | Fewer positives; single-year margins near ±9% |
| D. 30 min or more | 524 | 1.8% | 54 to 102 | Clearest "rare severe event" | 54 positives in 2025; too few to compare models on |
| E. Ordinal (all bins) | n/a | n/a | n/a | Uses all the information | Harder to build, explain and evaluate in the time available |

- **Target choice.**
  - **Primary: C, 15 minutes or more.**
  - **Secondary view: D, 30 minutes or more**, evaluated on the same model
    scores, for Public Affairs / Safety. Thirty minutes or more is used as a
    proxy for rare severe events; severity for Public Affairs / Safety is
    also covered descriptively, through evacuations and fire or smoke
    incidents, including station incidents (step 7).
  - **A, 5 minutes or more**, stays as the link to the STM's indicator in the
    reliability view. It is not treated as "major".
  - **A sensitivity run at B, 10 minutes or more**: not run, listed as
    further analysis (D5).
- **Reason.** 15 minutes is the lowest threshold that can be defended as
  "major" in front of stakeholders. Noise is less of a concern than the
  single-year margins suggest, because model comparison pools the
  rolling-origin folds for 2021 to 2024 (693 positives at 15 minutes or
  more), and 2025 stays out as the one-time final holdout.
- **Open point for step 5 (now closed by D4).** The validation scheme was
  still to be confirmed in step 5. The pooled count depends on it: 693 positives over 2021 to 2024
  with 2025 held out, or 814 if 2025 were included in the folds.

### D3. Feature sets (step 4)

Evidence: notebook section 6. Implemented in `src/features.py`.

- **Options.**

| Option | Fields | Main argument for | Main argument against |
|---|---|---|---|
| 1. Strict | Symptom, line, location (grouped, plus a between-stations flag), hour, weekday, month | Every field is documented or inherent at the start | Weakest; drops cheap and strong first-report fields |
| 2. Strict + first-report fields | Option 1 + train run attached, door involved, emergency brake, vehicle recorded | These describe the triggering event and are plausibly known at once | Their timing is a reading of the fields, not documented |
| 3. Option 2 + response indicators | Option 2 + traction power cut, emergency team, evacuation, material damage, several lines | Far stronger | Mostly consequences of a long incident; evacuation of train and station is 95.6% positive |

- **Choice.**
  - **Headline: option 2**, without "vehicle recorded" (weak, lift 0.86, and
    unclear timing).
  - **Lower bound: option 1**, reported beside the headline.
  - **Upper bound: option 3**, reported only as "if these indicators were
    known in the first minutes". It is not a usable model. Its gap over
    option 2 shows the value of timestamping response actions, which is a
    data-collection recommendation.
  - **No history features.** The number of incidents on the same line in the
    previous 60 minutes shows no relation to the target, and such features
    add leakage risk.
  - **No year feature.** It would encode reporting drift.
- **Handling of line and location.**
  - Multi-line incidents take their first listed line in options 1 and 2. A
    separate "several lines" value would let the model learn that the
    incident spread (21.6% positive) through the back door. "Unknown line" is
    kept only for `Non affecté` and `02-avr`. The "several lines" flag exists
    in option 3 only.
  - The same back door exists in the location code, so it is closed the same
    way: "Berri-UQAM - Ligne 1, 2, 4" becomes "Berri-UQAM", and a code that
    is only a line or a list of lines names no place and joins "other".
  - Locations with at least 100 incidents in the training period keep their
    own value; the rest are grouped as "other". The grouping is learned on
    training data only.
  - Hour is used as recorded.
- **No automated feature selection.** Features were chosen by whether they
  are available when an incident starts, because the main risk here is
  leakage, which no selection algorithm can detect: it would pick the
  evacuation flag first. The set is small (7 to 10 fields). A statistical
  search on a few hundred positives per training fold (289 to 760) would risk
  fitting noise, and would have to be repeated inside each training fold to
  avoid leaking test information. Instead: regularised logistic regression
  shrinks weak features, and the nested feature sets (strict, headline,
  upper bound) are compared explicitly. Permutation importance and a
  single-field ablation would add to this; they are listed as further
  analysis (D5).
- **Reason.** Option 2 is what an operator plausibly has when an incident
  starts. Options 1 and 3 bracket it: one shows what is lost by trusting only
  documented fields, the other what could be gained if response actions were
  timestamped.
- **Notes carried to step 6 and the README.**
  - "Train run attached" may partly overlap with the outcome (with no train
    attached, no train delay can be measured), and its recording drifts
    (14.7% to 23.0% of train incidents without a run). An ablation run,
    option 2 without this field, would show how much of the gain over option
    1 comes from it. Not run: listed as further analysis (D5). The logistic
    regression coefficient for this field is reported instead.
  - The symptom's relation to the target drifts (fire or smoke: 8% in 2019,
    26% in 2025), so performance is shown per fold.
  - Feature effects are associations, not causes.
  - Residual leak, accepted and documented: line-list location codes (280
    rows, 26.8% positive) sit inside the "other" location group (4,574 rows,
    8.2% positive when the grouping is learned on 2019 to 2023). A check
    with those 280 rows excluded is listed as further analysis (D5).

### D4. Validation scheme, metrics and baselines (step 5)

Evidence: notebook section 7. Fold construction in `src/validation.py`.

- **Validation options.**

| Scheme | Description | Main argument for | Main argument against |
|---|---|---|---|
| 1. Expanding window | Test on 2021, 2022, 2023, 2024; train each time on all earlier years | Most training data; 693 pooled test positives; performance visible per year | Early years (pre-COVID, older coding) stay in training |
| 2. Sliding window | Same test years; train on the previous 3 years only | Forgets old reporting practice | About 40% fewer training positives in later folds; window length is one more choice |
| 3. Single split | Train 2019 to 2023, test 2024 | Simplest | One year (222 positives) decides the model |

- **Validation choice.** Scheme 1, with per-fold results shown, for model
  comparison. Scheme 2 as a sensitivity run is listed as further analysis
  (D5).
- **Holdout.** 2025 (January to September): 3,046 train incidents, 121
  positives at 15 minutes or more, 54 at 30 minutes or more. The final model
  is trained on 2019 to 2024. The holdout is used once and never to choose
  between models.
- **Reasons for the holdout.**
  - It is the most recent data and the closest to deployment.
  - Incidents of 5 minutes or more match the STM's published rate, so the
    year looks complete for them.
  - Strike days account for only about 30 incidents.
  - The missing km for 2025 does not matter here: km is not a model feature
    (it measures exposure, not severity), and the rate analysis stops at
    September 2023.
- **Metrics.**
  - **Primary: PR-AUC** (average precision), read against the base rate of
    about 4%.
  - **Operational:** recall and precision among the 5% and the 10%
    highest-scored incidents (two alert budgets).
  - **Calibration:** Brier score against the constant-rate baseline, plus
    predicted versus observed rate by score band.
  - **Secondary:** ROC-AUC.
- **Baselines.** Both: a constant rate (the training base rate for every
  incident), and a symptom-only rate table (each incident gets the training
  rate of its symptom).
- **Uncertainty.** Bootstrap on the holdout, resampling whole service days,
  1,000 resamples. Days are resampled, not incidents, because incidents on
  the same day are not independent (272 holdout days, 22 of them with two or
  more major incidents).
- **Reason.** Pooling four yearly folds gives 693 test positives for model
  comparison, against 121 to 222 for any single year, while keeping the most
  recent year untouched for one final, honest estimate.

### D5. Scope of step 6 reduced (time budget)

- **Options.**
  1. Keep every run added during steps 1 to 5.
  2. Keep the core evaluation and move the extra runs to a "further analysis"
     list.
- **Choice.** Option 2.
  - **Kept:** both baselines; headline set with logistic regression and
    gradient boosting; strict and upper-bound sets with logistic regression;
    per-fold and pooled results; the 2025 holdout with bootstrap intervals;
    calibration; the 30-minute secondary view on the same scores; the
    sensitivity run excluding the 525 time/bin mismatches, on the headline
    set (D1), because it tests the key assumption behind the target; the
    driver analysis. Feature contributions are read from the logistic regression
    coefficients.
  - **Moved to the README, "Further analysis (not done in the time
    available)":** the run-attached ablation (D3), the sliding-window
    sensitivity (D4), the 10-minute target sensitivity (D2), the residual-leak check
    excluding the 280 line-list-location rows (D3), and permutation
    importance (D3).
- **Reason.** Time budget. Step 6 had grown to more than ten separate runs.
  The kept items answer the brief (a justified, validated predictive
  framework plus what drives major incidents); the moved items are
  robustness checks whose absence is stated openly.
- **Effect on earlier entries.** Where D1 to D4 mention a sensitivity run,
  ablation or permutation importance "in step 6", read it as "listed as
  further analysis". The exception is the mismatch sensitivity run in D1,
  which stays in step 6.
