"""Debug script to check uncertainty values"""
from app.services.temporal_calculator import TemporalCalculator, UncertaintyClass

calc = TemporalCalculator()

# Test case that's failing
result = calc.calculate_position_at_epoch(
    ra_deg=180.0, dec_deg=0.0,
    pmra_mas_yr=100, pmdec_mas_yr=100,
    target_epoch=52016  # +50,000 years
)

print(f"Epoch: {result.epoch}")
print(f"Delta years: {result.delta_years}")
print(f"Uncertainty (arcsec): {result.uncertainty_arcsec}")
print(f"Uncertainty (degrees): {result.uncertainty_arcsec / 3600}")
print(f"Uncertainty class: {result.uncertainty_class.value}")
print()
print(f"Expected: EXTREME_RANGE")
print(f"Threshold: <36000 arcsec (<10 degrees)")
print(f"Actual: {result.uncertainty_arcsec} arcsec ({result.uncertainty_arcsec / 3600:.2f} degrees)")
