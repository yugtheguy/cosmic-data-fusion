"""
Temporal Calculator Service for COSMIC Time Machine

This module handles calculation of stellar positions at arbitrary epochs
using proper motion data from Gaia DR3.

Key Concepts:
- Proper Motion: The apparent angular motion of a star across the sky
  measured in milliarcseconds per year (mas/yr)
- Epoch: A specific point in time (usually expressed as decimal year)
- Reference Epoch: The time when coordinates were measured (Gaia DR3 = J2016.0)

Scientific Accuracy:
- Linear approximation is valid for ±10,000 years for most stars
- Uncertainty increases with time delta from reference epoch
- Does NOT account for:
  - Radial velocity (motion toward/away from us)
  - Galactic rotation effects (significant beyond ±50,000 years)
  - Relativistic effects
  - N-body gravitational perturbations

References:
- Gaia DR3 Documentation: https://gea.esac.esa.int/archive/documentation/
- Proper Motion Primer: https://www.cosmos.esa.int/web/gaia/iow_20180316
"""

import logging
import math
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class UncertaintyClass(str, Enum):
    """Classification of temporal projection uncertainty."""
    HIGH_CONFIDENCE = "high_confidence"      # <0.1° error, ±5000 years
    ACCEPTABLE = "acceptable"                # <0.5° error, ±10000 years  
    APPROXIMATE = "approximate"              # <2° error, ±20000 years
    EXTREME_RANGE = "extreme_range"          # <10° error, ±50000 years (NEW)
    UNRELIABLE = "unreliable"                # >10° error, >±50000 years


@dataclass
class TemporalPosition:
    """Result of temporal position calculation."""
    ra_deg: float                           # Right Ascension at target epoch (degrees)
    dec_deg: float                          # Declination at target epoch (degrees)
    uncertainty_arcsec: float               # Position uncertainty (arcseconds)
    uncertainty_class: UncertaintyClass     # Qualitative uncertainty level
    epoch: float                            # Target epoch (decimal year)
    reference_epoch: float                  # Original measurement epoch
    delta_years: float                      # Time difference from reference


