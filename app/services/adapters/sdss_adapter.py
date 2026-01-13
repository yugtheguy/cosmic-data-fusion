"""
SDSS DR17 adapter for COSMIC Data Fusion.

Implements BaseAdapter interface for SDSS (Sloan Digital Sky Survey) catalog data ingestion.
Handles CSV and FITS file formats, validates SDSS-specific fields (ugriz photometry, redshift),
and transforms data to the unified schema.

IMPORTANT LICENSING NOTE:
SDSS data is publicly available under open data policy.
See: https://www.sdss.org/collaboration/citing-sdss/
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from io import StringIO

from app.services.adapters.base_adapter import BaseAdapter, ValidationResult
from app.services.utils.unit_converter import UnitConverter

logger = logging.getLogger(__name__)


class SDSSAdapter(BaseAdapter):
    """
    Adapter for ingesting SDSS DR17 catalog data.
    
    Supports:
    - CSV file parsing (photometric + spectroscopic)
    - FITS file parsing (future)
    - Coordinate validation (ICRS J2000)
    - Redshift to distance conversion
    - Multi-band photometry (ugriz)
    
    SDSS DR17 Specifics:
    - Coordinates are already in ICRS J2000
    - Five photometric filters: u, g, r, i, z (ugriz system)
    - Redshift available for spectroscopic objects
    - Spectral classification for stars and galaxies
    """
    
    # Required SDSS columns (minimum for ingestion)
    REQUIRED_COLUMNS = ["objid", "ra", "dec"]
    
    # Optional columns we can use
    OPTIONAL_COLUMNS = [
        # Photometry (PSF magnitudes)
        "psfMag_u", "psfMag_g", "psfMag_r", "psfMag_i", "psfMag_z",
        # Spectroscopy
        "z", "zErr", "specClass", "subClass",
        # Proper motion
        "pmra", "pmdec",
        # Extinction
        "extinction_u", "extinction_g", "extinction_r", "extinction_i", "extinction_z"
    ]
    
    # Column mapping: SDSS column -> internal name
    COLUMN_MAPPING = {
        "objid": "source_id",
        "ra": "ra",
        "dec": "dec",
        "psfMag_g": "brightness_mag",  # Use g-band as primary magnitude
        "z": "redshift",
        "zErr": "redshift_error",
        "specClass": "spectral_class",
        "subClass": "spectral_subclass",
    }
    
    def __init__(
        self,
        dataset_id: Optional[str] = None,
        apply_extinction_correction: bool = False
    ):
        """
        Initialize SDSS adapter.
        
        Args:
            dataset_id: Optional dataset identifier
            apply_extinction_correction: Whether to apply Galactic extinction correction
                                         to magnitudes (not implemented yet)
        """
        super().__init__(source_name="SDSS DR17", dataset_id=dataset_id)
        self.apply_extinction_correction = apply_extinction_correction
        
        if apply_extinction_correction:
            logger.warning(
                "Extinction correction requested but not yet implemented. "
                "Using raw magnitude values."
            )
    
    def parse(self, input_data: Any, **kwargs) -> List[Dict[str, Any]]:
        """
        Parse input data into raw records.
        
        Args:
            input_data: Can be:
                - str/Path: file path to CSV
                - StringIO/file-like: file content
                - List[Dict]: pre-parsed records
            **kwargs: Additional options
                - encoding: File encoding (default: 'utf-8')
        
        Returns:
            List of raw records as dictionaries
            
        Raises:
            ValueError: If input format is invalid or file cannot be read
        """
        encoding = kwargs.get('encoding', 'utf-8')
        
        # Handle different input types
        if isinstance(input_data, (str, Path)):
            # File path
            return self._parse_csv_file(Path(input_data), encoding)
        
        elif isinstance(input_data, StringIO):
            # StringIO object
            return self._parse_csv_stringio(input_data)
        
        elif isinstance(input_data, list):
            # Pre-parsed records
            logger.info(f"Received {len(input_data)} pre-parsed records")
            return input_data
        
        else:
            raise ValueError(
                f"Unsupported input type: {type(input_data)}. "
                "Expected file path, StringIO, or List[Dict]"
            )
    
    def _parse_csv_file(self, file_path: Path, encoding: str) -> List[Dict[str, Any]]:
        """
        Parse CSV file into records.
        
        Args:
            file_path: Path to CSV file
            encoding: File encoding
            
        Returns:
            List of raw records
        """
        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")
        
        logger.info(f"Parsing SDSS CSV file: {file_path}")
        
        records = []
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                # Filter out comment lines (lines starting with '#')
                lines = [line for line in f if not line.strip().startswith('#')]
                
                # Parse CSV
                reader = csv.DictReader(lines)
                
                for row_num, row in enumerate(reader, start=1):
                    # Clean up whitespace in values
                    cleaned_row = {k.strip(): v.strip() if isinstance(v, str) else v 
                                   for k, v in row.items()}
                    records.append(cleaned_row)
                    
            logger.info(f"Successfully parsed {len(records)} records from {file_path.name}")
            return records
            
        except Exception as e:
            logger.error(f"Failed to parse CSV file: {e}")
            raise ValueError(f"CSV parsing error: {e}")
    
    def _parse_csv_stringio(self, string_io: StringIO) -> List[Dict[str, Any]]:
        """
        Parse CSV from StringIO object.
        
        Args:
            string_io: StringIO containing CSV data
            
        Returns:
            List of raw records
        """
        logger.info("Parsing SDSS CSV from StringIO")
        
        records = []
        
        try:
            # Read all lines and filter comments
            string_io.seek(0)
            lines = [line for line in string_io if not line.strip().startswith('#')]
            
            # Parse CSV
            reader = csv.DictReader(lines)
            
            for row in reader:
                # Clean up whitespace
                cleaned_row = {k.strip(): v.strip() if isinstance(v, str) else v 
                               for k, v in row.items()}
                records.append(cleaned_row)
            
            logger.info(f"Successfully parsed {len(records)} records from StringIO")
            return records
            
        except Exception as e:
            logger.error(f"Failed to parse StringIO: {e}")
            raise ValueError(f"CSV parsing error: {e}")
    
    def validate(self, record: Dict[str, Any]) -> ValidationResult:
        """
        Validate a single SDSS record.
        
        Performs comprehensive validation including:
        - Coordinate range checks
        - Magnitude validity
        - Redshift range (if present)
        - Required fields presence
        
        Args:
            record: Raw record dictionary
            
        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult()
        
        # Check 1: Required fields presence
        for field in self.REQUIRED_COLUMNS:
            if field not in record or record[field] in [None, '', 'null', 'NULL']:
                result.add_error(f"Missing required field: {field}")
        
        # If required fields missing, return early
        if not result.is_valid:
            return result
        
        # Check 2: Coordinate ranges (RA: 0-360°, Dec: -90 to +90°)
        try:
            ra = float(record.get('ra', 0))
            dec = float(record.get('dec', 0))
            
            if not (0 <= ra < 360):
                result.add_error(f"RA out of range [0, 360): {ra}")
            
            if not (-90 <= dec <= 90):
                result.add_error(f"Dec out of range [-90, 90]: {dec}")
                
        except (ValueError, TypeError) as e:
            result.add_error(f"Invalid RA/Dec values: {e}")
        
        # Check 3: At least one magnitude present
        mag_fields = ['psfMag_u', 'psfMag_g', 'psfMag_r', 'psfMag_i', 'psfMag_z']
        has_magnitude = False
        
        for mag_field in mag_fields:
            if mag_field in record and record[mag_field] not in [None, '', 'null', 'NULL']:
                try:
                    mag_value = float(record[mag_field])
                    if not (-30 <= mag_value <= 50):  # Sanity check
                        result.add_warning(f"{mag_field} unusual value: {mag_value}")
                    else:
                        has_magnitude = True
                except (ValueError, TypeError):
                    result.add_warning(f"{mag_field} not numeric: {record[mag_field]}")
        
        if not has_magnitude:
            result.add_error("No valid magnitude values found (ugriz)")
        
        # Check 4: Magnitude reasonableness (typical range 3-30 mag)
        for mag_field in mag_fields:
            if mag_field in record and record[mag_field] not in [None, '', 'null', 'NULL']:
                try:
                    mag = float(record[mag_field])
                    
                    if mag < 3:
                        result.add_warning(f"{mag_field} extremely bright: {mag} mag (< 3)")
                    elif mag > 30:
                        result.add_warning(f"{mag_field} extremely faint: {mag} mag (> 30)")
                    elif mag < 0:
                        result.add_error(f"{mag_field} negative magnitude: {mag}")
                        
                except (ValueError, TypeError):
                    pass  # Already handled in Check 3
        
        # Check 5: Redshift validity (if present)
        if 'z' in record and record['z'] not in [None, '', 'null', 'NULL']:
            try:
                redshift = float(record['z'])
                
                if redshift < 0:
                    result.add_error(f"Negative redshift: {redshift}")
                elif redshift > 7.0:
                    result.add_warning(f"Very high redshift: {redshift} (> 7, unusual)")
                elif redshift > 10.0:
                    result.add_error(f"Redshift out of range: {redshift} (> 10)")
                    
            except (ValueError, TypeError):
                result.add_warning(f"Invalid redshift value: {record['z']}")
        
        # Check 6: Extinction values non-negative (if present)
        extinction_fields = ['extinction_u', 'extinction_g', 'extinction_r', 
                           'extinction_i', 'extinction_z']
        
        for ext_field in extinction_fields:
            if ext_field in record and record[ext_field] not in [None, '', 'null', 'NULL']:
                try:
                    extinction = float(record[ext_field])
                    
                    if extinction < 0:
                        result.add_error(f"{ext_field} negative: {extinction}")
                    elif extinction > 5.0:
                        result.add_warning(f"{ext_field} very high: {extinction} (> 5 mag)")
                        
                except (ValueError, TypeError):
                    result.add_warning(f"{ext_field} not numeric: {record[ext_field]}")
        
        # Check 7: Spectral class validity (if present)
        if 'specClass' in record and record['specClass'] not in [None, '', 'null', 'NULL']:
            valid_classes = ['STAR', 'GALAXY', 'QSO', 'UNKNOWN']
            spec_class = str(record['specClass']).upper().strip()
            
            if spec_class not in valid_classes:
                result.add_warning(
                    f"Unusual spectral class: {record['specClass']} "
                    f"(expected: {', '.join(valid_classes)})"
                )
        
        # Check 8: Object ID format (SDSS uses 64-bit integers)
        if 'objid' in record:
            try:
                objid = str(record['objid'])
                
                # SDSS object IDs are typically 18-19 digit numbers
                if not objid.isdigit():
                    result.add_warning(f"Object ID not numeric: {objid}")
                elif len(objid) < 10 or len(objid) > 25:
                    result.add_warning(f"Object ID unusual length: {len(objid)} digits")
                    
            except (ValueError, TypeError):
                result.add_error(f"Invalid object ID: {record['objid']}")
        
        return result
    
    def map_to_unified_schema(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map SDSS record to unified schema.
        
        Transforms SDSS fields to the standard UnifiedStarCatalog format.
        Preserves all ugriz magnitudes in raw_metadata.
        
        Args:
            record: Validated SDSS record
            
        Returns:
            Dictionary matching UnifiedStarCatalog schema
        """
        converter = UnitConverter()
        
        # Extract basic fields
        objid = record.get('objid', 'unknown')
        ra = float(record.get('ra', 0))
        dec = float(record.get('dec', 0))
        
        # Use g-band magnitude as primary brightness (most analogous to Gaia G-band)
        brightness_mag = None
        if 'psfMag_g' in record and record['psfMag_g'] not in [None, '', 'null', 'NULL']:
            try:
                brightness_mag = float(record['psfMag_g'])
            except (ValueError, TypeError):
                pass
        
        # Calculate distance from redshift (if available)
        distance_pc = None
        parallax_mas = None  # SDSS doesn't provide parallax
        
        if 'z' in record and record['z'] not in [None, '', 'null', 'NULL']:
            try:
                redshift = float(record['z'])
                if redshift >= 0:
                    distance_pc = converter.redshift_to_distance(redshift)
            except (ValueError, TypeError):
                pass
        
        # Extract observation time (if available)
        observation_time = None
        if 'mjd' in record:
            try:
                # MJD (Modified Julian Date) to datetime conversion
                from datetime import datetime, timedelta
                mjd = float(record['mjd'])
                # MJD epoch: November 17, 1858
                mjd_epoch = datetime(1858, 11, 17)
                observation_time = mjd_epoch + timedelta(days=mjd)
            except (ValueError, TypeError):
                pass
        
        # Build raw_metadata with all SDSS-specific fields
        raw_metadata = {}
        
        # Preserve all five magnitudes (ugriz)
        for band in ['u', 'g', 'r', 'i', 'z']:
            mag_field = f'psfMag_{band}'
            if mag_field in record and record[mag_field] not in [None, '', 'null', 'NULL']:
                try:
                    raw_metadata[mag_field] = float(record[mag_field])
                except (ValueError, TypeError):
                    pass
        
        # Preserve extinction values
        for band in ['u', 'g', 'r', 'i', 'z']:
            ext_field = f'extinction_{band}'
            if ext_field in record and record[ext_field] not in [None, '', 'null', 'NULL']:
                try:
                    raw_metadata[ext_field] = float(record[ext_field])
                except (ValueError, TypeError):
                    pass
        
        # Preserve spectroscopic information
        if 'z' in record and record['z'] not in [None, '', 'null', 'NULL']:
            try:
                raw_metadata['redshift'] = float(record['z'])
            except (ValueError, TypeError):
                pass
        
        if 'zErr' in record and record['zErr'] not in [None, '', 'null', 'NULL']:
            try:
                raw_metadata['redshift_error'] = float(record['zErr'])
            except (ValueError, TypeError):
                pass
        
        if 'specClass' in record and record['specClass']:
            raw_metadata['spectral_class'] = str(record['specClass'])
        
        if 'subClass' in record and record['subClass']:
            raw_metadata['spectral_subclass'] = str(record['subClass'])
        
        # Preserve proper motion (if available)
        if 'pmra' in record and record['pmra'] not in [None, '', 'null', 'NULL']:
            try:
                raw_metadata['pmra'] = float(record['pmra'])
            except (ValueError, TypeError):
                pass
        
        if 'pmdec' in record and record['pmdec'] not in [None, '', 'null', 'NULL']:
            try:
                raw_metadata['pmdec'] = float(record['pmdec'])
            except (ValueError, TypeError):
                pass
        
        # Return mapped record
        return {
            'object_id': f"sdss_dr17_{objid}",
            'source_id': f"SDSS DR17 {objid}",
            'ra_deg': ra,
            'dec_deg': dec,
            'brightness_mag': brightness_mag,
            'parallax_mas': parallax_mas,  # None for SDSS
            'distance_pc': distance_pc,
            'original_source': 'SDSS DR17',
            'raw_frame': 'ICRS',  # SDSS uses ICRS J2000
            'observation_time': observation_time,
            'dataset_id': self.dataset_id,
            'raw_metadata': raw_metadata
        }
