"""
Flexible coordinate parser supporting multiple astronomical coordinate formats.

Inspired by professional astronomical tools but implemented independently.
Converts various coordinate notations to decimal degrees (ICRS J2000).
"""

import re
from typing import Tuple, Optional
from astropy.coordinates import SkyCoord
from astropy import units as u
import logging

logger = logging.getLogger(__name__)


class CoordinateParser:
    """
    Parse astronomical coordinates in multiple formats.
    
    Supported formats:
    - Decimal degrees: "350.123456 -17.33333"
    - Sexagesimal: "20 54 05.689 +37 01 17.38"
    - HMS/DMS: "10:12:45.3 -45:17:50"
    - Mixed notation: "15h17m-11d10m", "15h17+89d15"
    - Degrees with suffix: "275d11m15.6954s +17d59m59.876s"
    - Hybrid: "12.34567h -17.87654d"
    """
    
    # Regex patterns for different formats
    DECIMAL_PATTERN = r'^([+-]?\d+\.?\d*)\s+([+-]?\d+\.?\d*)$'
    SEXAGESIMAL_PATTERN = r'^(\d{1,2})\s+(\d{1,2})\s+([\d.]+)\s+([+-]?\d{1,2})\s+(\d{1,2})\s+([\d.]+)$'
    HMS_DMS_PATTERN = r'^(\d{1,2}):(\d{1,2}):([\d.]+)\s+([+-]?\d{1,2}):(\d{1,2}):([\d.]+)$'
    MIXED_NOTATION_PATTERN = r'^(\d+\.?\d*)h(\d+\.?\d*)m?\s*([+-]?\d+\.?\d*)d(\d+\.?\d*)m?$'
    SUFFIX_PATTERN = r'^(\d+)d(\d+)m([\d.]+)s\s+([+-]?\d+)d(\d+)m([\d.]+)s$'
    HYBRID_PATTERN = r'^([\d.]+)h\s+([+-]?[\d.]+)d$'
    
    @staticmethod
    def parse(coord_string: str) -> Tuple[float, float]:
        """
        Parse coordinate string and return (RA, Dec) in decimal degrees.
        
        Args:
            coord_string: Coordinate string in any supported format
            
        Returns:
            Tuple of (ra_deg, dec_deg) in ICRS J2000
            
        Raises:
            ValueError: If format is not recognized or invalid
            
        Examples:
            >>> parse("350.123456 -17.33333")
            (350.123456, -17.33333)
            
            >>> parse("20 54 05.689 +37 01 17.38")
            (313.52370416666665, 37.02149444444444)
            
            >>> parse("15h17m-11d10m")
            (229.25, -11.166666666666666)
        """
        coord_string = coord_string.strip()
        
        # Try decimal degrees (simplest)
        result = CoordinateParser._parse_decimal(coord_string)
        if result:
            return result
            
        # Try sexagesimal (space-separated)
        result = CoordinateParser._parse_sexagesimal(coord_string)
        if result:
            return result
            
        # Try HMS:DMS (colon-separated)
        result = CoordinateParser._parse_hms_dms(coord_string)
        if result:
            return result
            
        # Try mixed notation (15h17m-11d10m)
        result = CoordinateParser._parse_mixed_notation(coord_string)
        if result:
            return result
            
        # Try suffix notation (275d11m15.6954s)
        result = CoordinateParser._parse_suffix(coord_string)
        if result:
            return result
            
        # Try hybrid notation (12.34567h -17.87654d)
        result = CoordinateParser._parse_hybrid(coord_string)
        if result:
            return result
            
        # Try using Astropy's flexible parser as fallback
        try:
            coord = SkyCoord(coord_string, frame='icrs')
            return coord.ra.deg, coord.dec.deg
        except Exception as e:
            logger.warning(f"Astropy parser failed: {e}")
            
        raise ValueError(
            f"Unrecognized coordinate format: '{coord_string}'. "
            "Supported formats: decimal degrees, sexagesimal (HH MM SS.S ±DD MM SS.S), "
            "HMS/DMS (HH:MM:SS.S ±DD:MM:SS.S), mixed notation (15h17m-11d10m), "
            "suffix notation (275d11m15.6954s +17d59m59.876s), or hybrid (12.34567h -17.87654d)"
        )
    
    @staticmethod
    def _parse_decimal(coord_string: str) -> Optional[Tuple[float, float]]:
        """Parse decimal degrees: '350.123456 -17.33333'"""
        match = re.match(CoordinateParser.DECIMAL_PATTERN, coord_string)
        if match:
            ra = float(match.group(1))
            dec = float(match.group(2))
            CoordinateParser._validate_ranges(ra, dec)
            return ra, dec
        return None
    
    @staticmethod
    def _parse_sexagesimal(coord_string: str) -> Optional[Tuple[float, float]]:
        """Parse sexagesimal: '20 54 05.689 +37 01 17.38'"""
        match = re.match(CoordinateParser.SEXAGESIMAL_PATTERN, coord_string)
        if match:
            ra_h, ra_m, ra_s = float(match.group(1)), float(match.group(2)), float(match.group(3))
            dec_d, dec_m, dec_s = float(match.group(4)), float(match.group(5)), float(match.group(6))
            
            # Convert to degrees
            ra_deg = (ra_h + ra_m / 60.0 + ra_s / 3600.0) * 15.0  # Hours to degrees
            dec_deg = abs(dec_d) + dec_m / 60.0 + dec_s / 3600.0
            if dec_d < 0:
                dec_deg = -dec_deg
                
            CoordinateParser._validate_ranges(ra_deg, dec_deg)
            return ra_deg, dec_deg
        return None
    
    @staticmethod
    def _parse_hms_dms(coord_string: str) -> Optional[Tuple[float, float]]:
        """Parse HMS/DMS: '10:12:45.3 -45:17:50'"""
        match = re.match(CoordinateParser.HMS_DMS_PATTERN, coord_string)
        if match:
            ra_h, ra_m, ra_s = float(match.group(1)), float(match.group(2)), float(match.group(3))
            dec_d, dec_m, dec_s = float(match.group(4)), float(match.group(5)), float(match.group(6))
            
            ra_deg = (ra_h + ra_m / 60.0 + ra_s / 3600.0) * 15.0
            dec_deg = abs(dec_d) + dec_m / 60.0 + dec_s / 3600.0
            if dec_d < 0:
                dec_deg = -dec_deg
                
            CoordinateParser._validate_ranges(ra_deg, dec_deg)
            return ra_deg, dec_deg
        return None
    
    @staticmethod
    def _parse_mixed_notation(coord_string: str) -> Optional[Tuple[float, float]]:
        """Parse mixed notation: '15h17m-11d10m' or '15h17+89d15'"""
        match = re.match(CoordinateParser.MIXED_NOTATION_PATTERN, coord_string)
        if match:
            ra_h, ra_m = float(match.group(1)), float(match.group(2))
            dec_d, dec_m = float(match.group(3)), float(match.group(4))
            
            ra_deg = (ra_h + ra_m / 60.0) * 15.0
            dec_deg = abs(dec_d) + dec_m / 60.0
            if dec_d < 0:
                dec_deg = -dec_deg
                
            CoordinateParser._validate_ranges(ra_deg, dec_deg)
            return ra_deg, dec_deg
        return None
    
    @staticmethod
    def _parse_suffix(coord_string: str) -> Optional[Tuple[float, float]]:
        """Parse suffix notation: '275d11m15.6954s +17d59m59.876s'"""
        match = re.match(CoordinateParser.SUFFIX_PATTERN, coord_string)
        if match:
            ra_d, ra_m, ra_s = float(match.group(1)), float(match.group(2)), float(match.group(3))
            dec_d, dec_m, dec_s = float(match.group(4)), float(match.group(5)), float(match.group(6))
            
            ra_deg = ra_d + ra_m / 60.0 + ra_s / 3600.0
            dec_deg = abs(dec_d) + dec_m / 60.0 + dec_s / 3600.0
            if dec_d < 0:
                dec_deg = -dec_deg
                
            CoordinateParser._validate_ranges(ra_deg, dec_deg)
            return ra_deg, dec_deg
        return None
    
    @staticmethod
    def _parse_hybrid(coord_string: str) -> Optional[Tuple[float, float]]:
        """Parse hybrid notation: '12.34567h -17.87654d'"""
        match = re.match(CoordinateParser.HYBRID_PATTERN, coord_string)
        if match:
            ra_h = float(match.group(1))
            dec_d = float(match.group(2))
            
            ra_deg = ra_h * 15.0  # Hours to degrees
            dec_deg = dec_d
            
            CoordinateParser._validate_ranges(ra_deg, dec_deg)
            return ra_deg, dec_deg
        return None
    
    @staticmethod
    def _validate_ranges(ra: float, dec: float):
        """Validate RA/Dec are in valid ranges"""
        if not (0 <= ra < 360):
            raise ValueError(f"RA must be between 0 and 360 degrees, got {ra}")
        if not (-90 <= dec <= 90):
            raise ValueError(f"Dec must be between -90 and 90 degrees, got {dec}")
    
    @staticmethod
    def parse_batch(coord_list: list[str]) -> list[Tuple[float, float, Optional[str]]]:
        """
        Parse a batch of coordinates.
        
        Args:
            coord_list: List of coordinate strings
            
        Returns:
            List of tuples (ra_deg, dec_deg, error_msg)
            error_msg is None if parsing succeeded
        """
        results = []
        for coord in coord_list:
            try:
                ra, dec = CoordinateParser.parse(coord)
                results.append((ra, dec, None))
            except Exception as e:
                results.append((None, None, str(e)))
        return results
