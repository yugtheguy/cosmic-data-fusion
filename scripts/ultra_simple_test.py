"""Ultra-simple test to identify the failing case"""
from app.services.temporal_calculator import TemporalCalculator, UncertaintyClass

calc = TemporalCalculator()

test_cases = [
    (2016, "HIGH_CONFIDENCE"),
    (7016, "HIGH_CONFIDENCE"),
    (12016, "ACCEPTABLE"),
    (22016, "APPROXIMATE"),
    (32016, "EXTREME_RANGE"),
    (52016, "EXTREME_RANGE"),
    (72016, "UNRELIABLE"),
]

print("Testing each case:")
for epoch, expected_name in test_cases:
    result = calc.calculate_position_at_epoch(
        ra_deg=180.0, dec_deg=0.0,
        pmra_mas_yr=50, pmdec_mas_yr=50,
        target_epoch=epoch
    )
    
    actual_name = result.uncertainty_class.name
    match = "OK" if actual_name == expected_name else "FAIL"
    
    print(f"{match} | Epoch {epoch} | Expected: {expected_name:20} | Got: {actual_name:20}")
    
    if match == "FAIL":
        print(f"   Delta: {result.delta_years}, Uncertainty: {result.uncertainty_arcsec:.2f}")
