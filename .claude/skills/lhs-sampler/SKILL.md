---
name: lhs-sampler
description: Retrieves pre-computed Latin hypercube designs from a pickle database and returns them as CSV, numpy, pandas, or pytorch. Use this skill whenever the user asks for a Latin hypercube sampling, LHS, design of experiment, DoE, initial sampling, sampling design, or any phrasing requesting a sample of N points across D dimensions (e.g. "I need 40 points in 3 dimensions"). Also use for followup conversion requests once a CSV has been produced ("make that numpy instead"). Do not use this skill for generating new designs from scratch, for non-Latin-hypercube design types like Sobol or factorial, or for arbitrary tabular data conversion unrelated to LHS retrieval.
---

# lhs-sampler

Retrieve a pre-computed Latin hypercube design from a pickle database and deliver it in the user's requested format.

## What this skill does

Looks up a design keyed by `dd<n_dims>_nn<n_points>` in a pickle file at the path defined in `scripts/query_lhs.py`. Returns the design as CSV, numpy, pandas, or pytorch. If anything is ambiguous or missing, asks the user before doing anything.

**Important:** All script paths below are relative to the repo root (`/home/user/testing_claude_code`). Always run scripts as `python /home/user/testing_claude_code/scripts/<script>.py`, not as relative paths.

## Workflow

### Step 1: Parse the request

Extract three fields from the user's message:

- `n_points` — integer, required
- `n_dims` — integer, required
- `format` — one of `numpy`, `pandas`, `pytorch`, `csv`; or null if unspecified

The user may use any of these terms for the request and they all mean the same thing: *Latin hypercube*, *Latin hypercube sampling*, *LHS*, *design of experiment*, *DoE*, *initial sampling*, *sampling design*. Treat them as synonyms.

Numbers may be in digits ("40") or words ("forty"). Order varies ("3 dimensions and 40 points" = "40 points in 3 dimensions"). Compact notation may appear ("40×3").

### Step 2: Decide whether to clarify

Apply these rules **in order**. If any fires, stop and ask the user — do not proceed.

1. **`n_points` is missing or unparseable** → ask: "How many points do you want in the design?"
2. **`n_dims` is missing or unparseable** → ask: "How many dimensions?"
3. **Both missing** → ask: "I need to know the number of points and the number of dimensions. What sizes do you need?"
4. **Size is given as a vague word** ("small," "a few," "moderate," "large," "big," "tiny") → ask: "Roughly how many points? I don't want to guess." **Never substitute a number for a vague word.**
5. **Conflicting numbers** ("40 points, no wait 50") → ask which the user meant.
6. **`format` is missing** → **do not ask yet.** Proceed; default to CSV; ask about format *after* delivering.
7. **`format` is an unrecognized value** (e.g. "polars," "JSON") → proceed as if format were missing (CSV + followup ask).

If none of these fire, proceed to step 3.

### Step 3: Look up the design

Run `python /home/user/testing_claude_code/scripts/query_lhs.py` with the parsed `n_points` and `n_dims`. It returns one of:

- The ndarray, shape `(n_points, n_dims)` — proceed to step 4.
- `KeyNotFoundSameDim(nearby=[…])` — clarify: list the closest 3 available `n_points` at this `n_dims`, ask the user to pick or revise. Do not proceed.
- `KeyNotFoundNoDim` — say: "I don't have any designs with `<n_dims>` dimensions in the database. The available dimensions are: `<list>`." Do not suggest substituting.

### Step 4: Deliver in the requested format

| Requested format | Action |
|---|---|
| `csv` (explicit) | Run `python /home/user/testing_claude_code/scripts/save_csv.py`; surface the file with `present_files`. |
| `numpy` | Run `python /home/user/testing_claude_code/scripts/save_csv.py` then `python /home/user/testing_claude_code/scripts/convert_csv.py --format numpy`; return the array. |
| `pandas` | Same, with `--format pandas`. Columns are `x1, x2, …, xD`. |
| `pytorch` | Same, with `--format pytorch`. dtype `float32`. |
| Unspecified (default) | Run `python /home/user/testing_claude_code/scripts/save_csv.py`, surface the file, then ask: "Saved as CSV. Want it as numpy, pandas, or pytorch instead?" |

### Step 5: Write the trace

Every run — success, clarification, or error — appends one JSON file to `traces/`. The schema is in `README.md` section 3.3. The trace is what the eval suite reads. Without it, no eval works.

## Followup turns (format conversion)

If the previous skill turn delivered a CSV and asked about format, and the user replies with a format name ("numpy please," "make it a tensor"), do **not** re-look-up the design. Run `python /home/user/testing_claude_code/scripts/convert_csv.py` on the existing CSV path (recorded in the previous trace's `csv_path` field) and return the converted form. Write a new trace with `followup_pending: false`.

If the user replies with something other than a format ("yes," "thanks," or a new request), treat that turn as a new request and run the workflow from step 1.

## Hard rules

- **Never substitute a number for a vague word.** "Small" is not 10, not 20, not anything. Ask.
- **Never silently fall back** to a nearby key. If `dd3_nn40` is missing, do not return `dd3_nn39` without asking.
- **Never generate a design.** This skill only retrieves. If the database doesn't have it, say so.
- **The model never produces the numeric values in the design.** Those come from the pickle, via Python, every time.

## Scripts

- `/home/user/testing_claude_code/scripts/query_lhs.py` — lookup + nearby-alternatives
- `/home/user/testing_claude_code/scripts/save_csv.py` — ndarray → CSV in `/mnt/user-data/outputs/`
- `/home/user/testing_claude_code/scripts/convert_csv.py` — CSV → numpy | pandas | pytorch

See `README.md` for the full contract and `evals/eval_cases.json` for the curated test set.
