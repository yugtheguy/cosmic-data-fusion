"""
FITS adapter for COSMIC Data Fusion.

Implements BaseAdapter interface for FITS (Flexible Image Transport System) catalog data ingestion.
Handles both single and multi-extension FITS files with binary tables.

Supports astronomical catalogs including:
- Hipparcos (ESA) - High precision parallax catalog
- 2MASS (NASA/IPAC) - Near-infrared sky survey
- Tycho-2 - Astrometric catalog
- Sloan FITS exports - SDSS data in FITS format
- Pan-STARRS FITS tables - Optical/NIR survey
- Gaia FITS exports - Alternative to CSV format
- User-defined catalogs via column mapping

FITS Format Overview:
- Primary HDU (Header Data Unit): Often metadata or empty
- Extension HDUs: Contain actual data in binary tables
- Headers: Contain metadata (TTYPE for column names, TUNIT for units)
- Coordinate Systems: Usually ICRS, but can vary (check RADESYS)

Example Usage:
    adapter = FITSAdapter(dataset_id="hipparcos_v2")
    records, results = adapter.process_batch(
        input_data="hipparcos_sample.fits",
        extension=1,  # Use first extension HDU
        skip_invalid=True
    )
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

import numpy as np
from astropy.io import fits
from astropy.table import Table
from astropy.time import Time

from app.services.adapters.base_adapter import BaseAdapter, ValidationResult
from app.services.utils.unit_converter import UnitConverter

logger = logging.getLogger(__name__)


class FITSAdapter(BaseAdapter):
    """
    Adapter for ingesting FITS catalog data with binary tables.
    
    This adapter is flexible and works with various FITS catalogs by:
    1. Auto-detecting coordinate columns (RA, Dec, and common variants)
    2. Auto-detecting magnitude columns (various band names)
    3. Supporting custom column mappings for non-standard catalogs
    4. Handling multi-extension FITS files
    
    FITS Coordinate Column Detection (case-insensitive):
    - RA variants: ra, RA, RAJ2000, ra_icrs, RAhour
    - Dec variants: dec, DEC, DEJ2000, dec_icrs, DECdeg
    
    FITS Magnitude Column Detection:
    - Standard: mag, Mag, Magnitude, MAG
    - Bands: Vmag, Bmag, Gmag, Jmag, Hmag, Kmag
    - SDSS: psfMag_g, psfMag_r, etc.
    
    Distance/Parallax Columns:
    - Parallax: parallax, Plx, PLX
    - Distance: Distance, Dist, distance_pc
    """
    
    # Common RA column name variants (case-insensitive matching)
    RA_COLUMN_VARIANTS = [
        "ra", "RA", "RAJ2000", "ra_icrs", "RA_ICRS", 
        "ra_deg", "RA_deg", "RAhour", "alpha"
    ]
    
    # Common Dec column name variants
    DEC_COLUMN_VARIANTS = [
        "dec", "DEC", "DEJ2000", "dec_icrs", "DEC_ICRS",
        "dec_deg", "DEC_deg", "DECdeg", "delta"
    ]
    
    # Common magnitude column variants (priority order)
    MAG_COLUMN_VARIANTS = [
        "Gmag", "Vmag", "gmag", "rmag", "Jmag", "Hmag", "Kmag",
        "mag", "Mag", "MAG", "magnitude", "Magnitude",
        "phot_g_mean_mag", "psfMag_g", "psfMag_r",
        "j_m", "h_m", "k_m"  # 2MASS near-infrared bands
    ]
    
    # Parallax column variants
    PARALLAX_COLUMN_VARIANTS = [
        "parallax", "Parallax", "Plx", "PLX", "plx"
    ]
    
    # Distance column variants
    DISTANCE_COLUMN_VARIANTS = [
        "distance", "Distance", "Dist", "distance_pc", "dist_pc"
    ]
    
    # Source ID column variants
    SOURCE_ID_VARIANTS = [
        "source_id", "SOURCE_ID", "objid", "OBJID", "ID", "id",
        "HIP", "hip", "designation", "Designation"
    ]
    
    def __init__(
        self,
        dataset_id: Optional[str] = None,
        column_mapping: Optional[Dict[str, str]] = None
    ):
        """
        Initialize FITS adapter.
        
        Args:
            dataset_id: Optional dataset identifier for tracking
            column_mapping: Optional custom column mapping for non-standard FITS files
                          Format: {"ra": "custom_ra_column", "dec": "custom_dec_column", ...}
        """
        super().__init__(source_name="FITS Catalog", dataset_id=dataset_id)
        self.column_mapping = column_mapping or {}
        self.detected_columns = {}  # Will store auto-detected columns
    
    def parse(self, input_data: Any, **kwargs) -> List[Dict[str, Any]]:
        """
        Parse FITS file into raw records.
        
        Args:
            input_data: Can be:
                - str/Path: file path to .fits or .fits.gz
                - Already opened astropy Table
                - List[Dict]: pre-parsed records (passthrough)
            **kwargs: Additional options:
                - extension: HDU extension to read (int index or str name)
                             Default: first extension with binary table data
                - memmap: Use memory mapping for large files (default: True)
        
        Returns:
            List of raw records as dictionaries
            
        Raises:
            ValueError: If file not found, invalid FITS format, or no data tables
        """
        # Handle pre-parsed data
        if isinstance(input_data, list):
            logger.info(f"Received {len(input_data)} pre-parsed records")
            return input_data
        
        # Handle astropy Table
        if isinstance(input_data, Table):
            return self._table_to_records(input_data)
        
        # Handle file path
        if isinstance(input_data, (str, Path)):
            return self._parse_fits_file(Path(input_data), **kwargs)
        
        raise ValueError(
            f"Unsupported input type: {type(input_data)}. "
            "Expected file path, astropy Table, or list of dicts."
        )
    
    def _parse_fits_file(self, file_path: Path, **kwargs) -> List[Dict[str, Any]]:
        """
        Parse FITS file from disk.
        
        Args:
            file_path: Path to FITS file
            **kwargs: extension (int/str), memmap (bool)
            
        Returns:
            List of record dictionaries
        """
        if not file_path.exists():
            raise ValueError(f"FITS file not found: {file_path}")
        
        logger.info(f"Opening FITS file: {file_path}")
        
        try:
            # Open FITS file
            memmap = kwargs.get('memmap', True)
            with fits.open(file_path, memmap=memmap) as hdul:
                # Log FITS structure
                logger.info(f"FITS file has {len(hdul)} HDU(s)")
                for i, hdu in enumerate(hdul):
                    logger.info(
                        f"  HDU {i}: {hdu.name} "
                        f"({type(hdu).__name__}, "
                        f"{getattr(hdu, 'data', None).__class__.__name__ if hasattr(hdu, 'data') else 'no data'})"
                    )
                
                # Select target HDU
                target_hdu = self._select_data_hdu(hdul, kwargs.get('extension'))
                
                if target_hdu is None:
                    raise ValueError("No data table found in FITS file")
                
                logger.info(f"Reading data from HDU: {target_hdu.name} (index {hdul.index(target_hdu)})")
                
                # Convert to astropy Table
                table = Table(target_hdu.data)
                
                # Store header information for later use
                self._extract_header_metadata(target_hdu.header)
                
                logger.info(f"Parsed {len(table)} records with {len(table.colnames)} columns")
                logger.info(f"Columns: {', '.join(table.colnames[:10])}...")
                
                return self._table_to_records(table)
                
        except Exception as e:
            raise ValueError(f"Failed to parse FITS file: {e}")
    
    def _select_data_hdu(self, hdul: fits.HDUList, extension: Optional[Union[int, str]]) -> Optional[fits.BinTableHDU]:
        """
        Select the HDU containing binary table data.
        
        Args:
            hdul: FITS HDU list
            extension: User-specified extension (int index or str name), or None for auto-detect
            
        Returns:
            Binary table HDU or None if not found
        """
        # User specified extension
        if extension is not None:
            if isinstance(extension, int):
                if extension < len(hdul):
                    return hdul[extension]
                else:
                    raise ValueError(f"HDU index {extension} out of range (file has {len(hdul)} HDUs)")
            elif isinstance(extension, str):
                if extension in hdul:
                    return hdul[extension]
                else:
                    available = [hdu.name for hdu in hdul]
                    raise ValueError(f"HDU '{extension}' not found. Available: {available}")
        
        # Auto-detect: Find first binary table HDU
        for hdu in hdul:
            if isinstance(hdu, fits.BinTableHDU) and hdu.data is not None:
                return hdu
        
        return None
    
    def _extract_header_metadata(self, header: fits.Header):
        """
        Extract useful metadata from FITS header.
        
        Stores coordinate system, observation date, catalog name, etc.
        
        Args:
            header: FITS header object
        """
        self.header_metadata = {
            'coordinate_system': header.get('RADESYS', 'ICRS'),
            'equinox': header.get('EQUINOX', 2000.0),
            'observation_date': header.get('DATE-OBS'),
            'origin': header.get('ORIGIN', 'Unknown'),
            'telescope': header.get('TELESCOP'),
            'instrument': header.get('INSTRUME'),
        }
        
        logger.info(f"FITS metadata: {self.header_metadata}")
    
    def _table_to_records(self, table: Table) -> List[Dict[str, Any]]:
        """
        Convert astropy Table to list of dictionaries.
        
        Args:
            table: Astropy table
            
        Returns:
            List of record dictionaries
        """
        records = []
        
        for row in table:
            record = {}
            for col_name in table.colnames:
                value = row[col_name]
                
                # Handle numpy types and masked values
                if hasattr(value, 'mask') and value.mask:
                    record[col_name] = None
                elif isinstance(value, (np.integer, np.floating)):
                    record[col_name] = value.item()
                elif isinstance(value, np.ndarray):
                    record[col_name] = value.tolist()
                else:
                    record[col_name] = value
            
            records.append(record)
        
        return records
    
    def _detect_column_name(self, record: Dict[str, Any], variants: List[str]) -> Optional[str]:
        """
        Detect column name from variants (case-insensitive).
        
        Args:
            record: Data record
            variants: List of possible column names
            
        Returns:
            Detected column name or None
        """
        record_keys_lower = {k.lower(): k for k in record.keys()}
        
        for variant in variants:
            if variant.lower() in record_keys_lower:
                return record_keys_lower[variant.lower()]
        
        return None
    
    def validate(self, record: Dict[str, Any]) -> ValidationResult:
        """
        Validate a single FITS record using 8-point validation framework.
        
        Validation Rules:
        1. Required fields present (RA, Dec)
        2. Coordinate ranges (RA: 0-360°, Dec: -90-90°)
        3. Coordinate type validation (numeric, not null)
        4. Magnitude reasonableness (-5 to 30 mag)
        5. Distance/Parallax validity (if present)
        6. Metadata integrity (catalog identifiers)
        7. No NaN/Inf values in critical fields
        8. Missing value handling policy
        
        Args:
            record: Raw FITS record dictionary
            
        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult()
        
        # Rule 1: Detect and validate required fields (RA, Dec)
        ra_col = self._detect_column_name(record, self.RA_COLUMN_VARIANTS)
        dec_col = self._detect_column_name(record, self.DEC_COLUMN_VARIANTS)
        
        if not ra_col:
            result.add_error("No RA column found in FITS record")
            return result
        
        if not dec_col:
            result.add_error("No Dec column found in FITS record")
            return result
        
        # Store detected columns for mapping
        self.detected_columns['ra'] = ra_col
        self.detected_columns['dec'] = dec_col
        
        ra_value = record.get(ra_col)
        dec_value = record.get(dec_col)
        
        # Rule 3: Coordinate type validation
        if ra_value is None:
            result.add_error(f"RA ({ra_col}) is null")
            return result
        
        if dec_value is None:
            result.add_error(f"Dec ({dec_col}) is null")
            return result
        
        # Rule 7: Check for NaN/Inf
        try:
            ra_float = float(ra_value)
            dec_float = float(dec_value)
            
            if not np.isfinite(ra_float):
                result.add_error(f"RA ({ra_col}) is NaN or Inf: {ra_value}")
                return result
            
            if not np.isfinite(dec_float):
                result.add_error(f"Dec ({dec_col}) is NaN or Inf: {dec_value}")
                return result
            
        except (ValueError, TypeError) as e:
            result.add_error(f"Invalid coordinate values: {e}")
            return result
        
        # Rule 2: Coordinate ranges
        if not (0.0 <= ra_float < 360.0):
            result.add_error(f"RA out of range [0, 360): {ra_float}")
        
        if not (-90.0 <= dec_float <= 90.0):
            result.add_error(f"Dec out of range [-90, 90]: {dec_float}")
        
        # Rule 4: Magnitude validation (optional field)
        mag_col = self._detect_column_name(record, self.MAG_COLUMN_VARIANTS)
        if mag_col:
            self.detected_columns['magnitude'] = mag_col
            mag_value = record.get(mag_col)
            
            if mag_value is not None:
                try:
                    mag_float = float(mag_value)
                    if np.isfinite(mag_float):
                        if not (-5.0 <= mag_float <= 30.0):
                            result.add_warning(f"Magnitude out of typical range [-5, 30]: {mag_float}")
                    else:
                        result.add_warning(f"Magnitude is NaN or Inf")
                except (ValueError, TypeError):
                    result.add_warning(f"Invalid magnitude value: {mag_value}")
        else:
            result.add_warning("No magnitude column detected")
        
        # Rule 5: Parallax/Distance validation (optional)
        plx_col = self._detect_column_name(record, self.PARALLAX_COLUMN_VARIANTS)
        if plx_col:
            self.detected_columns['parallax'] = plx_col
            plx_value = record.get(plx_col)
            
            if plx_value is not None:
                try:
                    plx_float = float(plx_value)
                    if np.isfinite(plx_float):
                        if plx_float < 0:
                            result.add_warning(f"Negative parallax: {plx_float} mas")
                        elif plx_float > 1000:
                            result.add_warning(f"Very large parallax: {plx_float} mas (distance < 1 pc)")
                except (ValueError, TypeError):
                    result.add_warning(f"Invalid parallax value: {plx_value}")
        
        dist_col = self._detect_column_name(record, self.DISTANCE_COLUMN_VARIANTS)
        if dist_col:
            self.detected_columns['distance'] = dist_col
        
        # Rule 6: Source ID validation
        source_id_col = self._detect_column_name(record, self.SOURCE_ID_VARIANTS)
        if source_id_col:
            self.detected_columns['source_id'] = source_id_col
        else:
            result.add_warning("No source ID column detected, will use row index")
        
        return result
    
    def map_to_unified_schema(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map FITS record to unified schema.
        
        Args:
            record: Validated FITS record
            
        Returns:
            Dictionary with unified schema fields
        """
        # Get detected column names
        ra_col = self.detected_columns.get('ra')
        dec_col = self.detected_columns.get('dec')
        mag_col = self.detected_columns.get('magnitude')
        plx_col = self.detected_columns.get('parallax')
        dist_col = self.detected_columns.get('distance')
        source_id_col = self.detected_columns.get('source_id')
        
        # Extract values
        ra_deg = float(record[ra_col])
        dec_deg = float(record[dec_col])
        
        # Source ID
        if source_id_col:
            source_id = str(record[source_id_col])
        else:
            # Fallback: use coordinate-based ID
            source_id = f"fits_{ra_deg:.6f}_{dec_deg:.6f}"
        
        # Object ID (catalog-specific)
        object_id = f"fits_{self.dataset_id}_{source_id}"
        
        # Magnitude
        brightness_mag = None
        if mag_col and record.get(mag_col) is not None:
            try:
                brightness_mag = float(record[mag_col])
                if not np.isfinite(brightness_mag):
                    brightness_mag = None
            except (ValueError, TypeError):
                pass
        
        # Parallax and distance
        parallax_mas = None
        distance_pc = None
        
        if plx_col and record.get(plx_col) is not None:
            try:
                parallax_mas = float(record[plx_col])
                if np.isfinite(parallax_mas) and parallax_mas > 0:
                    distance_pc = UnitConverter.parallax_to_distance(parallax_mas)
            except (ValueError, TypeError):
                pass
        
        if distance_pc is None and dist_col and record.get(dist_col) is not None:
            try:
                distance_pc = float(record[dist_col])
                if not np.isfinite(distance_pc):
                    distance_pc = None
            except (ValueError, TypeError):
                pass
        
        # Observation time
        observation_time = None
        if hasattr(self, 'header_metadata'):
            date_obs = self.header_metadata.get('observation_date')
            if date_obs:
                try:
                    observation_time = datetime.fromisoformat(str(date_obs))
                except:
                    pass
        
        # Coordinate system
        raw_frame = getattr(self, 'header_metadata', {}).get('coordinate_system', 'ICRS')
        
        # Original source
        origin = getattr(self, 'header_metadata', {}).get('origin', 'FITS Catalog')
        
        # Raw metadata: store all non-standard fields
        raw_metadata = {}
        standard_fields = {ra_col, dec_col, mag_col, plx_col, dist_col, source_id_col}
        for key, value in record.items():
            if key not in standard_fields and value is not None:
                # Store extra fields
                if isinstance(value, (int, float, str, bool)):
                    raw_metadata[key] = value
                elif isinstance(value, (list, np.ndarray)):
                    raw_metadata[key] = str(value)
        
        return {
            'object_id': object_id,
            'source_id': source_id,
            'ra_deg': ra_deg,
            'dec_deg': dec_deg,
            'brightness_mag': brightness_mag,
            'parallax_mas': parallax_mas,
            'distance_pc': distance_pc,
            'original_source': origin,
            'raw_frame': raw_frame,
            'observation_time': observation_time,
            'dataset_id': self.dataset_id,
            'raw_metadata': raw_metadata if raw_metadata else None,
        }
