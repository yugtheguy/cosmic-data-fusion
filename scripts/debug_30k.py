"""Minimal debug test"""
from app.services.temporal_calculator import TemporalCalculator, UncertaintyClass

calc = TemporalCalculator()

# Test the exact case that's failing
result = calc.calculate_position_at_epoch(
    ra_deg=180.0, dec_deg=0.0,
    pmra_mas_yr=50, pmdec_mas_yr=50,
    target_epoch=32016
)

print(f"Epoch: 32016 (+30,000 years)")
print(f"Uncertainty: {result.uncertainty_arcsec:.2f} arcsec")
print(f"Class: {result.uncertainty_class}")
print(f"Class value: {result.uncertainty_class.value}")
print(f"Expected: UncertaintyClass.EXTREME_RANGE")
print(f"Match: {result.uncertainty_class == UncertaintyClass.EXTREME_RANGE}")
print()

# Check enum values
print("Available classes:")
for cls in UncertaintyClass:
    print(f"  - {cls.name}: {cls.value}")
