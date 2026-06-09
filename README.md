# lhs-sampler — Trust Anchor

**Status:** spec, pre-implementation
**Last reviewed:** 2026-05-26

This document is the single source of truth for what the `lhs-sampler` skill does and what counts as "done." Every other artifact in this directory (`SKILL.md`, `eval_cases.json`, the scripts) implements this spec. If a script disagrees with this document, the document wins until we explicitly revise it here.

---

## 1. Purpose

A skill that takes a natural-language request for a Latin hypercube design (or DoE, initial sampling, etc.) and returns the requested design from a pre-built pickle database. The skill performs no design generation of its own — it is a lookup-and-format service over a fixed database.

## 2. Inputs

A single English string from the user, in any reasonable phrasing, naming at minimum:

- **`n_points`** (integer, required) — number of sample points.
- **`n_dims`** (integer, required) — number of dimensions.

Optionally:

- **`format`** (one of: `numpy`, `pandas`, `pytorch`, `csv`) — output format.

Trigger phrases that the skill must recognize as requests for this service: *Latin hypercube*, *LHS*, *design of experiment*, *DoE*, *initial sampling*, *sampling design*, plus generic *"sample N points in D dimensions"* phrasing.

## 3. Outputs

### 3.1 Success

A trace JSON is written to `traces/<timestamp>_<id>.json` regardless of outcome. Every successful response is built from the design **after columnwise min-max normalization to [0, 1]** (performed inside `query_lhs.lookup()` — see section 5). On success:

- **CSV** (default, or explicitly requested): file saved to `/mnt/user-data/outputs/lhs_dd<D>_nn<N>.csv`, surfaced to the user via `present_files`. Values are normalized.
- **numpy**: a **string code snippet** of the form `x = np.array([[...], ...])`, returned in-conversation. The skill does not produce a live `numpy.ndarray`.
- **pandas**: a **string code snippet** `x = pd.DataFrame([[...], ...], columns=['x1', ..., 'xD'])`.
- **pytorch**: a **string code snippet** `x = torch.tensor([[...], ...], dtype=torch.float32)`.

The skill runs on stdlib Python only. The `numpy` / `pandas` / `pytorch` outputs are text the user can paste into their own environment. The only place `numpy` is imported is `scripts/query_lhs.py`, and only to unpickle the database.

When format is **unspecified**, the default is CSV plus a followup question asking whether the user wants it rendered as numpy, pandas, or pytorch. The skill does *not* eagerly produce both — CSV first, then conversion on a second turn if requested.

### 3.2 Clarification

When the request is ambiguous or the design isn't available, the skill returns a concise natural-language question and writes a trace with `clarification_needed: true`. No partial execution. The user's next turn supplies the missing info.

### 3.3 Trace JSON schema

Every run writes exactly one trace file. Fields:

```json
{
  "timestamp": "ISO-8601 string",
  "run_id": "short hex id, 6 chars",
  "raw_request": "the user's verbatim string",
  "parsed": {
    "n_points": "int or null",
    "n_dims": "int or null",
    "format": "one of: numpy, pandas, pytorch, csv, null"
  },
  "clarification_needed": "bool",
  "clarification_reason": "one of: missing_n_points, missing_n_dims, missing_both, vague_size, conflicting_input, key_not_in_db_same_dim, key_not_in_db_no_dim, null",
  "missing_fields": "list of strings, or null",
  "db_key_attempted": "string or null, e.g. 'dd3_nn40'",
  "key_found": "bool or null",
  "nearby_alternatives": "list of ints (n_points values at same n_dims), or null",
  "csv_path": "string path or null",
  "output_format_delivered": "string or null",
  "output_shape": "[N, D] or null",
  "followup_pending": "bool — true when CSV delivered but format ask is open",
  "error": "string or null"
}
```

The trace is the substrate for evaluation. Every `eval_cases.json` case asserts on fields of this trace. The trace and the eval are the same artifact viewed from two sides.

## 4. Clarification rules (the encoded contract)

These are not heuristics; they are rules. The skill must follow them exactly.

| Trigger | Action |
|---|---|
| `n_points` missing or unparseable | Clarify. Reason: `missing_n_points`. |
| `n_dims` missing or unparseable | Clarify. Reason: `missing_n_dims`. |
| Both missing | Clarify both. Reason: `missing_both`. |
| Size given as vague word ("small," "a few," "moderate," "large") | Clarify. Reason: `vague_size`. **Never silently pick a default.** |
| Conflicting numbers ("40 points, no wait 50") | Clarify. Reason: `conflicting_input`. |
| Both parsed, but `dd<D>_nn<N>` not in DB, and other `n_points` values exist at this `n_dims` | Clarify. Reason: `key_not_in_db_same_dim`. List nearby `n_points` (closest 3 by absolute distance). |
| Both parsed, but no designs exist at `n_dims=D` in DB | Clarify. Reason: `key_not_in_db_no_dim`. Say so explicitly. Do not suggest other dimensions. |
| `format` missing | **Do not clarify before running.** Default to CSV, deliver it, then ask. |
| `format` value unrecognized (e.g. "as a polars dataframe") | Clarify. Treat as a `missing_format`-style case → deliver CSV and ask, do not error. |

