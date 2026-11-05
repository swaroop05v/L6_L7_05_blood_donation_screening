"""
Lab 7 - Fuzz testing processor.py with Hypothesis
Swaroop Venkateshwar (PES1UG24CS923)

Rule used by every fuzz test: for ANY input a function may either
  - return a correct result, or
  - reject the input cleanly with ValueError.
Any other exception (AttributeError, IndexError, KeyError, ZeroDivisionError, ...) is a crash = bug.

Run:
    python -m pytest test_processor.py -v
"""
import math

import pytest
from hypothesis import given, settings, strategies as st

from processor import validate_blood_type, calculate_pulse_pressure, parse_donor_registry

VALID_ANTIGENS = ("A", "B", "AB", "O")
RH_WORDS = ("Positive", "Negative")

# Random garbage that still looks a bit like the real format, so the fuzzer gets past the first split
messy_token = st.one_of(
    st.text(max_size=6),
    st.integers(-1000, 100000).map(str),
    st.floats(allow_nan=True, allow_infinity=True).map(str),
    st.sampled_from(["", " ", "nan", "inf", "-0", "1e400", "0"]),
)


def fail_crash(func_name, value, err):
    pytest.fail(f"{func_name}({value!r}) crashed with {type(err).__name__}: {err}")


# ---------- validate_blood_type ----------

@given(st.text() | st.none())
def test_validate_blood_type_no_crash(s):
    try:
        result = validate_blood_type(s)
    except ValueError:
        return  # invalid input rejected cleanly
    except Exception as err:  # anything else is a crash
        fail_crash("validate_blood_type", s, err)
    # accepted input must give a real blood group, e.g. "AB Positive"
    antigen, rh = result.split(" ")
    assert antigen in VALID_ANTIGENS, f"accepted invalid antigen in {s!r} -> {result!r}"
    assert rh in RH_WORDS


@given(
    st.sampled_from(VALID_ANTIGENS),
    st.sampled_from("+-"),
    st.booleans(),
    st.sampled_from(["", " ", "  ", "\t"]),
)
def test_validate_blood_type_valid_codes(antigen, sign, lower, pad):
    code = f"{pad}{antigen.lower() if lower else antigen}{sign}{pad}"
    expected = f"{antigen} {'Positive' if sign == '+' else 'Negative'}"
    assert validate_blood_type(code) == expected


# ---------- calculate_pulse_pressure ----------

@given(st.text() | st.none())
def test_calculate_pulse_pressure_safe(s):
    try:
        result = calculate_pulse_pressure(s)
    except ValueError:
        return
    except Exception as err:
        fail_crash("calculate_pulse_pressure", s, err)
    assert result.startswith("Diff: ")


@given(st.tuples(messy_token, messy_token).map("/".join))
def test_calculate_pulse_pressure_structured_fuzz(s):
    # "<something>/<something>": numbers, zero, negatives, floats, huge values, text
    try:
        result = calculate_pulse_pressure(s)
    except ValueError:
        return
    except Exception as err:
        fail_crash("calculate_pulse_pressure", s, err)
    diff = int(result.split(",")[0].replace("Diff: ", ""))
    assert diff > 0, f"accepted impossible blood pressure {s!r} -> {result!r}"


@given(st.integers(2, 300).flatmap(lambda sys_: st.tuples(st.just(sys_), st.integers(1, sys_ - 1))))
def test_calculate_pulse_pressure_valid_readings(bp):
    systolic, diastolic = bp
    result = calculate_pulse_pressure(f"{systolic}/{diastolic}")
    assert result == f"Diff: {systolic - diastolic}, Ratio: {round(systolic / diastolic, 2)}"


# ---------- parse_donor_registry ----------

@given(st.text() | st.none())
def test_parse_donor_registry_safe(s):
    try:
        result = parse_donor_registry(s)
    except ValueError:
        return
    except Exception as err:
        fail_crash("parse_donor_registry", s, err)
    assert result.startswith("Donor ")


@settings(max_examples=300)
@given(st.lists(messy_token, min_size=0, max_size=5).map("|".join))
def test_parse_donor_registry_structured_fuzz(s):
    # 0-5 pipe-separated fields of numbers, NaN, infinity, negatives, text
    try:
        result = parse_donor_registry(s)
    except ValueError:
        return
    except Exception as err:
        fail_crash("parse_donor_registry", s, err)
    fields = s.split("|")
    assert len(fields) == 3, f"accepted {len(fields)} fields: {s!r}"
    assert fields[0].strip(), f"accepted an empty donor id: {s!r}"
    weight, hb = float(fields[1]), float(fields[2])
    assert math.isfinite(weight) and math.isfinite(hb), f"accepted NaN/infinity: {s!r}"
    assert weight > 0 and hb > 0, f"accepted a non-positive value: {s!r}"


@given(
    st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=8),
    st.floats(30, 150),
    st.floats(8, 20),
)
def test_parse_donor_registry_valid_records(donor_id, weight, hb):
    result = parse_donor_registry(f"{donor_id}|{weight}|{hb}")
    expected = "Eligible" if weight >= 50.0 and hb >= 12.5 else "Deferred"
    assert result == f"Donor {donor_id}: {expected}"