class TemporalCalculator:
    """
    Calculate stellar positions at arbitrary epochs using proper motion.
    
    Core algorithm:
    1. Calculate time delta from reference epoch
    2. Apply proper motion vectors (pmra, pmdec)
    3. Handle spherical geometry corrections
    4. Estimate uncertainty
    """
    
    # Default reference epoch for Gaia DR3
    DEFAULT_REFERENCE_EPOCH = 2016.0
    
    # Uncertainty thresholds (years)
    THRESHOLD_HIGH_CONFIDENCE = 5000
    THRESHOLD_ACCEPTABLE = 10000
    THRESHOLD_APPROXIMATE = 20000
    THRESHOLD_EXTREME_RANGE = 50000  # NEW: Support for extreme temporal predictions
    
    def __init__(self, reference_epoch: float = DEFAULT_REFERENCE_EPOCH):
        """
        Initialize temporal calculator.
        
        Args:
            reference_epoch: Reference epoch for coordinates (default: J2016.0)
        """
        self.reference_epoch = reference_epoch
        logger.info(f"TemporalCalculator initialized with reference epoch {reference_epoch}")
    
    def calculate_position_at_epoch(
        self,
        ra_deg: float,
        dec_deg: float,
        pmra_mas_yr: Optional[float],
        pmdec_mas_yr: Optional[float],
        target_epoch: float,
        pmra_error_mas_yr: Optional[float] = None,
        pmdec_error_mas_yr: Optional[float] = None,
        reference_epoch: Optional[float] = None
    ) -> TemporalPosition:
        """
        Calculate star position at a target epoch using proper motion.
        
        Args:
            ra_deg: Current Right Ascension (degrees, ICRS)
            dec_deg: Current Declination (degrees, ICRS)
            pmra_mas_yr: Proper motion in RA * cos(dec) (mas/year)
            pmdec_mas_yr: Proper motion in Declination (mas/year)
            target_epoch: Target epoch as decimal year (e.g., 2026.5, -3000)
            pmra_error_mas_yr: PM error in RA (optional, for uncertainty calc)
            pmdec_error_mas_yr: PM error in Dec (optional, for uncertainty calc)
            reference_epoch: Reference epoch (default: class default)
            
        Returns:
            TemporalPosition with calculated coordinates and uncertainty
            
        Raises:
            ValueError: If coordinates are out of valid ranges
        """
        # Validate inputs
        if not (-90 <= dec_deg <= 90):
            raise ValueError(f"Declination {dec_deg}° out of range [-90, 90]")
        
        if not (0 <= ra_deg < 360):
            raise ValueError(f"Right Ascension {ra_deg}° out of range [0, 360)")
        
        # Use provided reference epoch or default
        ref_epoch = reference_epoch or self.reference_epoch
        
        # Calculate time delta
        delta_years = target_epoch - ref_epoch
        
        # If no proper motion data, return current position with warning
        if pmra_mas_yr is None or pmdec_mas_yr is None:
            logger.warning(
                f"No proper motion data for star at RA={ra_deg:.4f}, Dec={dec_deg:.4f}. "
                "Returning static position."
            )
            return TemporalPosition(
                ra_deg=ra_deg,
                dec_deg=dec_deg,
                uncertainty_arcsec=999999.0,  # Very large (unknown) but JSON-serializable
                uncertainty_class=UncertaintyClass.UNRELIABLE,
                epoch=target_epoch,
                reference_epoch=ref_epoch,
                delta_years=delta_years
            )
        
        # Convert proper motion from mas/year to degrees/year
        # Note: pmra is already pmra*cos(dec) from Gaia
        pmra_deg_yr = pmra_mas_yr / (3600 * 1000)     # mas -> arcsec -> deg
        pmdec_deg_yr = pmdec_mas_yr / (3600 * 1000)
        
        # Calculate position change
        delta_ra_deg = pmra_deg_yr * delta_years
        delta_dec_deg = pmdec_deg_yr * delta_years
        
        # Apply changes
        # RA wraps around at 0°/360°
        ra_new = (ra_deg + delta_ra_deg) % 360.0
        
        # Dec is bounded at poles
        dec_new = dec_deg + delta_dec_deg
        dec_new = max(-90.0, min(90.0, dec_new))
        
        # Handle pole crossing (RA becomes undefined at poles)
        if abs(dec_new) > 89.9:
            logger.debug(f"Star approaching celestial pole: dec={dec_new:.2f}°")
        
        # Calculate uncertainty
        uncertainty_arcsec = self._calculate_uncertainty(
            delta_years=delta_years,
            pmra_mas_yr=pmra_mas_yr,
            pmdec_mas_yr=pmdec_mas_yr,
            pmra_error_mas_yr=pmra_error_mas_yr,
            pmdec_error_mas_yr=pmdec_error_mas_yr
        )
        
        # Classify uncertainty
        uncertainty_class = self._classify_uncertainty(
            delta_years=abs(delta_years),
            uncertainty_arcsec=uncertainty_arcsec
        )
        
        return TemporalPosition(
            ra_deg=ra_new,
            dec_deg=dec_new,
            uncertainty_arcsec=uncertainty_arcsec,
            uncertainty_class=uncertainty_class,
            epoch=target_epoch,
            reference_epoch=ref_epoch,
            delta_years=delta_years
        )
    
    def _calculate_uncertainty(
        self,
        delta_years: float,
        pmra_mas_yr: float,
        pmdec_mas_yr: float,
        pmra_error_mas_yr: Optional[float],
        pmdec_error_mas_yr: Optional[float]
    ) -> float:
        """
        Calculate position uncertainty in arcseconds.
        
        Uncertainty sources:
        1. Proper motion measurement errors
        2. Linear approximation breakdown over time
        3. Unmodeled accelerations (galactic rotation, etc.)
        
        Args:
            delta_years: Time from reference epoch
            pmra_mas_yr: Proper motion in RA
            pmdec_mas_yr: Proper motion in Dec
            pmra_error_mas_yr: PM error in RA (optional)
            pmdec_error_mas_yr: PM error in Dec (optional)
            
        Returns:
            Total uncertainty in arcseconds
        """
        # Component 1: Propagated measurement error
        if pmra_error_mas_yr and pmdec_error_mas_yr:
            # Error propagates linearly with time
            error_ra_mas = pmra_error_mas_yr * abs(delta_years)
            error_dec_mas = pmdec_error_mas_yr * abs(delta_years)
            
            # Combined error (RSS - root sum of squares)
            measurement_error_mas = math.sqrt(error_ra_mas**2 + error_dec_mas**2)
        else:
            # Assume 1% of total motion if errors not provided
            total_motion_mas = math.sqrt(pmra_mas_yr**2 + pmdec_mas_yr**2) * abs(delta_years)
            measurement_error_mas = 0.01 * total_motion_mas
        
        # Component 2: Model error (linear approximation breakdown)
        # Increases quadratically with time
        # Enhanced for extreme ranges: use higher coefficient beyond ±20,000 years
        if abs(delta_years) > 20000:
            # Extreme range: account for galactic rotation and higher-order effects
            model_error_mas = 0.005 * (delta_years ** 2)  # 5x higher coefficient
        else:
            # Normal range: typical galactic rotation effects
            model_error_mas = 0.001 * (delta_years ** 2)
        
        # Component 3: Baseline uncertainty (even at reference epoch)
        baseline_error_mas = 0.1  # Gaia DR3 typical astrometric precision
        
        # Total uncertainty (RSS combination)
        total_uncertainty_mas = math.sqrt(
            measurement_error_mas**2 +
            model_error_mas**2 +
            baseline_error_mas**2
        )
        
        # Convert to arcseconds
        return total_uncertainty_mas / 1000.0
    
    def _classify_uncertainty(
        self,
        delta_years: float,
        uncertainty_arcsec: float
    ) -> UncertaintyClass:
        """
        Classify uncertainty level based on time delta and error magnitude.
        
        Args:
            delta_years: Absolute time from reference epoch
            uncertainty_arcsec: Calculated uncertainty in arcseconds
            
        Returns:
            UncertaintyClass enum value
        """
        # Time-based classification (primary criterion)
        if delta_years < self.THRESHOLD_HIGH_CONFIDENCE:
            # <5000 years: High confidence
            if uncertainty_arcsec < 360:  # <0.1 degree
                return UncertaintyClass.HIGH_CONFIDENCE
            else:
                return UncertaintyClass.ACCEPTABLE
        
        elif delta_years < self.THRESHOLD_ACCEPTABLE:
            # 5000-10000 years: Acceptable
            if uncertainty_arcsec < 1800:  # <0.5 degree
                return UncertaintyClass.ACCEPTABLE
            else:
                return UncertaintyClass.APPROXIMATE
        
        elif delta_years < self.THRESHOLD_APPROXIMATE:
            # 10000-20000 years: Approximate
            return UncertaintyClass.APPROXIMATE
        
        elif delta_years <= self.THRESHOLD_EXTREME_RANGE:  # Changed < to <= to include boundary
            # 20000-50000 years: Extreme range (NEW)
            # Allow higher uncertainty for extreme predictions (up to 10 degrees)
            if uncertainty_arcsec < 36000:  # <10 degrees (increased from 5)
                return UncertaintyClass.EXTREME_RANGE
            else:
                return UncertaintyClass.UNRELIABLE
        
        else:
            # >50000 years: Unreliable
            return UncertaintyClass.UNRELIABLE
    
    def calculate_motion_vector(
        self,
        pmra_mas_yr: float,
        pmdec_mas_yr: float
    ) -> Tuple[float, float]:
        """
        Calculate total proper motion magnitude and direction.
        
        Args:
            pmra_mas_yr: Proper motion in RA * cos(dec) (mas/year)  
            pmdec_mas_yr: Proper motion in Dec (mas/year)
            
        Returns:
            Tuple of (magnitude in mas/yr, position angle in degrees)
            Position angle is measured East of North (astronomical convention)
        """
        # Total magnitude
        magnitude = math.sqrt(pmra_mas_yr**2 + pmdec_mas_yr**2)
        
        # Position angle (East of North)
        # atan2(pmra, pmdec) gives angle from north axis
        angle_rad = math.atan2(pmra_mas_yr, pmdec_mas_yr)
        angle_deg = math.degrees(angle_rad)
        
        # Normalize to [0, 360)
        if angle_deg < 0:
            angle_deg += 360
        
        return magnitude, angle_deg


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def batch_calculate_positions(
    stars: list,
    target_epoch: float,
    calculator: Optional[TemporalCalculator] = None
) -> list:
    """
    Calculate positions for multiple stars at a target epoch.
    
    Args:
        stars: List of star dictionaries with RA, Dec, PM data
        target_epoch: Target epoch for all stars
        calculator: TemporalCalculator instance (creates default if None)
        
    Returns:
        List of dictionaries with original and calculated positions
    """
    if calculator is None:
        calculator = TemporalCalculator()
    
    results = []
    
    for star in stars:
        try:
            # Extract data from star dict
            result = calculator.calculate_position_at_epoch(
                ra_deg=star['ra_deg'],
                dec_deg=star['dec_deg'],
                pmra_mas_yr=star.get('pmra'),
                pmdec_mas_yr=star.get('pmdec'),
                target_epoch=target_epoch,
                reference_epoch=star.get('ref_epoch')
            )
            
            # Combine with original star data
            results.append({
                **star,
                'ra_at_epoch': result.ra_deg,
                'dec_at_epoch': result.dec_deg,
                'uncertainty_arcsec': result.uncertainty_arcsec,
                'uncertainty_class': result.uncertainty_class.value,
                'epoch': result.epoch
            })
            
        except Exception as e:
            logger.error(f"Failed to calculate position for star {star.get('id')}: {e}")
            # Include star with null calculated values
            results.append({
                **star,
                'ra_at_epoch': None,
                'dec_at_epoch': None,
                'uncertainty_arcsec': None,
                'uncertainty_class': 'error',
                'epoch': target_epoch
            })
    
    return results


def format_epoch_display(epoch: float) -> str:
    """
    Format epoch as human-readable string.
    
    Args:
        epoch: Decimal year (e.g., 2026.5, -3000)
        
    Returns:
        Formatted string (e.g., "2026 AD", "3000 BC")
    """
    if epoch >= 1:
        year = int(epoch)
        fraction = epoch - year
        if fraction > 0.5:
            return f"{year + 1} AD"
        else:
            return f"{year} AD"
    else:
        year = int(abs(epoch))
        return f"{year} BC"
