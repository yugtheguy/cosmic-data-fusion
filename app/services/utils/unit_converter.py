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
        magnitude: Optional[float],
        source_filter: str = "G",
        target_filter: str = "V",
        color_index: Optional[float] = None
    ) -> Optional[float]:
        """
        Normalize magnitude from one photometric system to another.
        
        Implements empirical transformations for common photometric systems:
        - Gaia (G, BP, RP) → Johnson-Cousins (V, B, R, I)
        - SDSS (g, r, i, z) → Johnson-Cousins
        - 2MASS (J, H, K) → Johnson-Cousins
        
        Args:
            magnitude: Input magnitude in source filter
            source_filter: Source filter name (case-insensitive)
                         Supported: G, g, r, i, z, J, H, K, BP, RP
            target_filter: Target filter name (case-insensitive)
                          Supported: V, B, R, I, J, H, K
            color_index: Optional color index for improved accuracy
                        (e.g., G-RP for Gaia, g-r for SDSS)
            
        Returns:
            Magnitude in target filter system, or None if conversion not possible
            
        References:
            - Gaia transformations: Jordi et al. 2010, A&A 523, A48
            - SDSS transformations: Jester et al. 2005, AJ 130, 873
            - 2MASS: Carpenter 2001, AJ 121, 2851
            
        Note:
            Conversions without color information use typical main-sequence
            star assumptions (G-V type). For more accurate results, provide
            color indices when available.
        """
        if magnitude is None:
            return None
        
        # Normalize filter names to uppercase
        source = source_filter.upper().strip()
        target = target_filter.upper().strip()
        
        # If same filter, return as-is
        if source == target:
            return magnitude
        
        # Define conversion offsets (zero-point differences)
        # These are approximate conversions assuming solar-type stars (G2V)
        # More accurate conversions require color information
        
        # Gaia G-band to Johnson V (for G2V stars)
        # V ≈ G - 0.01 * (G-RP) - 0.02 (simplified, assuming G-RP ≈ 0.6)
        if source == "G" and target == "V":
            if color_index is not None:  # G-RP provided
                return magnitude - 0.01 * color_index - 0.02
            else:
                # Assume solar-type star (G-RP ≈ 0.6)
                return magnitude - 0.03
        
        # Gaia BP to Johnson B
        if source == "BP" and target == "B":
            if color_index is not None:  # BP-RP provided
                return magnitude - 0.08 - 0.06 * color_index
            else:
                return magnitude - 0.20  # Typical offset
        
        # Gaia RP to Cousins R
        if source == "RP" and target == "R":
            if color_index is not None:  # BP-RP provided
                return magnitude + 0.12 - 0.05 * color_index
            else:
                return magnitude - 0.15  # Typical offset
        
        # SDSS g to Johnson V
        # V ≈ g - 0.59 * (g-r) - 0.01 (Jester et al. 2005)
        if source == "G" and target == "V":
            if color_index is not None:  # g-r provided
                return magnitude - 0.59 * color_index - 0.01
            else:
                # Assume g-r ≈ 0.45 for solar-type
                return magnitude - 0.27
        
        # SDSS r to Cousins R
        # R ≈ r - 0.21 * (g-r) - 0.01
        if source == "R" and target == "R":
            if color_index is not None:  # g-r provided
                return magnitude - 0.21 * color_index - 0.01
            else:
                return magnitude - 0.11
        
        # SDSS i to Cousins I
        # I ≈ i - 0.37 * (r-i) + 0.03
        if source == "I" and target == "I":
            if color_index is not None:  # r-i provided
                return magnitude - 0.37 * color_index + 0.03
            else:
                return magnitude - 0.05
        
        # 2MASS filters are close to Johnson-Cousins in NIR
        if source in ["J", "H", "K"] and target in ["J", "H", "K"]:
            # 2MASS and Johnson-Cousins are nearly identical in NIR
            if source == target:
                return magnitude
            # Color differences between bands (fainter = more positive magnitude)
            # For G-type stars: J is brightest, then H, then K (reddest)
            # Typical colors: J-H ≈ 0.30, H-K ≈ 0.20, J-K ≈ 0.50
            offsets = {
                ("J", "H"): 0.30,   # H is 0.30 mag fainter than J
                ("J", "K"): 0.50,   # K is 0.50 mag fainter than J
                ("H", "J"): -0.30,  # J is 0.30 mag brighter than H
                ("H", "K"): 0.20,   # K is 0.20 mag fainter than H
                ("K", "J"): -0.50,  # J is 0.50 mag brighter than K
                ("K", "H"): -0.20,  # H is 0.20 mag brighter than K
            }
            offset = offsets.get((source, target), 0.0)
            return magnitude + offset
        
        # Cross-band conversions (optical to NIR)
        # V to J (very approximate)
        if source == "V" and target == "J":
            # V-J ≈ 1.0 to 2.0 depending on stellar type
            # Assume solar-type: V-J ≈ 1.1
            return magnitude - 1.1
        
        # Unsupported conversion - log warning and return original
        logger.warning(
            f"Magnitude conversion {source} → {target} not implemented. "
            f"Returning original magnitude. For accurate results, implement "
            f"the specific transformation or use color indices."
        )
        return magnitude
    
    @staticmethod
    def flux_to_magnitude(
        flux: Optional[float],
        flux_zero_point: float = 3631.0,  # Jy (AB magnitude system)
        magnitude_system: str = "AB"
    ) -> Optional[float]:
        """
        Convert flux to magnitude using standard photometric systems.
        
        Implements magnitude calculation for:
        - AB magnitude system (commonly used in SDSS, Pan-STARRS)
        - Vega magnitude system (traditional, used in Johnson-Cousins)
        - ST magnitude system (HST Space Telescope system)
        
        Args:
            flux: Flux value (units depend on magnitude_system)
            flux_zero_point: Zero-point flux in appropriate units
                           AB: Jy (janskys), default 3631 Jy
                           Vega: depends on filter
                           ST: erg/s/cm²/Å
            magnitude_system: Magnitude system to use
                            "AB" (default), "Vega", "ST"
            
        Returns:
            Magnitude value, or None if flux is invalid
            
        Formula:
            m = -2.5 * log10(flux / flux_zero_point)
            
        Note:
            AB system definition: m_AB = -2.5 * log10(f_ν) - 48.60
            where f_ν is in erg/s/cm²/Hz
            Conversion: 3631 Jy = 10^(-48.60/2.5) erg/s/cm²/Hz
        """
        import math
        
        if flux is None or flux <= 0:
            logger.warning(f"Invalid flux for magnitude conversion: {flux}")
            return None
        
        if flux_zero_point <= 0:
            logger.error(f"Invalid zero-point flux: {flux_zero_point}")
            return None
        
        try:
            # Basic magnitude formula
            magnitude = -2.5 * math.log10(flux / flux_zero_point)
            
            # Validate result is finite
            if not math.isfinite(magnitude):
                logger.warning(f"Non-finite magnitude result: flux={flux}, zp={flux_zero_point}")
                return None
            
            # Sanity check: astronomical magnitudes typically in range -30 to +30
            if not (-30.0 <= magnitude <= 30.0):
                logger.warning(
                    f"Magnitude {magnitude:.2f} outside typical range [-30, 30]. "
                    f"Check flux units and zero-point."
                )
            
            return magnitude
            
        except (ValueError, ZeroDivisionError) as e:
            logger.error(f"Error converting flux to magnitude: {e}")
            return None
    
    @staticmethod
    def magnitude_to_flux(
        magnitude: Optional[float],
        flux_zero_point: float = 3631.0,  # Jy (AB magnitude system)
        magnitude_system: str = "AB"
    ) -> Optional[float]:
        """
        Convert magnitude to flux (inverse of flux_to_magnitude).
        
        Args:
            magnitude: Magnitude value
            flux_zero_point: Zero-point flux in appropriate units
            magnitude_system: Magnitude system ("AB", "Vega", "ST")
            
        Returns:
            Flux value in units matching flux_zero_point, or None if invalid
            
        Formula:
            flux = flux_zero_point * 10^(-magnitude / 2.5)
        """
        import math
        
        if magnitude is None:
            return None
        
        if flux_zero_point <= 0:
            logger.error(f"Invalid zero-point flux: {flux_zero_point}")
            return None
        
        try:
            # Inverse magnitude formula
            flux = flux_zero_point * math.pow(10.0, -magnitude / 2.5)
            
            # Validate result
            if not math.isfinite(flux) or flux <= 0:
                logger.warning(f"Invalid flux result: {flux}")
                return None
            
            return flux
            
        except (ValueError, OverflowError) as e:
            logger.error(f"Error converting magnitude to flux: {e}")
            return None
    
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
    
    @staticmethod
    def arcsec_to_mas(arcsec: float) -> float:
        """
        Convert arcseconds to milliarcseconds.
        
        Args:
            arcsec: Angle in arcseconds
            
        Returns:
            Angle in milliarcseconds
        """
        return arcsec * 1000.0
    
    @staticmethod
    def mas_to_arcsec(mas: float) -> float:
        """
        Convert milliarcseconds to arcseconds.
        
        Args:
            mas: Angle in milliarcseconds
            
        Returns:
            Angle in arcseconds
        """
        return mas / 1000.0
    
    @staticmethod
    def safe_float_convert(value, default: Optional[float] = None) -> Optional[float]:
        """
        Safely convert a value to float, handling NaN, Inf, and None.
        
        Useful for FITS data which may contain masked values or invalid numbers.
        
        Args:
            value: Value to convert (any type)
            default: Default value if conversion fails or value is invalid
            
        Returns:
            Float value or default if invalid
        """
        import numpy as np
        
        if value is None:
            return default
        
        try:
            f = float(value)
            if np.isfinite(f):
                return f
            else:
                logger.debug(f"Non-finite value encountered: {f}")
                return default
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to convert to float: {value} ({e})")
            return default
