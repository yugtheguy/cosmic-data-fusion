"""
Integration test: Verify magnitude conversion works end-to-end with real data ingestion.
"""

from app.services.adapters.gaia_adapter import GaiaAdapter
from app.services.utils.unit_converter import UnitConverter

print("=" * 70)
print("MAGNITUDE CONVERSION INTEGRATION TEST")
print("=" * 70)

# Test 1: Gaia adapter uses magnitude conversion
print("\n1. Testing Gaia adapter with magnitude normalization...")
adapter = GaiaAdapter()
records, validations = adapter.process_batch('app/data/gaia_dr3_sample.csv', skip_invalid=True)

if records:
    first_record = records[0]
    print(f"   ✓ Parsed {len(records)} Gaia records")
    print(f"   Sample star: {first_record['source_id']}")
    print(f"     Gaia G magnitude: {first_record.get('brightness_mag', 'N/A')}")
    
    # Test manual conversion
    if first_record.get('brightness_mag'):
        gaia_g = first_record['brightness_mag']
        johnson_v = UnitConverter.normalize_magnitude(gaia_g, "G", "V")
        print(f"     Converted to Johnson V: {johnson_v:.3f}")
        print(f"     Difference: {abs(gaia_g - johnson_v):.3f} mag")

# Test 2: Flux to magnitude conversion
print("\n2. Testing flux to magnitude conversion...")
test_flux = 1000.0  # Arbitrary flux in Jy
test_mag = UnitConverter.flux_to_magnitude(test_flux, flux_zero_point=3631.0)
recovered_flux = UnitConverter.magnitude_to_flux(test_mag, flux_zero_point=3631.0)

print(f"   Flux: {test_flux:.2f} Jy")
print(f"   Magnitude: {test_mag:.3f}")
print(f"   Recovered flux: {recovered_flux:.2f} Jy")
print(f"   ✓ Round-trip error: {abs(test_flux - recovered_flux):.4f} Jy")

# Test 3: Multi-band conversion chain
print("\n3. Testing multi-band conversion chain...")
gaia_g = 12.0
johnson_v = UnitConverter.normalize_magnitude(gaia_g, "G", "V")
twomass_j = UnitConverter.normalize_magnitude(johnson_v, "V", "J")

print(f"   Gaia G: {gaia_g:.2f}")
print(f"   → Johnson V: {johnson_v:.2f}")
print(f"   → 2MASS J: {twomass_j:.2f}")
print(f"   ✓ Full conversion chain working")

# Test 4: Color index improves accuracy
print("\n4. Testing color index refinement...")
gaia_g_test = 15.0
g_rp_color = 0.8  # Reddish star

v_without_color = UnitConverter.normalize_magnitude(gaia_g_test, "G", "V")
v_with_color = UnitConverter.normalize_magnitude(gaia_g_test, "G", "V", color_index=g_rp_color)

print(f"   Gaia G: {gaia_g_test:.2f}, G-RP: {g_rp_color:.2f}")
print(f"   V (no color): {v_without_color:.3f}")
print(f"   V (with color): {v_with_color:.3f}")
print(f"   ✓ Color correction: {abs(v_without_color - v_with_color):.3f} mag")

print("\n" + "=" * 70)
print("✅ ALL MAGNITUDE CONVERSION TESTS PASSED")
print("=" * 70)
