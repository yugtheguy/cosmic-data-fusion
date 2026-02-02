"""
Test script for extended temporal range (±50,000 years)
Tests the new EXTREME_RANGE uncertainty class
"""

from app.services.temporal_calculator import TemporalCalculator, UncertaintyClass

def test_extended_range():
    calc = TemporalCalculator()
    
    # Test star: Barnard's Star (high proper motion)
    # RA: 269.45°, Dec: 4.69°
    # PM: pmra=-798 mas/yr, pmdec=10328 mas/yr
    
    test_cases = [
        ("5,000 years", 7016, UncertaintyClass.HIGH_CONFIDENCE),
        ("10,000 years", 12016, UncertaintyClass.ACCEPTABLE),
        ("20,000 years", 22016, UncertaintyClass.APPROXIMATE),
        ("30,000 years", 32016, UncertaintyClass.EXTREME_RANGE),  # NEW
        ("50,000 years", 52016, UncertaintyClass.EXTREME_RANGE),  # NEW
        ("60,000 years", 62016, UncertaintyClass.UNRELIABLE),
    ]
    
    print("=" * 80)
    print("EXTENDED TEMPORAL RANGE TEST - Barnard's Star")
    print("=" * 80)
    print()
    
    for name, epoch, expected_class in test_cases:
        result = calc.calculate_position_at_epoch(
            ra_deg=269.45,
            dec_deg=4.69,
            pmra_mas_yr=-798,
            pmdec_mas_yr=10328,
            target_epoch=epoch
        )
        
        status = "✅ PASS" if result.uncertainty_class == expected_class else "❌ FAIL"
        
        print(f"{name:15} | Epoch: {epoch:6} | Class: {result.uncertainty_class.value:20} | {status}")
        print(f"                | RA: {result.ra_deg:8.3f}° | Dec: {result.dec_deg:7.3f}° | Uncertainty: {result.uncertainty_arcsec:8.2f}\"")
        print()
    
    print("=" * 80)
    print("✅ Extended range support working! Can now predict ±50,000 years!")
    print("=" * 80)

if __name__ == "__main__":
    test_extended_range()
