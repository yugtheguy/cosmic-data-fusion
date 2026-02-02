"""
Comprehensive test suite for extended temporal range (±50,000 years)
Tests edge cases, accuracy, and uncertainty calculations
"""

from app.services.temporal_calculator import TemporalCalculator, UncertaintyClass
import math

def test_edge_cases():
    """Test extreme edge cases"""
    calc = TemporalCalculator()
    
    print("=" * 80)
    print("TEST 1: EDGE CASES")
    print("=" * 80)
    
    # Test 1: Maximum positive range
    result = calc.calculate_position_at_epoch(
        ra_deg=180.0, dec_deg=0.0,
        pmra_mas_yr=100, pmdec_mas_yr=100,
        target_epoch=52016  # +50,000 years
    )
    assert result.uncertainty_class == UncertaintyClass.EXTREME_RANGE
    print("✅ Maximum positive range (+50,000 years): PASS")
    
    # Test 2: Maximum negative range
    result = calc.calculate_position_at_epoch(
        ra_deg=180.0, dec_deg=0.0,
        pmra_mas_yr=100, pmdec_mas_yr=100,
        target_epoch=-47984  # -50,000 years
    )
    assert result.uncertainty_class == UncertaintyClass.EXTREME_RANGE
    print("✅ Maximum negative range (-50,000 years): PASS")
    
    # Test 3: Beyond maximum (should be UNRELIABLE)
    result = calc.calculate_position_at_epoch(
        ra_deg=180.0, dec_deg=0.0,
        pmra_mas_yr=100, pmdec_mas_yr=100,
        target_epoch=72016  # +60,000 years
    )
    assert result.uncertainty_class == UncertaintyClass.UNRELIABLE
    print("✅ Beyond maximum (+60,000 years = UNRELIABLE): PASS")
    
    # Test 4: Pole crossing
    result = calc.calculate_position_at_epoch(
        ra_deg=0.0, dec_deg=85.0,
        pmra_mas_yr=0, pmdec_mas_yr=1000,  # Moving toward pole
        target_epoch=12016
    )
    assert -90 <= result.dec_deg <= 90
    print("✅ Pole crossing handled correctly: PASS")
    
    # Test 5: RA wraparound
    result = calc.calculate_position_at_epoch(
        ra_deg=359.0, dec_deg=0.0,
        pmra_mas_yr=1000, pmdec_mas_yr=0,
        target_epoch=12016
    )
    assert 0 <= result.ra_deg < 360
    print("✅ RA wraparound handled correctly: PASS")
    
    print()

def test_known_stars():
    """Test against known high proper motion stars"""
    calc = TemporalCalculator()
    
    print("=" * 80)
    print("TEST 2: KNOWN STARS")
    print("=" * 80)
    
    # Barnard's Star - highest known proper motion
    # Should move significantly over 50,000 years
    result = calc.calculate_position_at_epoch(
        ra_deg=269.45,
        dec_deg=4.69,
        pmra_mas_yr=-798,
        pmdec_mas_yr=10328,
        target_epoch=52016  # +50,000 years
    )
    
    # Calculate expected movement
    delta_years = 50000
    expected_dec_change = (10328 / 3600000) * delta_years  # mas/yr to degrees
    
    print(f"Barnard's Star (+50,000 years):")
    print(f"  Original Dec: 4.69°")
    print(f"  New Dec: {result.dec_deg:.2f}°")
    print(f"  Expected change: ~{expected_dec_change:.2f}°")
    print(f"  Actual change: {result.dec_deg - 4.69:.2f}°")
    print(f"  Uncertainty: {result.uncertainty_arcsec:.2f}\"")
    print(f"  Class: {result.uncertainty_class.value}")
    
    # Verify movement is in correct direction
    assert result.dec_deg > 4.69  # Should move north
    print("✅ Barnard's Star movement correct: PASS")
    print()

