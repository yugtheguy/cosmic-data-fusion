"""Simple test to verify EXTREME_RANGE class works"""
import sys
# Force reload
if 'app.services.temporal_calculator' in sys.modules:
    del sys.modules['app.services.temporal_calculator']

from app.services.temporal_calculator import TemporalCalculator, UncertaintyClass

calc = TemporalCalculator()

# Test +50,000 years
result = calc.calculate_position_at_epoch(
    ra_deg=180.0, dec_deg=0.0,
    pmra_mas_yr=100, pmdec_mas_yr=100,
    target_epoch=52016
)

print(f"Delta years: {result.delta_years}")
print(f"Uncertainty: {result.uncertainty_arcsec:.2f} arcsec ({result.uncertainty_arcsec/3600:.2f} degrees)")
print(f"Threshold: 36000 arcsec (10 degrees)")
print(f"Class: {result.uncertainty_class.value}")
print(f"Expected: extreme_range")
print()

if result.uncertainty_class == UncertaintyClass.EXTREME_RANGE:
    print("✅ TEST PASSED!")
else:
    print(f"❌ TEST FAILED - Got {result.uncertainty_class.value} instead of extreme_range")
    print(f"Debug: Checking threshold constant...")
    print(f"THRESHOLD_EXTREME_RANGE = {calc.THRESHOLD_EXTREME_RANGE}")
