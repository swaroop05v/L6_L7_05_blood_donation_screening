import math

# Fixed after fuzz testing (Lab 7): every function now checks its input and raises
# ValueError with a clear message, instead of crashing with AttributeError / IndexError /
# KeyError / ZeroDivisionError or silently accepting impossible values.

VALID_ANTIGENS = ("A", "B", "AB", "O")
RH_MAP = {"+": "Positive", "-": "Negative"}
MAX_BP_MMHG = 400  # anything above this is not a real blood pressure reading


def validate_blood_type(blood_code):
    """
    Standardizes blood group and Rh factor (e.g. 'O+', 'AB-').
    Raises ValueError unless the input is an ABO antigen (A, B, AB, O) followed by + or -.
    """
    if not isinstance(blood_code, str):
        raise ValueError("Blood type must be text, e.g. 'O+'")
    cleaned = blood_code.strip().upper()
    if len(cleaned) < 2:
        raise ValueError("Blood type is too short, e.g. 'O+'")
    antigen = cleaned[:-1]
    rh_char = cleaned[-1]
    if antigen not in VALID_ANTIGENS:
        raise ValueError(f"Unknown blood group '{antigen}' (use A, B, AB or O)")
    if rh_char not in RH_MAP:
        raise ValueError(f"Rh factor must be + or -, got '{rh_char}'")
    return f"{antigen} {RH_MAP[rh_char]}"


def calculate_pulse_pressure(bp_string):
    """
    Calculates pulse pressure (systolic - diastolic) and arterial ratio.
    Expects 'systolic/diastolic' (e.g. '120/80') with 0 < diastolic < systolic <= 400.
    """
    if not isinstance(bp_string, str):
        raise ValueError("Blood pressure must be text, e.g. '120/80'")
    parts = bp_string.split('/')
    if len(parts) != 2:
        raise ValueError("Blood pressure must look like 'systolic/diastolic', e.g. '120/80'")
    try:
        systolic = int(parts[0])
        diastolic = int(parts[1])
    except ValueError:
        raise ValueError("Systolic and diastolic must be whole numbers") from None
    if not 0 < diastolic < systolic <= MAX_BP_MMHG:
        raise ValueError("Need 0 < diastolic < systolic <= 400 mmHg")
    pulse_diff = systolic - diastolic
    ratio = round(systolic / diastolic, 2)
    return f"Diff: {pulse_diff}, Ratio: {ratio}"


def parse_donor_registry(donor_entry):
    """
    Parses pipe-delimited record: 'DonorID|WeightKg|Hemoglobin'.
    Raises ValueError unless there are exactly 3 fields, a non-empty ID and
    positive, finite numbers for weight and hemoglobin.
    """
    if not isinstance(donor_entry, str):
        raise ValueError("Donor record must be text, e.g. 'D101|65|13.5'")
    fields = donor_entry.split('|')
    if len(fields) != 3:
        raise ValueError(f"Donor record needs 3 fields (ID|Weight|Hemoglobin), got {len(fields)}")
    donor_id = fields[0].strip()
    if not donor_id:
        raise ValueError("Donor ID is empty")
    try:
        weight = float(fields[1])
        hemoglobin = float(fields[2])
    except ValueError:
        raise ValueError("Weight and hemoglobin must be numbers") from None
    if not (math.isfinite(weight) and math.isfinite(hemoglobin)):
        raise ValueError("Weight and hemoglobin must be real numbers (not NaN or infinity)")
    if weight <= 0 or hemoglobin <= 0:
        raise ValueError("Weight and hemoglobin must be greater than zero")
    eligible = weight >= 50.0 and hemoglobin >= 12.5
    return f"Donor {donor_id}: {'Eligible' if eligible else 'Deferred'}"


def run_step(label, func, prompt):
    value = input(prompt)
    try:
        print(label, func(value))
    except ValueError as err:
        print("Invalid input:", err)


def main():
    print("==== Running validate_blood_type ====")
    run_step("Validated:", validate_blood_type, "Enter blood type (e.g. A+, O-, AB+): ")

    print("\n==== Running calculate_pulse_pressure ====")
    run_step("BP Metrics:", calculate_pulse_pressure, "Enter BP (e.g. 120/80): ")

    print("\n==== Running parse_donor_registry ====")
    run_step("Status:", parse_donor_registry, "Enter record (ID|Weight|Hemoglobin): ")


if __name__ == "__main__":
    main()
