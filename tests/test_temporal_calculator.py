"""
Unit tests for Temporal Calculator Service

Tests cover:
1. Basic position calculations
2. Coordinate wrapping (RA at 0°/360°)
3. Pole handling (Dec at ±90°)
4. Uncertainty classification
5. Edge cases (no PM data, extreme time deltas)
"""

import pytest
import math
from app.services.temporal_calculator import (
    TemporalCalculator,
    UncertaintyClass,
    batch_calculate_positions,
    format_epoch_display
)


class TestTemporalCalculator:
    """Test suite for TemporalCalculator class."""
    
    @pytest.fixture
    def calculator(self):
        """Create calculator instance with default settings."""
        return TemporalCalculator()
    
    def test_initialization(self, calculator):
        """Test calculator initializes with correct default epoch."""
        assert calculator.reference_epoch == 2016.0
    
    def test_basic_forward_motion(self, calculator):
        """Test forward time calculation with positive proper motion."""
        # Star at RA=100°, Dec=+30°
        # Moving +10 mas/yr in RA, +5 mas/yr in Dec
        # 1000 years forward
        result = calculator.calculate_position_at_epoch(
            ra_deg=100.0,
            dec_deg=30.0,
            pmra_mas_yr=10.0,
            pmdec_mas_yr=5.0,
            target_epoch=3016.0  # 1000 years after ref epoch
        )
        
        # Expected change:
        # RA: +10 mas/yr * 1000 yr = 10000 mas = 10 arcsec = 0.00278 deg
        # Dec: +5 mas/yr * 1000 yr = 5000 mas = 5 arcsec = 0.00139 deg
        
        assert result.ra_deg == pytest.approx(100.00278, rel=1e-5)
        assert result.dec_deg == pytest.approx(30.00139, rel=1e-5)
        assert result.epoch == 3016.0
        assert result.delta_years == 1000.0
        assert result.uncertainty_class == UncertaintyClass.HIGH_CONFIDENCE
    
    def test_backward_time_calculation(self, calculator):
        """Test backward time (historical epoch)."""
        result = calculator.calculate_position_at_epoch(
            ra_deg=50.0,
            dec_deg=20.0,
            pmra_mas_yr=20.0,
            pmdec_mas_yr=-10.0,
            target_epoch=-3000.0  # 5016 years before ref epoch
        )
        
        # PM should be reversed
        assert result.delta_years == -5016.0
        # RA should decrease (negative delta * positive PM)
        assert result.ra_deg < 50.0
        # Dec should increase (negative delta * negative PM)
        assert result.dec_deg > 20.0
    
    def test_ra_wraparound_forward(self, calculator):
        """Test RA wraps correctly at 360°."""
        # Star near RA=359°, moving eastward
        result = calculator.calculate_position_at_epoch(
            ra_deg=359.0,
            dec_deg=0.0,
            pmra_mas_yr=3600000.0,  # 1 deg/yr
            pmdec_mas_yr=0.0,
            target_epoch=2018.0  # 2 years forward
        )
        
        # Should wrap to ~1° (359 + 2 = 361 -> 1)
        assert result.ra_deg == pytest.approx(1.0, abs=0.1)
    
    def test_ra_wraparound_backward(self, calculator):
        """Test RA wraps correctly when crossing 0°."""
        # Star near RA=1°, moving backward in time westward
        result = calculator.calculate_position_at_epoch(
            ra_deg=1.0,
            dec_deg=0.0,
            pmra_mas_yr=3600000.0,  # 1 deg/yr eastward
            pmdec_mas_yr=0.0,
            target_epoch=2014.0  # 2 years backward
        )
        
        # Should wrap to ~359° (1 - 2 = -1 -> 359)
        assert result.ra_deg == pytest.approx(359.0, abs=0.1)
    
    def test_declination_clamping_north_pole(self, calculator):
        """Test Dec clamped at +90° (North Celestial Pole)."""
        result = calculator.calculate_position_at_epoch(
            ra_deg=100.0,
            dec_deg=89.5,
            pmra_mas_yr=0.0,
            pmdec_mas_yr=3600000.0,  # 1 deg/yr northward
            target_epoch=2017.0  # 1 year forward
        )
        
        # Should clamp at 90°
        assert result.dec_deg == 90.0
    
    def test_declination_clamping_south_pole(self, calculator):
        """Test Dec clamped at -90° (South Celestial Pole)."""
        result = calculator.calculate_position_at_epoch(
            ra_deg=100.0,
            dec_deg=-89.0,
            pmra_mas_yr=0.0,
            pmdec_mas_yr=-3600000.0,  # 1 deg/yr southward
            target_epoch=2017.0  # 1 year forward
        )
        
        # Should clamp at -90°
      assert result.dec_deg == -90.0
    
    def test_no_proper_motion_data(self, calculator):
        """Test handling of stars without PM data."""
        result = calculator.calculate_position_at_epoch(
            ra_deg=100.0,
            dec_deg=30.0,
            pmra_mas_yr=None,  # No PM data
            pmdec_mas_yr=None,
            target_epoch=3016.0
        )
        
        # Should return original position
        assert result.ra_deg == 100.0
        assert result.dec_deg == 30.0
        # But flag as unreliable
        assert result.uncertainty_class == UncertaintyClass.UNRELIABLE
        assert math.isinf(result.uncertainty_arcsec)
    
    def test_uncertainty_classification_high_confidence(self, calculator):
        """Test uncertainty classified as HIGH_CONFIDENCE for small time delta."""
        result = calculator.calculate_position_at_epoch(
            ra_deg=100.0,
            dec_deg=30.0,
            pmra_mas_yr=10.0,
            pmdec_mas_yr=5.0,
            target_epoch=2016.0 + 1000  # 1000 years (< 5000)
        )
        
        assert result.uncertainty_class == UncertaintyClass.HIGH_CONFIDENCE
    
    def test_uncertainty_classification_acceptable(self, calculator):
        """Test uncertainty classified as ACCEPTABLE for medium time delta."""
        result = calculator.calculate_position_at_epoch(
            ra_deg=100.0,
            dec_deg=30.0,
            pmra_mas_yr=10.0,
            pmdec_mas_yr=5.0,
            target_epoch=2016.0 + 7000  # 7000 years (5k-10k range)
        )
        
        assert result.uncertainty_class == UncertaintyClass.ACCEPTABLE
    
    def test_uncertainty_classification_approximate(self, calculator):
        """Test uncertainty classified as APPROXIMATE for large time delta."""
        result = calculator.calculate_position_at_epoch(
            ra_deg=100.0,
            dec_deg=30.0,
            pmra_mas_yr=10.0,
            pmdec_mas_yr=5.0,
            target_epoch=2016.0 + 15000  # 15000 years (10k-20k range)
        )
        
        assert result.uncertainty_class == UncertaintyClass.APPROXIMATE
    
    def test_uncertainty_classification_unreliable(self, calculator):
        """Test uncertainty classified as UNRELIABLE for extreme time delta."""
        result = calculator.calculate_position_at_epoch(
            ra_deg=100.0,
            dec_deg=30.0,
            pmra_mas_yr=10.0,
            pmdec_mas_yr=5.0,
            target_epoch=2016.0 + 50000  # 50000 years (> 20k)
        )
        
        assert result.uncertainty_class == UncertaintyClass.UNRELIABLE
    
    def test_motion_vector_calculation(self, calculator):
        """Test total motion magnitude and direction calculation."""
        # PM vectors: RA=30 mas/yr, Dec=40 mas/yr
        magnitude, angle = calculator.calculate_motion_vector(30.0, 40.0)
        
        # Magnitude should be sqrt(30² + 40²) = 50
        assert magnitude == pytest.approx(50.0)
        
        # Angle should be arctan(30/40) ≈ 36.87° East of North
        assert angle == pytest.approx(36.87, rel=0.01)
    
    def test_invalid_coordinates(self, calculator):
        """Test that invalid coordinates raise ValueError."""
        # Invalid Dec > 90
        with pytest.raises(ValueError):
            calculator.calculate_position_at_epoch(
                ra_deg=100.0,
                dec_deg=95.0,  # Invalid
                pmra_mas_yr=10.0,
                pmdec_mas_yr=5.0,
                target_epoch=2020.0
            )
        
        # Invalid RA < 0
        with pytest.raises(ValueError):
            calculator.calculate_position_at_epoch(
                ra_deg=-10.0,  # Invalid
                dec_deg=30.0,
                pmra_mas_yr=10.0,
                pmdec_mas_yr=5.0,
                target_epoch=2020.0
            )


