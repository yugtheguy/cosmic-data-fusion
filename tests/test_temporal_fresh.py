"""
Fresh test file with new name to avoid any caching issues
Testing extended temporal range (±50,000 years)
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Force fresh import
for module in list(sys.modules.keys()):
    if 'temporal_calculator' in module:
        del sys.modules[module]

from app.services.temporal_calculator import TemporalCalculator, UncertaintyClass

def main():
    print("=" * 80)
    print("FRESH TEST - Extended Temporal Range")
    print("=" * 80)
    print()
    
    calc = TemporalCalculator()
    
    # First, verify EXTREME_RANGE exists
    print("Step 1: Verify EXTREME_RANGE enum exists")
    print(f"Available uncertainty classes:")
    for cls in UncertaintyClass:
        print(f"  - {cls.name}: '{cls.value}'")
    print()
    
    # Test cases
    test_cases = [
        (2016, "HIGH_CONFIDENCE", "Reference epoch"),
        (7016, "HIGH_CONFIDENCE", "+5,000 years"),
        (12016, "ACCEPTABLE", "+10,000 years"),
        (22016, "APPROXIMATE", "+20,000 years"),
        (32016, "EXTREME_RANGE", "+30,000 years"),
        (52016, "EXTREME_RANGE", "+50,000 years"),
        (72016, "UNRELIABLE", "+60,000 years"),
    ]
    
    print("Step 2: Run test cases")
    print()
    
    all_passed = True
    
    for epoch, expected_class_name, description in test_cases:
        result = calc.calculate_position_at_epoch(
            ra_deg=180.0, dec_deg=0.0,
            pmra_mas_yr=50, pmdec_mas_yr=50,
            target_epoch=epoch
        )
        
        # Get expected class by name
        expected_class = getattr(UncertaintyClass, expected_class_name)
        
        # Check if it matches
        passed = result.uncertainty_class == expected_class
        status = "[PASS]" if passed else "[FAIL]"
        
        print(f"{status} {description:20} | Expected: {expected_class.value:20} | Got: {result.uncertainty_class.value:20}")
        
        if not passed:
            all_passed = False
            print(f"     ERROR: Expected {expected_class_name} but got {result.uncertainty_class.name}")
            print(f"     Uncertainty: {result.uncertainty_arcsec:.2f} arcsec")
            print(f"     Delta years: {result.delta_years}")
    
    print()
    print("=" * 80)
    
    if all_passed:
        print("SUCCESS: ALL TESTS PASSED!")
        print("=" * 80)
        return 0
    else:
        print("FAILURE: SOME TESTS FAILED")
        print("=" * 80)
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
