"""
Lab 6 - Branch coverage tests for blood_donation_screening.py
Swaroop Venkateshwar (PES1UG24CS923)

Goal: every decision (if / for) takes both its True and False path (>= 90% branch coverage).
Line coverage alone is not enough: e.g. a test where the cohort IS fast-track runs every line,
but never checks what happens when it is NOT fast-track.

Run:
    coverage run --branch -m pytest BranchCoverageTest_blood_donation_screening.py
    coverage report -m
"""
import pytest

from blood_donation_screening import process_donor_cohort, verify_storage_centrifuge

VOLUME = 450


def donor(age=25, weight_kg=65, hb=14.0):
    return {"age": age, "weight_kg": weight_kg, "hb": hb}


def cohort(donors, registered=True, cohort_type="standard", fast_track=False):
    return {
        "clinic_registered": registered,
        "type": cohort_type,
        "fast_track": fast_track,
        "donors": donors,
    }


# ---------- input validation: if not isinstance(...) or standard_volume_ml <= 0 ----------

@pytest.mark.parametrize(
    "cohorts, volume",
    [
        ("not a list", VOLUME),  # first condition True
        (None, VOLUME),
        ([], 0),  # list, but volume is zero
        ([], -100),  # list, but volume is negative
    ],
)
def test_invalid_input_raises(cohorts, volume):
    with pytest.raises(ValueError, match="Invalid cohort list or volume"):
        process_donor_cohort(cohorts, volume)


def test_empty_cohort_list_is_zero_yield():
    # valid input (False branch of the check) and the cohort loop runs zero times
    assert process_donor_cohort([], VOLUME) == {"collected_ml": 0, "status": "ZERO_YIELD"}


# ---------- cohort loop ----------

def test_unregistered_cohort_skipped_registered_counted():
    # registered False -> continue; registered True -> processed
    cohorts = [cohort([donor()], registered=False), cohort([donor()])]
    assert process_donor_cohort(cohorts, VOLUME) == {"collected_ml": 450, "status": "ACCEPTED"}


def test_missing_registration_flag_defaults_to_skipped():
    # .get("clinic_registered", False) -> default False
    assert process_donor_cohort([{"donors": [donor()]}], VOLUME)["status"] == "ZERO_YIELD"


def test_cohort_without_donors_key():
    # .get("donors", []) -> donor loop runs zero times
    assert process_donor_cohort([{"clinic_registered": True}], VOLUME)["status"] == "ZERO_YIELD"


def test_missing_type_defaults_to_standard_so_low_hb_does_not_reset():
    # no "type" key -> "standard": a low-hb donor is deferred but collection is kept
    c = {"clinic_registered": True, "donors": [donor(), donor(hb=10.0), donor()]}
    assert process_donor_cohort([c], VOLUME) == {"collected_ml": 900, "status": "ACCEPTED"}


# ---------- age / weight check: if age < 17 or weight < 50 ----------

@pytest.mark.parametrize(
    "age, weight, expected_ml",
    [
        (16, 65, 0),  # too young
        (25, 49, 0),  # too light
        (17, 50, 450),  # exactly on both limits -> accepted
    ],
)
def test_age_and_weight_limits(age, weight, expected_ml):
    result = process_donor_cohort([cohort([donor(age=age, weight_kg=weight)])], VOLUME)
    assert result["collected_ml"] == expected_ml


def test_donor_with_missing_fields_is_deferred():
    # missing age/weight default to 0 -> deferred
    assert process_donor_cohort([cohort([{}])], VOLUME)["status"] == "ZERO_YIELD"


# ---------- hemoglobin checks ----------

@pytest.mark.parametrize(
    "hb, expected_ml",
    [
        (12.4, 0),  # just below 12.5 -> deferred
        (12.5, 450),  # lower limit -> accepted
        (18.0, 450),  # upper limit -> accepted
        (18.1, 0),  # just above 18.0 -> deferred
    ],
)
def test_hemoglobin_limits(hb, expected_ml):
    result = process_donor_cohort([cohort([donor(hb=hb)])], VOLUME)
    assert result["collected_ml"] == expected_ml