class TestBatchCalculation:
    """Test batch processing utilities."""
    
    def test_batch_calculate_positions(self):
        """Test batch calculation for multiple stars."""
        stars = [
            {'id': 1, 'ra_deg': 100.0, 'dec_deg': 30.0, 'pmra': 10.0, 'pmdec': 5.0},
            {'id': 2, 'ra_deg': 200.0, 'dec_deg': -20.0, 'pmra': -5.0, 'pmdec': 8.0},
            {'id': 3, 'ra_deg': 50.0, 'dec_deg': 60.0, 'pmra': None, 'pmdec': None},  # No PM
        ]
        
        results = batch_calculate_positions(stars, target_epoch=3016.0)
        
        assert len(results) == 3
        
        # Star 1 should have calculated position
        assert 'ra_at_epoch' in results[0]
        assert results[0]['ra_at_epoch'] is not None
        
        # Star 2 should have calculated position
        assert results[1]['ra_at_epoch'] is not None
        
        # Star 3 (no PM) should return original position
        assert results[2]['ra_at_epoch'] == 50.0
        assert results[2]['uncertainty_class'] == 'unreliable'


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_format_epoch_display_ad(self):
        """Test epoch formatting for AD years."""
        assert format_epoch_display(2026.3) == "2026 AD"
        assert format_epoch_display(2026.7) == "2027 AD"  # Rounds up
        assert format_epoch_display(1000.0) == "1000 AD"
    
    def test_format_epoch_display_bc(self):
        """Test epoch formatting for BC years."""
        assert format_epoch_display(-3000) == "3000 BC"
        assert format_epoch_display(-500.5) == "500 BC"


