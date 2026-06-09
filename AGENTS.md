# AGENTS.md — Instructions for the coding agent

This directory is a **spec-driven development** package. The spec is in `README.md` and `evals/eval_cases.json`. The implementation is your job. Do not modify the spec without an explicit request from the user.

## Read order

1. `README.md` — the trust anchor. Read it all.
2. `SKILL.md` — what Claude does at runtime when the skill triggers.
3. `evals/eval_cases.json` — the 21 cases that define correct behavior.
4. `scripts/*.py` — the three stub files. Read all three before writing any code; they share types and contracts.

## Implementation order

Do these in order. Do not skip ahead.

1. **`scripts/query_lhs.py`** — the foundation. Everything else depends on `lookup()`.
   - Run `pytest evals/test_pipeline.py::TestBuildKey evals/test_pipeline.py::TestNearestNPoints evals/test_pipeline.py::TestLookup` after.
   - All those tests must pass before moving on.
2. **`scripts/save_csv.py`** — depends on `query_lhs.lookup`.
   - Run `pytest evals/test_pipeline.py::TestSaveCSV` after.
3. **`scripts/convert_csv.py`** — independent of the other two; depends only on a CSV existing.
   - Run `pytest evals/test_pipeline.py::TestConvertCSV` after.
4. **`evals/run_eval.py`** — the end-to-end runner. Implement only after the three scripts pass unit tests.
5. **Set `LHS_DB_PATH` in `query_lhs.py`** to the real DB path the user provides.

## Hard rules

- **Do not change the spec.** If a test seems wrong, surface it to the user before adjusting. The cases in `eval_cases.json` reflect deliberate decisions, not guesses.
- **Do not add behavior not in the spec.** No caching, no MCP wrapping, no fallback design generation, no fuzzy key matching beyond what's specified. If you find yourself wanting to, stop and ask.
- **Numbers come from Python, never from Claude.** The L step parses; the D scripts do all arithmetic and lookups. If you see yourself writing prompt instructions that ask the model to compute something, that's a bug.
- **Every failure becomes a case, not a retry.** If a behavior is wrong, the fix is `eval_cases.json` + script change, not "be more careful next time."

## Testing

- Unit tests: `pytest evals/test_pipeline.py` — must run in seconds.
- Eval set: `python evals/run_eval.py --mode=dry-run` first (sanity-check the cases), then run the skill against each prompt, then `--mode=replay`.
- The fixture pickle at `evals/fixtures/mini_lhs.p` is already built. Do not regenerate it unless explicitly asked — its contents are part of the test contract.

## When you're stuck

- If a stub's TODO is ambiguous, prefer the simpler reading and note the assumption in a comment.
- If two parts of the spec seem to conflict, surface to the user. Do not silently pick.
- If a test fails and you don't see why, check whether the spec actually allows the behavior the code produces — the spec is the source of truth.

## What "done" looks like

- All unit tests in `evals/test_pipeline.py` pass.
- `python evals/run_eval.py --mode=dry-run` prints all 21 cases without error.
- A manual eval pass (running Claude-with-the-skill on the 21 prompts) produces traces, and `python evals/run_eval.py --mode=replay` shows ≥ 20/21 passing. The one that may be borderline is the parsing of compact notation `40x3` — flag it for human review if it doesn't pass; do not patch the spec.
