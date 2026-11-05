"""
Lab 6 - Code (line) coverage tests for blood_donation_screening.py
Swaroop Venkateshwar (PES1UG24CS923)

Goal: execute every line of the module at least once (>= 90% line coverage).

Run:
    coverage run -m pytest CodeCoverageTest_blood_donation_screening.py
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


# ---------- process_donor_cohort ----------

def test_single_accepted_donor():
    result = process_donor_cohort([cohort([donor()])], VOLUME)
    assert result == {"collected_ml": 450, "status": "ACCEPTED"}


def test_invalid_input_raises_value_error():
    # covers the raise line
    with pytest.raises(ValueError):
        process_donor_cohort("not a list", VOLUME)


def test_unregistered_cohort_is_skipped():
    # covers the "continue" for a cohort that is not clinic registered
    result = process_donor_cohort([cohort([donor()], registered=False)], VOLUME)
    assert result == {"collected_ml": 0, "status": "ZERO_YIELD"}


def test_underage_donor_is_deferred():
    # covers the age/weight deferral and the ZERO_YIELD return
    result = process_donor_cohort([cohort([donor(age=16)])], VOLUME)
    assert result == {"collected_ml": 0, "status": "ZERO_YIELD"}


def test_low_hemoglobin_in_high_altitude_cohort_resets_collection():
    # first donor is accepted (450 ml), then a low-hb donor in a high-altitude cohort
    # resets the total to 0 and stops the cohort (break)
    donors = [donor(), donor(hb=11.0), donor()]
    result = process_donor_cohort([cohort(donors, cohort_type="high_altitude")], VOLUME)
    assert result == {"collected_ml": 0, "status": "ZERO_YIELD"}


def test_high_hemoglobin_donor_is_deferred():
    # covers the hb > 18.0 deferral
    result = process_donor_cohort([cohort([donor(hb=18.5), donor()])], VOLUME)
    assert result == {"collected_ml": 450, "status": "ACCEPTED"}


def test_fast_track_cohort_adds_bonus_volume():
    # covers the +50 ml fast-track line
    result = process_donor_cohort([cohort([donor()], fast_track=True)], VOLUME)
    assert result == {"collected_ml": 500, "status": "ACCEPTED"}


def test_more_than_four_deferrals_is_high_deferral():
    # covers the HIGH_DEFERRAL return: 5 deferred donors, 1 accepted
    donors = [donor(age=16)] * 5 + [donor()]
    result = process_donor_cohort([cohort(donors)], VOLUME)
    assert result == {"collected_ml": 450, "status": "HIGH_DEFERRAL"}


# ---------- verify_storage_centrifuge ----------

def test_centrifuge_no_data():
    assert verify_storage_centrifuge([]) == "NO_DATA"


def test_centrifuge_two_consecutive_drops_aborts():
    assert verify_storage_centrifuge([[3500, 2900, 2800]]) == "ABORT_SPIN"


def test_centrifuge_single_drop_then_recovery_is_stable():
    # a drop followed by a normal reading resets the streak
    assert verify_storage_centrifuge([[3500, 2900, 3200, 3100]]) == "STABLE"