## 5. L/D split

| Step | Type | Implementation |
|---|---|---|
| Parse natural language → structured params | **L** (Claude, in-skill) | The skill prompt instructs Claude to extract and either populate the trace's `parsed` field or set `clarification_needed: true`. |
| Build DB key from params | **D** | `f"dd{n_dims}_nn{n_points}"` in `query_lhs.py`. |
| Look up key in pickle | **D** | `db[key]` in `query_lhs.py`. |
| Normalize columns to [0, 1] | **D** | `normalize()` in `query_lhs.py`, called by `lookup()` before returning. |
| Find nearby alternatives when key missing | **D** | Filter `db.keys()` by `n_dims`, return nearest `n_points` values. |
| Save normalized rows → CSV | **D** | Stdlib `csv.writer` in `save_csv.py`. |
| Render CSV → numpy / pandas / pytorch code snippet | **D** | Three branches in `convert_csv.py`. Output is a string, not a live object. |
| Compose user-facing reply | **L** (thin) | Natural-language wrapper around structured outcome. |

**Critical:** numbers and keys *never* pass through model judgment. The parser produces integers; everything downstream is code.

## 6. Worked examples

See `eval_cases.json` for the full curated set of 21 cases. The five worth reading first:

1. `happy_basic_numpy`: "I want a sampling with 40 points in 3 dimensions in a numpy array" → numpy ndarray (40, 3).
2. `happy_no_format_default_csv`: "I want an LHS with 40 points in 3 dimensions" → CSV delivered + followup ask.
3. `missing_dims`: "give me 30 points for my LHS" → clarify, reason `missing_n_dims`.
4. `vague_small`: "give me a small LHS in 4 dimensions" → clarify, reason `vague_size`. **Do not pick a number.**
5. `missing_key_same_dim`: "75 points, 3 dimensions, numpy" → suggest nearby N at D=3.

## 7. What this skill does NOT do

- Does not generate designs (no scipy/pyDOE fallback).
- Does not remember previous turns beyond the immediate followup for format conversion.
- Does not modify the pickle database.
- Does not handle non-Latin-hypercube design types (Sobol, Halton, factorial, etc.) — those would be a different skill if needed.
- Does not run scripts with user-controlled DB paths; the path is set in `query_lhs.py` (configurable, but by the developer, not by request input).

## 8. Configuration

The pickle path is hardcoded as a module-level constant `LHS_DB_PATH` in `scripts/query_lhs.py`. To point at a different database, edit that file. No environment variables, no runtime arguments from the user.

### 8.1 Dependencies

The runtime skill is **stdlib-only**. Only `scripts/query_lhs.py` imports `numpy`, and only to unpickle the database (the pickle stores `numpy.ndarray` objects). All downstream work — normalization, CSV writing, code-snippet rendering — is plain Python.

`evals/fixtures/build_fixture.py` uses `numpy` to build the test fixture; that script is run once, offline, and is not part of the skill's runtime path.

## 9. Ratchet rules (for future failures)

When the skill misbehaves, **do not retry with "be more careful."** Apply one of:

| Failure | Encoding |
|---|---|
| Parser misreads phrasing | Add case to `eval_cases.json`; if a convention is missing, add a specific line to `SKILL.md` naming the failure it prevents. |
| Numeric extraction wrong | Tighten / replace with a regex in `query_lhs.py`. Move from L to D. |
| Missing-key handling wrong | Add case to `eval_cases.json`; add guard in `query_lhs.py`. |
| CSV written wrong place / collision | Add guard in `save_csv.py`. |
| Wrong dtype / shape on conversion | Unit test in `test_pipeline.py`. |

Every line in `SKILL.md` should trace back to a specific historical failure. The first commit's `SKILL.md` contains only lines justified by the spec above; nothing speculative.

## 10. Open questions deferred

- Two-turn flow for unspecified format may feel awkward in practice. If it does, we revisit (eager-deliver-and-ask alternative noted in conversation).
- Cost/latency of pickle load is unmeasured. If load is slow enough to feel sluggish, consider module-level caching.
- LLM-as-judge for clarification *prose quality* is deferred. Currently we only assert structural correctness of trace fields.

These are explicitly out of scope for v1.