# ============================================================
# INTEGRATION TEST WITH REAL-WORLD DATA
# ============================================================

class TestRealWorldCases:
    """Test with realistic astronomical scenarios."""
    
    @pytest.fixture
    def calculator(self):
        return TemporalCalculator()
    
    def test_barnards_star_motion(self, calculator):
        """
        Test with Barnard's Star - famous high proper motion star.
        
        Barnard's Star properties:
        - RA: 269.45° (17h 57m 48s)
        - Dec: +4.69°
        - PM(RA): -798.58 mas/yr (Gaia DR3)
        - PM(Dec): +10337.77 mas/yr (Gaia DR3)
        - Fastest known star in proper motion
        """
        result = calculator.calculate_position_at_epoch(
            ra_deg=269.45,
            dec_deg=4.69,
            pmra_mas_yr=-798.58,
            pmdec_mas_yr=10337.77,
            target_epoch=2026.0  # 10 years after Gaia epoch
        )
        
        # After 10 years:
        # RA change: -798.58 * 10 = -7985.8 mas ≈ -2.22 arcsec ≈ -0.00062 deg
        # Dec change: +10337.77 * 10 = +103377.7 mas ≈ +28.72 arcsec ≈ +0.00798 deg
        
        assert result.ra_deg < 269.45  # RA decreases
        assert result.dec_deg > 4.69   # Dec increases
        assert result.uncertainty_class == UncertaintyClass.HIGH_CONFIDENCE
    
    def test_pleiades_cluster_motion(self, calculator):
        """
        Test with Pleiades cluster typical proper motion.
        
        Pleiades average PM:
        - PM(RA): ~20 mas/yr
        - PM(Dec): ~-45 mas/yr
        """
        # Calculate position 2000 years in past
        result = calculator.calculate_position_at_epoch(
            ra_deg=56.75,  # Pleiades center
            dec_deg=24.12,
            pmra_mas_yr=20.0,
            pmdec_mas_yr=-45.0,
            target_epoch=-2000.0  # Year 2000 BC
        )
        
        # Should be classified as high confidence
        assert result.uncertainty_class in [
            UncertaintyClass.HIGH_CONFIDENCE,
            UncertaintyClass.ACCEPTABLE
        ]
        
        # Position should have changed measurably
        # ~4000 years back: significant offset
        assert abs(result.ra_deg - 56.75) > 0.01  # > 0.01 degrees