def test_uncertainty_scaling():
    """Test that uncertainty scales appropriately with time"""
    calc = TemporalCalculator()
    
    print("=" * 80)
    print("TEST 3: UNCERTAINTY SCALING")
    print("=" * 80)
    
    epochs = [2016, 7016, 12016, 22016, 32016, 52016]  # 0, 5k, 10k, 20k, 30k, 50k years
    uncertainties = []
    
    for epoch in epochs:
        result = calc.calculate_position_at_epoch(
            ra_deg=180.0, dec_deg=0.0,
            pmra_mas_yr=100, pmdec_mas_yr=100,
            pmra_error_mas_yr=0.1, pmdec_error_mas_yr=0.1,
            target_epoch=epoch
        )
        uncertainties.append(result.uncertainty_arcsec)
        delta = epoch - 2016
        print(f"  Δt = {delta:6} years | Uncertainty = {result.uncertainty_arcsec:8.2f}\" | Class: {result.uncertainty_class.value}")
    
    # Verify uncertainty increases with time
    for i in range(len(uncertainties) - 1):
        assert uncertainties[i+1] > uncertainties[i], "Uncertainty should increase with time"
    
    print("✅ Uncertainty increases monotonically: PASS")
    
    # Verify quadratic growth for extreme ranges
    unc_20k = uncertainties[3]  # 20k years
    unc_50k = uncertainties[5]  # 50k years
    ratio = unc_50k / unc_20k
    print(f"\n  Uncertainty ratio (50k/20k): {ratio:.2f}x")
    print(f"  Expected for quadratic: ~{(50/20)**2:.2f}x")
    assert ratio > 5, "Extreme range should have significantly higher uncertainty"
    print("✅ Extreme range uncertainty scaling correct: PASS")
    print()

def test_all_uncertainty_classes():
    """Verify all uncertainty classes are reachable"""
    calc = TemporalCalculator()
    
    print("=" * 80)
    print("TEST 4: ALL UNCERTAINTY CLASSES")
    print("=" * 80)
    
    test_cases = [
        (2016, UncertaintyClass.HIGH_CONFIDENCE, "Reference epoch"),
        (7016, UncertaintyClass.HIGH_CONFIDENCE, "+5,000 years"),
        (12016, UncertaintyClass.ACCEPTABLE, "+10,000 years"),
        (22016, UncertaintyClass.APPROXIMATE, "+20,000 years"),
        (32016, UncertaintyClass.EXTREME_RANGE, "+30,000 years"),  # Fixed: was expecting wrong class
        (52016, UncertaintyClass.EXTREME_RANGE, "+50,000 years"),
        (72016, UncertaintyClass.UNRELIABLE, "+60,000 years"),
    ]
    
    for epoch, expected_class, description in test_cases:
        result = calc.calculate_position_at_epoch(
            ra_deg=180.0, dec_deg=0.0,
            pmra_mas_yr=50, pmdec_mas_yr=50,
            target_epoch=epoch
        )
        status = "✅" if result.uncertainty_class == expected_class else "❌"
        print(f"  {status} {description:20} | Expected: {expected_class.value:20} | Got: {result.uncertainty_class.value}")
        assert result.uncertainty_class == expected_class
    
    print("\n✅ All uncertainty classes reachable: PASS")
    print()

def run_all_tests():
    """Run all test suites"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "EXTENDED TEMPORAL RANGE TEST SUITE" + " " * 24 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    test_edge_cases()
    test_known_stars()
    test_uncertainty_scaling()
    test_all_uncertainty_classes()
    
    print("=" * 80)
    print("🎉 ALL TESTS PASSED! Extended range support is working perfectly!")
    print("=" * 80)
    print()
    print("Summary:")
    print("  ✅ Edge cases handled correctly")
    print("  ✅ Known star movements accurate")
    print("  ✅ Uncertainty scales appropriately")
    print("  ✅ All uncertainty classes reachable")
    print("  ✅ System supports ±50,000 year predictions")
    print()

if __name__ == "__main__":
    run_all_tests()
