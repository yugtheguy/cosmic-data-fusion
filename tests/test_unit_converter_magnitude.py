"""
Unit tests for magnitude conversion functionality.

Tests the UnitConverter.normalize_magnitude() and flux conversion methods
with known astronomical values and edge cases.
"""

import pytest
import math
from app.services.utils.unit_converter import UnitConverter


class TestMagnitudeNormalization:
    """Test magnitude conversion between photometric systems."""
    
    def test_same_filter_returns_unchanged(self):
        """Test that converting to same filter returns input."""
        mag = 10.5
        result = UnitConverter.normalize_magnitude(mag, "G", "G")
        assert result == mag
        
        result = UnitConverter.normalize_magnitude(mag, "V", "V")
        assert result == mag
    
    def test_gaia_g_to_johnson_v(self):
        """Test Gaia G-band to Johnson V conversion."""
        # For a G2V star with G=10.0 and G-RP=0.6
        gaia_g = 10.0
        color_index = 0.6
        
        result = UnitConverter.normalize_magnitude(
            gaia_g, 
            source_filter="G", 
            target_filter="V",
            color_index=color_index
        )
        
        # Expected: V ≈ G - 0.01*(G-RP) - 0.02 = 10.0 - 0.006 - 0.02 = 9.974
        assert result is not None
        assert abs(result - 9.974) < 0.01
    
    def test_gaia_g_to_v_without_color(self):
        """Test Gaia G to V conversion without color index."""
        gaia_g = 10.0
        
        result = UnitConverter.normalize_magnitude(
            gaia_g,
            source_filter="G",
            target_filter="V"
        )
        
        # Without color, assumes solar-type: V ≈ G - 0.03
        assert result is not None
        assert abs(result - 9.97) < 0.01
    
    def test_2mass_j_to_h_conversion(self):
        """Test 2MASS J to H band conversion."""
        j_mag = 12.0
        
        result = UnitConverter.normalize_magnitude(
            j_mag,
            source_filter="J",
            target_filter="H"
        )
        
        # J-H ≈ 0.30 for G-type stars
        # H ≈ J + 0.30 = 12.30
        assert result is not None
        assert abs(result - 12.30) < 0.01
    
    def test_2mass_j_to_k_conversion(self):
        """Test 2MASS J to K band conversion."""
        j_mag = 12.0
        
        result = UnitConverter.normalize_magnitude(
            j_mag,
            source_filter="J",
            target_filter="K"
        )
        
        # J-K ≈ 0.50 for G-type stars
        # K ≈ J + 0.50 = 12.50
        assert result is not None
        assert abs(result - 12.50) < 0.01
    
    def test_filter_name_case_insensitive(self):
        """Test that filter names are case-insensitive."""
        mag = 10.0
        
        result1 = UnitConverter.normalize_magnitude(mag, "g", "v")
        result2 = UnitConverter.normalize_magnitude(mag, "G", "V")
        result3 = UnitConverter.normalize_magnitude(mag, "G", "v")
        
        # All should give same result
        assert result1 == result2 == result3
    
    def test_none_magnitude_returns_none(self):
        """Test that None input returns None."""
        result = UnitConverter.normalize_magnitude(None, "G", "V")
        assert result is None
    
    def test_unsupported_conversion_returns_original(self):
        """Test that unsupported conversions return original with warning."""
        mag = 10.0
        
        # X to Y conversion doesn't exist
        result = UnitConverter.normalize_magnitude(
            mag,
            source_filter="X",
            target_filter="Y"
        )
        
        # Should return original magnitude
        assert result == mag


class TestFluxToMagnitude:
    """Test flux to magnitude conversions."""
    
    def test_basic_flux_to_magnitude(self):
        """Test basic flux to magnitude conversion (AB system)."""
        # At magnitude 0, flux = zero-point flux = 3631 Jy
        flux = 3631.0
        result = UnitConverter.flux_to_magnitude(flux)
        
        assert result is not None
        assert abs(result - 0.0) < 0.001
    
    def test_magnitude_zero_point(self):
        """Test that zero-point flux gives magnitude 0."""
        zp = 3631.0
        result = UnitConverter.flux_to_magnitude(zp, flux_zero_point=zp)
        
        assert result is not None
        assert abs(result - 0.0) < 0.001
    
    def test_bright_object_negative_magnitude(self):
        """Test that bright objects (high flux) have negative magnitudes."""
        # 10x brighter = -2.5 mag
        flux = 36310.0  # 10x zero-point
        result = UnitConverter.flux_to_magnitude(flux)
        
        assert result is not None
        assert abs(result - (-2.5)) < 0.001
    
    def test_faint_object_positive_magnitude(self):
        """Test that faint objects (low flux) have positive magnitudes."""
        # 10x fainter = +2.5 mag
        flux = 363.1  # 0.1x zero-point
        result = UnitConverter.flux_to_magnitude(flux)
        
        assert result is not None
        assert abs(result - 2.5) < 0.001
    
    def test_magnitude_formula_accuracy(self):
        """Test magnitude formula with known values."""
        # m = -2.5 * log10(flux / flux_zp)
        flux = 1000.0
        flux_zp = 3631.0
        
        expected = -2.5 * math.log10(flux / flux_zp)
        result = UnitConverter.flux_to_magnitude(flux, flux_zero_point=flux_zp)
        
        assert result is not None
        assert abs(result - expected) < 0.001
    
    def test_zero_flux_returns_none(self):
        """Test that zero flux returns None."""
        result = UnitConverter.flux_to_magnitude(0.0)
        assert result is None
    
    def test_negative_flux_returns_none(self):
        """Test that negative flux returns None."""
        result = UnitConverter.flux_to_magnitude(-100.0)
        assert result is None
    
    def test_none_flux_returns_none(self):
        """Test that None flux returns None."""
        result = UnitConverter.flux_to_magnitude(None)
        assert result is None
    
    def test_invalid_zero_point_returns_none(self):
        """Test that invalid zero-point returns None."""
        result = UnitConverter.flux_to_magnitude(1000.0, flux_zero_point=0.0)
        assert result is None
        
        result = UnitConverter.flux_to_magnitude(1000.0, flux_zero_point=-10.0)
        assert result is None


