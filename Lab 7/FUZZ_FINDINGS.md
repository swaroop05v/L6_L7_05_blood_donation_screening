# Lab 7 – Fuzz testing findings (Hypothesis)

Swaroop Venkateshwar (PES1UG24CS923)

**Rule checked by every fuzz test:** for any input, a function must either return a correct result or reject the input cleanly with `ValueError`. Any other exception is a crash.

## Before the fix: `fuzz_bugs_found.png`

`python -m pytest test_processor.py -v --tb=no -rf` → **5 failed, 3 passed.** Hypothesis found 14 distinct failures, each shrunk to a minimal input:

| Function | Minimal failing input | Problem |
|---|---|---|
| `validate_blood_type` | `None` | crash: `AttributeError` (`.strip()` on None) |
| | `''` | crash: `IndexError` (`cleaned[-1]` on empty string) |
| | `'0'` | crash: `KeyError` (unknown Rh sign) |
| | `'Z+'` | accepted an invalid blood group → `'Z Positive'` |
| `calculate_pulse_pressure` | `None` | crash: `AttributeError` |
| | `'0/0'` | crash: `ZeroDivisionError` |
| | `'0/1'` | accepted an impossible reading → `'Diff: -1'` |
| `parse_donor_registry` | `None` | crash: `AttributeError` |
| | `''`, `'|0'` | crash: `IndexError` (fewer than 3 fields) |
| | `'|0|0|'` | accepted 4 fields |
| | `'|0|0'` | accepted an empty donor ID |
| | `'D1|nan|13'` | accepted NaN / infinity as weight |

## Fix (`processor.py`)

- Every function checks that the input is a string.
- Blood type: must be exactly A, B, AB or O followed by `+` or `-` (case and spaces ignored).
- Blood pressure: exactly two whole numbers with `0 < diastolic < systolic <= 400`, so there is no division by zero and no negative pulse pressure.
- Donor record: exactly 3 fields, a non-empty ID, and weight and hemoglobin as positive, finite numbers.
- Invalid input raises `ValueError` with a clear message. `main()` prints that message instead of crashing.

## After the fix: `fuzz_all_passing.png`

All 8 tests pass. They were also re-run locally with 2,000 random examples per test, five times, with no failures.
