"""
Coordinate standardization service using Astropy.

ALL coordinate transformations happen here using astropy.coordinates.SkyCoord.
NEVER use manual trigonometry for coordinate conversion.

Astronomy Notes:
- ICRS (International Celestial Reference System) is the modern standard
- ICRS is defined by distant quasars, making it extremely stable
- FK5 J2000 is nearly identical to ICRS (< 0.1 arcsec difference)
- Galactic coordinates require a ~62.87° rotation transformation
"""

import logging
from typing import Tuple

from astropy.coordinates import SkyCoord
import astropy.units as u

from app.schemas import CoordinateFrame

logger = logging.getLogger(__name__)


class CoordinateStandardizer:
    """
    Service for transforming coordinates to ICRS J2000.
    
    Uses Astropy's SkyCoord for all transformations, ensuring:
    - Correct spherical geometry handling
    - Proper precession/nutation for FK5
    - Accurate Galactic-to-equatorial conversion
    
    Astropy uses high-precision algorithms from SOFA/ERFA libraries.
    """
    
    @staticmethod
    def transform_to_icrs(
        coord1: float,
        coord2: float,
        frame: CoordinateFrame
    ) -> Tuple[float, float]:
        """
        Transform coordinates from any supported frame to ICRS J2000.
        
        This is the ONLY method that should perform coordinate transformations
        in the entire application.
        
        Args:
            coord1: First coordinate in degrees
                   - RA for ICRS/FK5
                   - Galactic longitude (l) for GALACTIC
            coord2: Second coordinate in degrees
                   - Dec for ICRS/FK5
                   - Galactic latitude (b) for GALACTIC
            frame: Source coordinate frame
            
        Returns:
            Tuple of (ra_deg, dec_deg) in ICRS J2000
            
        Raises:
            ValueError: If coordinates are invalid for the frame
            
        Technical Notes:
            - Galactic→ICRS uses IAU 1958 Galactic plane definition
            - FK5→ICRS involves a small frame rotation (< 0.1 arcsec)
            - All math is handled internally by Astropy
        """
        logger.debug(
            f"Transforming ({coord1:.6f}, {coord2:.6f}) from {frame.value} to ICRS"
        )
        
        if frame == CoordinateFrame.ICRS:
            # Input already ICRS - validate through SkyCoord
            # This ensures coordinates are physically valid
            sky_coord = SkyCoord(
                ra=coord1 * u.degree,
                dec=coord2 * u.degree,
                frame="icrs"
            )
            
        elif frame == CoordinateFrame.FK5:
            # FK5 J2000 - nearly identical to ICRS
            # The ~20 mas offset is handled by Astropy's frame tie
            sky_coord = SkyCoord(
                ra=coord1 * u.degree,
                dec=coord2 * u.degree,
                frame="fk5",
                equinox="J2000"  # Explicitly J2000 epoch
            )
            
        elif frame == CoordinateFrame.GALACTIC:
            # Galactic coordinates (l, b)
            # l=0, b=0 points toward Sagittarius A* (Galactic center)
            # Transformation involves rotation by Galactic pole position
            sky_coord = SkyCoord(
                l=coord1 * u.degree,
                b=coord2 * u.degree,
                frame="galactic"
            )
            
        else:
            raise ValueError(f"Unsupported coordinate frame: {frame}")
        
        # Transform to ICRS J2000
        # For ICRS input, this validates; for others, it transforms
        icrs_coord = sky_coord.icrs
        
        # Extract as Python floats (degrees)
        ra_deg = float(icrs_coord.ra.deg)
        dec_deg = float(icrs_coord.dec.deg)
        
        logger.debug(f"Result: RA={ra_deg:.6f}°, Dec={dec_deg:.6f}° (ICRS)")
        
        return ra_deg, dec_deg
    
    @staticmethod
    def calculate_angular_separation(
        ra1: float,
        dec1: float,
        ra2: float,
        dec2: float
    ) -> float:
        """
        Calculate angular separation between two points on the celestial sphere.
        
        Uses Astropy's SkyCoord.separation() method which implements
        the Vincenty formula for accurate results at any separation.
        
        Args:
            ra1, dec1: First point (degrees, ICRS)
            ra2, dec2: Second point (degrees, ICRS)
            
        Returns:
            Angular separation in degrees
            
        Note:
            This properly handles the spherical geometry, including
            the cos(dec) factor and poles.
        """
        coord1 = SkyCoord(ra=ra1 * u.degree, dec=dec1 * u.degree, frame="icrs")
        coord2 = SkyCoord(ra=ra2 * u.degree, dec=dec2 * u.degree, frame="icrs")
        
        # separation() uses Vincenty formula for accuracy
        separation = coord1.separation(coord2)
        
        return float(separation.deg)
    
    @staticmethod
    def calculate_bounding_box_for_cone(
        ra_center: float,
        dec_center: float,
        radius: float
    ) -> Tuple[float, float, float, float]:
        """
        Calculate bounding box for a cone search.
        
        The bounding box is used as a pre-filter before computing
        exact angular separations. This leverages the database index.
        
        Args:
            ra_center: Center RA in degrees
            dec_center: Center Dec in degrees
            radius: Search radius in degrees
            
        Returns:
            Tuple of (ra_min, ra_max, dec_min, dec_max)
            Note: ra_min may be <0 or ra_max >360 for wrap handling
            
        Astronomy Note:
            The RA range expands as 1/cos(dec) near the poles because
            lines of constant RA converge. This ensures we don't miss
            any stars near the poles.
        """
        import math
        
        # Dec bounds are straightforward (clamp to valid range)
        dec_min = max(-90.0, dec_center - radius)
        dec_max = min(90.0, dec_center + radius)
        
        # RA bounds need cos(dec) correction
        # At the poles, we need to search all RA values
        if dec_max >= 89.0 or dec_min <= -89.0:
            # Near pole - search full RA range
            ra_min = 0.0
            ra_max = 360.0
        else:
            # cos(dec) factor for RA extent
            # Use the dec closest to equator for conservative bound
            cos_dec = math.cos(math.radians(max(abs(dec_min), abs(dec_max))))
            
            # Avoid division by very small numbers
            if cos_dec < 0.01:
                ra_min = 0.0
                ra_max = 360.0
            else:
                ra_extent = radius / cos_dec
                ra_min = ra_center - ra_extent
                ra_max = ra_center + ra_extent
        
        return ra_min, ra_max, dec_min, dec_max