class TestMagnitudeToFlux:
    """Test magnitude to flux conversions (inverse)."""
    
    def test_magnitude_zero_gives_zero_point(self):
        """Test that magnitude 0 gives zero-point flux."""
        zp = 3631.0
        result = UnitConverter.magnitude_to_flux(0.0, flux_zero_point=zp)
        
        assert result is not None
        assert abs(result - zp) < 0.01
    
    def test_round_trip_conversion(self):
        """Test flux → magnitude → flux round trip."""
        original_flux = 1000.0
        zp = 3631.0
        
        # Convert to magnitude
        mag = UnitConverter.flux_to_magnitude(original_flux, flux_zero_point=zp)
        assert mag is not None
        
        # Convert back to flux
        recovered_flux = UnitConverter.magnitude_to_flux(mag, flux_zero_point=zp)
        assert recovered_flux is not None
        
        # Should match original (within floating point precision)
        assert abs(recovered_flux - original_flux) < 0.01
    
    def test_magnitude_formula_inverse(self):
        """Test inverse magnitude formula."""
        mag = 10.0
        zp = 3631.0
        
        # flux = zp * 10^(-mag/2.5)
        expected = zp * math.pow(10.0, -mag / 2.5)
        result = UnitConverter.magnitude_to_flux(mag, flux_zero_point=zp)
        
        assert result is not None
        assert abs(result - expected) < 0.01
    
    def test_none_magnitude_returns_none(self):
        """Test that None magnitude returns None."""
        result = UnitConverter.magnitude_to_flux(None)
        assert result is None
    
    def test_invalid_zero_point_returns_none(self):
        """Test that invalid zero-point returns None."""
        result = UnitConverter.magnitude_to_flux(10.0, flux_zero_point=0.0)
        assert result is None


class TestMagnitudeEdgeCases:
    """Test edge cases and error handling."""
    
    def test_very_bright_magnitude(self):
        """Test handling of very bright objects (m < -10)."""
        mag = -15.0
        flux = UnitConverter.magnitude_to_flux(mag)
        
        assert flux is not None
        assert flux > 0
        
        # Round trip
        recovered_mag = UnitConverter.flux_to_magnitude(flux)
        assert recovered_mag is not None
        assert abs(recovered_mag - mag) < 0.01
    
    def test_very_faint_magnitude(self):
        """Test handling of very faint objects (m > 25)."""
        mag = 28.0
        flux = UnitConverter.magnitude_to_flux(mag)
        
        assert flux is not None
        assert flux > 0
        
        # Round trip
        recovered_mag = UnitConverter.flux_to_magnitude(flux)
        assert recovered_mag is not None
        assert abs(recovered_mag - mag) < 0.01
    
    def test_extreme_magnitude_warning(self):
        """Test that extreme magnitudes generate warnings."""
        # This should work but generate a warning
        very_high_flux = 3631.0 * 10**20  # Should give m ≈ -50
        mag = UnitConverter.flux_to_magnitude(very_high_flux)
        
        # Should still return a value (with warning logged)
        assert mag is not None
        assert mag < -30  # Very negative


class TestMagnitudeIntegration:
    """Integration tests with realistic astronomical scenarios."""
    
    def test_gaia_star_conversion(self):
        """Test conversion of typical Gaia star magnitude."""
        # Typical Gaia measurement: G=12.5, G-RP=0.7 (slightly red star)
        gaia_g = 12.5
        g_rp = 0.7
        
        johnson_v = UnitConverter.normalize_magnitude(
            gaia_g,
            source_filter="G",
            target_filter="V",
            color_index=g_rp
        )
        
        assert johnson_v is not None
        # V should be slightly brighter than G for red stars
        assert johnson_v < gaia_g
        assert abs(johnson_v - 12.47) < 0.1  # Expected ~12.47
    
    def test_sdss_magnitude_chain(self):
        """Test SDSS g → V → flux conversion chain."""
        sdss_g = 15.0
        
        # Convert SDSS g to Johnson V
        johnson_v = UnitConverter.normalize_magnitude(
            sdss_g,
            source_filter="G",
            target_filter="V"
        )
        
        assert johnson_v is not None
        
        # Convert magnitude to flux
        flux = UnitConverter.magnitude_to_flux(johnson_v)
        assert flux is not None
        assert flux > 0
        
        # Convert back
        recovered_mag = UnitConverter.flux_to_magnitude(flux)
        assert recovered_mag is not None
        assert abs(recovered_mag - johnson_v) < 0.01
    
    def test_2mass_infrared_chain(self):
        """Test 2MASS J → H → K conversion chain."""
        j_mag = 11.0
        
        # J to H
        h_mag = UnitConverter.normalize_magnitude(j_mag, "J", "H")
        assert h_mag is not None
        assert h_mag > j_mag  # H is fainter (redder)
        
        # H to K
        k_mag = UnitConverter.normalize_magnitude(h_mag, "H", "K")
        assert k_mag is not None
        assert k_mag > h_mag  # K is even fainter
        
        # J to K directly
        k_mag_direct = UnitConverter.normalize_magnitude(j_mag, "J", "K")
        assert k_mag_direct is not None
        
        # Should be approximately equal (within 0.05 mag)
        assert abs(k_mag - k_mag_direct) < 0.05


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