def test_low_hb_high_altitude_resets_and_stops_cohort():
    # high_altitude True branch: total reset to 0 and break (the third donor is never processed)
    donors = [donor(), donor(hb=11.0), donor()]
    result = process_donor_cohort([cohort(donors, cohort_type="high_altitude")], VOLUME)
    assert result == {"collected_ml": 0, "status": "ZERO_YIELD"}


def test_low_hb_high_altitude_reset_also_wipes_earlier_cohorts():
    # the reset sets the running total to 0, so volume from an earlier cohort is lost too
    cohorts = [cohort([donor()]), cohort([donor(hb=11.0)], cohort_type="high_altitude")]
    assert process_donor_cohort(cohorts, VOLUME) == {"collected_ml": 0, "status": "ZERO_YIELD"}


def test_low_hb_standard_cohort_keeps_going():
    # high_altitude False branch: deferred, but the loop continues
    donors = [donor(), donor(hb=11.0), donor()]
    assert process_donor_cohort([cohort(donors)], VOLUME) == {"collected_ml": 900, "status": "ACCEPTED"}


def test_high_altitude_cohort_with_normal_hb_collects_normally():
    donors = [donor(), donor()]
    result = process_donor_cohort([cohort(donors, cohort_type="high_altitude")], VOLUME)
    assert result == {"collected_ml": 900, "status": "ACCEPTED"}


# ---------- fast track ----------

def test_fast_track_bonus_only_for_fast_track_cohorts():
    cohorts = [cohort([donor()], fast_track=True), cohort([donor()], fast_track=False)]
    assert process_donor_cohort(cohorts, VOLUME) == {"collected_ml": 950, "status": "ACCEPTED"}


def test_fast_track_bonus_applies_even_after_high_altitude_reset():
    # after the break, the fast-track check still runs, so 50 ml is added to the reset total
    c = cohort([donor(), donor(hb=11.0)], cohort_type="high_altitude", fast_track=True)
    assert process_donor_cohort([c], VOLUME) == {"collected_ml": 50, "status": "ACCEPTED"}


def test_fast_track_on_unregistered_cohort_is_ignored():
    c = cohort([donor()], registered=False, fast_track=True)
    assert process_donor_cohort([c], VOLUME)["status"] == "ZERO_YIELD"


# ---------- final status ----------

def test_exactly_four_deferrals_is_not_high_deferral():
    donors = [donor(age=16)] * 4 + [donor()]
    assert process_donor_cohort([cohort(donors)], VOLUME) == {"collected_ml": 450, "status": "ACCEPTED"}


def test_five_deferrals_is_high_deferral_even_with_zero_yield():
    # HIGH_DEFERRAL is checked before ZERO_YIELD
    donors = [donor(age=16), donor(weight_kg=40), donor(hb=11.0), donor(hb=19.0), donor(age=10)]
    assert process_donor_cohort([cohort(donors)], VOLUME) == {"collected_ml": 0, "status": "HIGH_DEFERRAL"}


def test_deferrals_counted_across_cohorts():
    cohorts = [cohort([donor(age=16)] * 3), cohort([donor(hb=19.0)] * 2 + [donor()])]
    assert process_donor_cohort(cohorts, VOLUME) == {"collected_ml": 450, "status": "HIGH_DEFERRAL"}


# ---------- verify_storage_centrifuge ----------

@pytest.mark.parametrize("runs", [[], None])
def test_centrifuge_no_data(runs):
    assert verify_storage_centrifuge(runs) == "NO_DATA"


@pytest.mark.parametrize(
    "runs, expected",
    [
        ([[3500, 3600, 3000]], "STABLE"),  # never below 3000 (3000 itself is fine)
        ([[3500, 2900, 3200, 2950]], "STABLE"),  # drops, but never two in a row
        ([[2999, 2999]], "ABORT_SPIN"),  # two consecutive drops
        ([[3500, 3400], [3100, 2500, 2400, 3500]], "ABORT_SPIN"),  # second run fails
        ([[2900], [2900]], "STABLE"),  # streak resets for every new run
        ([[]], "STABLE"),  # a run with no readings
    ],
)
def test_centrifuge_runs(runs, expected):
    assert verify_storage_centrifuge(runs) == expected
