"""
Unit conversion utilities for astronomical data.

Provides functions for converting between different units commonly used
in astronomical catalogs (parallax, distance, magnitude, etc.).
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class UnitConverter:
    """
    Utility class for astronomical unit conversions.
    
    Handles conversions between:
    - Parallax and distance
    - Various distance units
    - Magnitude systems (future)
    """
    
    @staticmethod
    def parallax_to_distance(parallax_mas: Optional[float]) -> Optional[float]:
        """
        Convert parallax to distance.
        
        Uses the simple relation: distance (pc) = 1000 / parallax (mas)
        
        Args:
            parallax_mas: Parallax in milliarcseconds
            
        Returns:
            Distance in parsecs, or None if parallax is invalid
            
        Note:
            - Returns None for non-positive parallax values
            - Does not apply corrections for negative parallax
            - For Gaia, consider using corrected parallax when available
        """
        if parallax_mas is None:
            return None
            
        if parallax_mas <= 0:
            logger.warning(f"Invalid parallax value: {parallax_mas} mas (must be positive)")
            return None
            
        try:
            distance_pc = 1000.0 / parallax_mas
            return distance_pc
        except ZeroDivisionError:
            logger.error("Division by zero in parallax conversion")
            return None
    
    @staticmethod
    def distance_to_parallax(distance_pc: Optional[float]) -> Optional[float]:
        """
        Convert distance to parallax.
        
        Uses the inverse relation: parallax (mas) = 1000 / distance (pc)
        
        Args:
            distance_pc: Distance in parsecs
            
        Returns:
            Parallax in milliarcseconds, or None if distance is invalid
        """
        if distance_pc is None:
            return None
            
        if distance_pc <= 0:
            logger.warning(f"Invalid distance value: {distance_pc} pc (must be positive)")
            return None
            
        try:
            parallax_mas = 1000.0 / distance_pc
            return parallax_mas
        except ZeroDivisionError:
            logger.error("Division by zero in distance conversion")
            return None
    
    @staticmethod
    def lightyears_to_parsecs(lightyears: float) -> float:
        """
        Convert light years to parsecs.
        
        Args:
            lightyears: Distance in light years
            
        Returns:
            Distance in parsecs
        """
        return lightyears / 3.26156
    
    @staticmethod
    def parsecs_to_lightyears(parsecs: float) -> float:
        """
        Convert parsecs to light years.
        
        Args:
            parsecs: Distance in parsecs
            
        Returns:
            Distance in light years
        """
        return parsecs * 3.26156
    
    @staticmethod
    def kiloparsecs_to_parsecs(kiloparsecs: float) -> float:
        """
        Convert kiloparsecs to parsecs.
        
        Args:
            kiloparsecs: Distance in kiloparsecs
            
        Returns:
            Distance in parsecs
        """
        return kiloparsecs * 1000.0
    
    @staticmethod
    def megaparsecs_to_parsecs(megaparsecs: float) -> float:
        """
        Convert megaparsecs to parsecs.
        
        Args:
            megaparsecs: Distance in megaparsecs
            
        Returns:
            Distance in parsecs
        """
        return megaparsecs * 1_000_000.0
    
    @staticmethod
    def normalize_magnitude(
        magnitude: float,
        source_filter: str = "G",
        target_filter: str = "V"
    ) -> float:
        """
        Normalize magnitude from one photometric system to another.
        
        This is a placeholder for future implementation.
        Proper magnitude conversion requires color information.
        
        Args:
            magnitude: Input magnitude
            source_filter: Source filter (e.g., "G" for Gaia, "g" for SDSS)
            target_filter: Target filter (e.g., "V" for Johnson V-band)
            
        Returns:
            Normalized magnitude (currently returns input unchanged)
            
        Note:
            Full implementation requires:
            - Color indices (e.g., G-RP, g-r)
            - Filter transformation equations
            - Stellar type considerations
        """
        # TODO: Implement proper magnitude conversion
        # For now, return as-is
        logger.debug(f"Magnitude normalization not implemented: {source_filter} -> {target_filter}")
        return magnitude
    
    @staticmethod
    def redshift_to_distance(redshift: Optional[float], h0: float = 70.0) -> Optional[float]:
        """
        Convert redshift to luminosity distance in parsecs.
        
        Uses simplified Hubble law for low redshift (z < 0.1):
            d = c * z / H0
        
        For higher redshift, uses approximation:
            d ≈ (c/H0) * z * (1 + z/2)
        
        Args:
            redshift: Cosmological redshift (z)
            h0: Hubble constant in km/s/Mpc (default: 70.0)
            
        Returns:
            Distance in parsecs, or None if redshift is invalid
            
        Note:
            - Speed of light c = 299,792 km/s
            - Result is in parsecs (1 Mpc = 1,000,000 pc)
            - Assumes flat ΛCDM cosmology approximation
            - For precise distances, use astropy.cosmology
        """
        if redshift is None or redshift < 0:
            return None
        
        # Speed of light in km/s
        c = 299792.458
        
        # Convert H0 from km/s/Mpc to 1/s using 1 Mpc = 3.086e19 km
        # Distance in Mpc: d_Mpc = (c/H0) * z * correction
        
        if redshift < 0.1:
            # Simple Hubble law for low redshift
            distance_mpc = (c / h0) * redshift
        else:
            # First-order correction for higher redshift
            distance_mpc = (c / h0) * redshift * (1 + redshift / 2.0)
        
        # Convert Mpc to parsecs
        distance_pc = distance_mpc * 1_000_000.0
        
        return distance_pc
    
    @staticmethod
    def distance_to_redshift(distance_pc: Optional[float], h0: float = 70.0) -> Optional[float]:
        """
        Convert luminosity distance to redshift (inverse of redshift_to_distance).
        
        Uses simplified approximation.
        
        Args:
            distance_pc: Distance in parsecs
            h0: Hubble constant in km/s/Mpc (default: 70.0)
            
        Returns:
            Redshift (z), or None if distance is invalid
        """
        if distance_pc is None or distance_pc <= 0:
            return None
        
        # Convert parsecs to Mpc
        distance_mpc = distance_pc / 1_000_000.0
        
        # Speed of light in km/s
        c = 299792.458
        
        # Inverse calculation (simplified)
        # For low z: z = H0 * d / c
        redshift = (h0 * distance_mpc) / c
        
        return redshift
