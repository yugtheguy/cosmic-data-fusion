"""
CSV adapter for COSMIC Data Fusion.

Implements BaseAdapter interface for generic CSV catalog data ingestion.
Handles flexible CSV formats with auto-detection and custom column mapping.

Supports:
- Any CSV astronomical catalog with configurable column mappings
- Auto-detection of common astronomical column names
- Multiple delimiter support (comma, tab, semicolon, pipe)
- Header auto-detection
- Custom column name mapping for non-standard formats
- Data type inference and conversion

Example Usage:
    # Auto-detection mode (for standard column names)
    adapter = CSVAdapter(dataset_id="custom_catalog")
    records, results = adapter.process_batch("my_catalog.csv")
    
    # Custom mapping mode (for non-standard columns)
    adapter = CSVAdapter(
        dataset_id="custom_catalog",
        column_mapping={
            "ra": "RIGHT_ASCENSION",
            "dec": "DECLINATION", 
            "magnitude": "MAG_V",
            "parallax": "PLX"
        }
    )
    records, results = adapter.process_batch("custom_catalog.csv")
"""

import csv
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from io import StringIO

import numpy as np
from sqlalchemy.orm import Session

from app.services.adapters.base_adapter import BaseAdapter, ValidationResult
from app.services.utils.unit_converter import UnitConverter

logger = logging.getLogger(__name__)


class CSVAdapter(BaseAdapter):
    """
    Flexible adapter for ingesting generic CSV astronomical catalogs.
    
    This adapter handles various CSV formats by:
    1. Auto-detecting delimiter (comma, tab, semicolon, pipe)
    2. Auto-detecting common astronomical column names
    3. Supporting custom column mappings for non-standard formats
    4. Validating astronomical coordinates and measurements
    5. Converting units as needed
    
    Column Detection (case-insensitive):
    - RA: ra, RA, right_ascension, RAJ2000, ra_deg, alpha
    - Dec: dec, DEC, declination, DEJ2000, dec_deg, delta
    - Magnitude: mag, magnitude, Vmag, Gmag, brightness
    - Parallax: parallax, plx, parallax_mas
    - Distance: distance, dist, distance_pc
    - Source ID: id, source_id, objid, catalog_id
    """
    
    # Common RA column name variants (case-insensitive)
    RA_COLUMN_VARIANTS = [
        "ra", "RA", "right_ascension", "RIGHT_ASCENSION", "RAJ2000",
        "ra_deg", "RA_deg", "ra_icrs", "RA_ICRS", "alpha", "Alpha"
    ]
    
    # Common Dec column name variants
    DEC_COLUMN_VARIANTS = [
        "dec", "DEC", "declination", "DECLINATION", "DEJ2000",
        "dec_deg", "DEC_deg", "dec_icrs", "DEC_ICRS", "delta", "Delta"
    ]
    
    # Common magnitude column variants (priority order)
    MAG_COLUMN_VARIANTS = [
        "mag", "Mag", "MAG", "magnitude", "Magnitude", "MAGNITUDE",
        "brightness", "Brightness", "brightness_mag",
        "Vmag", "Gmag", "Rmag", "Bmag", "Imag",  # Standard bands
        "vmag", "gmag", "rmag", "bmag", "imag",
        "phot_g_mean_mag", "psfMag_g"
    ]
    
    # Parallax column variants
    PARALLAX_COLUMN_VARIANTS = [
        "parallax", "Parallax", "PARALLAX", "plx", "Plx", "PLX",
        "parallax_mas", "parallax_milliarcsec"
    ]
    
    # Distance column variants
    DISTANCE_COLUMN_VARIANTS = [
        "distance", "Distance", "DISTANCE", "dist", "Dist",
        "distance_pc", "dist_pc", "Distance_pc"
    ]
    
    # Source ID column variants
    SOURCE_ID_VARIANTS = [
        "id", "ID", "source_id", "SOURCE_ID", "objid", "OBJID",
        "catalog_id", "object_id", "star_id", "designation"
    ]
    
    # Supported delimiters for auto-detection
    SUPPORTED_DELIMITERS = [',', '\t', ';', '|']
    
    def __init__(
        self,
        db: Optional[Session] = None,
        error_reporter=None,
        dataset_id: Optional[str] = None,
        column_mapping: Optional[Dict[str, str]] = None,
        delimiter: Optional[str] = None,
    ):
        """Initialize CSV adapter.

        Accepts either a dataset_id (legacy usage) or a SQLAlchemy Session as the
        first positional argument (new usage from full-stack tests).
        """
        db_session = db if isinstance(db, Session) else None
        dataset_value = None
        if isinstance(db, str):
            dataset_value = db
        elif dataset_id:
            dataset_value = dataset_id

        super().__init__(
            source_name="CSV Catalog",
            dataset_id=dataset_value,
            db=db_session,
            error_reporter=error_reporter,
        )
        self.column_mapping = column_mapping or {}
        self.delimiter = delimiter
        self.detected_columns = {}  # Will store auto-detected columns
        self.detected_delimiter = None
    
    def parse(self, input_data: Any, **kwargs) -> List[Dict[str, Any]]:
        """
        Parse CSV input into raw records.
        
        Args:
            input_data: Can be:
                - str/Path: file path to CSV
                - StringIO/file-like: file content
                - List[Dict]: pre-parsed records (passthrough)
            **kwargs: Additional options:
                - encoding: File encoding (default: 'utf-8')
                - skip_rows: Number of rows to skip (default: 0)
                - max_rows: Maximum rows to read (default: None = all)
                - has_header: Whether CSV has header row (default: True)
        
        Returns:
            List of raw records as dictionaries
            
        Raises:
            ValueError: If file not found, invalid format, or cannot parse
        """
        # Handle pre-parsed data
        if isinstance(input_data, list):
            logger.info(f"Received {len(input_data)} pre-parsed records")
            return input_data
        
        # Handle file path
        if isinstance(input_data, (str, Path)):
            return self._parse_csv_file(Path(input_data), **kwargs)
        
        # Handle file-like object (StringIO, uploaded file, etc.)
        if hasattr(input_data, 'read'):
            return self._parse_csv_filelike(input_data, **kwargs)
        
        raise ValueError(
            f"Unsupported input type: {type(input_data)}. "
            "Expected file path, file-like object, or List[Dict]"
        )
    
    def _parse_csv_file(self, file_path: Path, **kwargs) -> List[Dict[str, Any]]:
        """
        Parse CSV file from disk.
        
        Args:
            file_path: Path to CSV file
            **kwargs: Parsing options
            
        Returns:
            List of record dictionaries
        """
        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")
        
        encoding = kwargs.get('encoding', 'utf-8')
        
        logger.info(f"Parsing CSV file: {file_path}")
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return self._parse_csv_filelike(f, **kwargs)
        except UnicodeDecodeError as e:
            # Try alternative encodings
            logger.warning(f"UTF-8 decode failed, trying latin-1: {e}")
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return self._parse_csv_filelike(f, **kwargs)
            except Exception as e2:
                raise ValueError(f"Failed to decode CSV file: {e2}")
        except Exception as e:
            raise ValueError(f"Failed to read CSV file: {e}")
    
    def _parse_csv_filelike(self, file_obj, **kwargs) -> List[Dict[str, Any]]:
        """
        Parse CSV from file-like object.
        
        Args:
            file_obj: File-like object with read() method
            **kwargs: Parsing options
            
        Returns:
            List of record dictionaries
        """
        skip_rows = kwargs.get('skip_rows', 0)
        max_rows = kwargs.get('max_rows', None)
        has_header = kwargs.get('has_header', True)
        
        try:
            # Read content
            if hasattr(file_obj, 'seek'):
                file_obj.seek(0)
            
            content = file_obj.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            
            # Auto-detect delimiter if not specified
            if self.delimiter is None:
                self.detected_delimiter = self._detect_delimiter(content)
                logger.info(f"Auto-detected delimiter: {repr(self.detected_delimiter)}")
            else:
                self.detected_delimiter = self.delimiter
            
            # Filter comment lines and skip rows
            lines = []
            line_num = 0
            for line in content.split('\n'):
                line_stripped = line.strip()
                
                # Skip empty lines and comments
                if not line_stripped or line_stripped.startswith('#'):
                    continue
                
                # Skip requested number of rows
                if line_num < skip_rows:
                    line_num += 1
                    continue
                
                lines.append(line)
                line_num += 1
            
            if not lines:
                raise ValueError("No data lines found in CSV")
            
            # Parse CSV
            csv_content = '\n'.join(lines)
            reader = csv.DictReader(
                StringIO(csv_content),
                delimiter=self.detected_delimiter
            )
            
            records = []
            for row_num, row in enumerate(reader, start=1):
                # Stop at max_rows if specified
                if max_rows and row_num > max_rows:
                    break
                
                # Clean keys and values (remove whitespace)
                cleaned_row = {k.strip(): v.strip() if v else None for k, v in row.items()}
                
                # Add row number for debugging
                cleaned_row['_row_num'] = row_num + skip_rows
                
                records.append(cleaned_row)
            
            logger.info(f"Parsed {len(records)} records from CSV")
            return records
            
        except Exception as e:
            raise ValueError(f"Failed to parse CSV: {e}")
    
    def _detect_delimiter(self, content: str) -> str:
        """
        Auto-detect CSV delimiter.
        
        Args:
            content: CSV file content
            
        Returns:
            Detected delimiter character
        """
        # Get first few non-comment lines for detection
        lines = []
        for line in content.split('\n')[:10]:
            line_stripped = line.strip()
            if line_stripped and not line_stripped.startswith('#'):
                lines.append(line)
        
        if not lines:
            return ','  # Default to comma
        
        # Count occurrences of each delimiter in first few lines
        delimiter_counts = {delim: 0 for delim in self.SUPPORTED_DELIMITERS}
        
        for line in lines[:5]:  # Check first 5 data lines
            for delim in self.SUPPORTED_DELIMITERS:
                count = line.count(delim)
                delimiter_counts[delim] += count
        
        # Choose delimiter with most occurrences
        best_delimiter = max(delimiter_counts, key=delimiter_counts.get)
        
        if delimiter_counts[best_delimiter] == 0:
            logger.warning("No delimiter detected, defaulting to comma")
            return ','
        
        return best_delimiter
    
    def _detect_column_name(self, record: Dict[str, Any], variants: List[str]) -> Optional[str]:
        """
        Detect column name from variants (case-insensitive).
        
        Args:
            record: Data record
            variants: List of possible column names
            
        Returns:
            Detected column name or None
        """
        # First check if custom mapping exists
        for key in variants:
            if key.lower() in [k.lower() for k in self.column_mapping.keys()]:
                mapped_name = self.column_mapping.get(key.lower())
                if mapped_name in record:
                    return mapped_name
        
        # Fall back to auto-detection
        record_keys_lower = {k.lower(): k for k in record.keys()}
        
        for variant in variants:
            if variant.lower() in record_keys_lower:
                return record_keys_lower[variant.lower()]
        
        return None
    
    def validate(self, record: Dict[str, Any]) -> ValidationResult:
        """
        Validate a single CSV record using 8-point validation framework.
        
        Validation Rules:
        1. Required fields present (RA, Dec)
        2. Coordinate ranges (RA: 0-360°, Dec: -90-90°)
        3. Coordinate type validation (numeric, not null)
        4. Magnitude reasonableness (-5 to 30 mag)
        5. Distance/Parallax validity (if present)
        6. Metadata integrity (source identifiers)
        7. No NaN/Inf values in critical fields
        8. Missing value handling policy
        
        Args:
            record: Raw CSV record dictionary
            
        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult()
        row_num = record.get('_row_num', 'unknown')
        
        # Rule 1: Detect and validate required fields (RA, Dec)
        ra_col = self._detect_column_name(record, self.RA_COLUMN_VARIANTS)
        dec_col = self._detect_column_name(record, self.DEC_COLUMN_VARIANTS)
        
        if not ra_col:
            result.add_error(f"Row {row_num}: No RA column found in CSV record")
            return result
        
        if not dec_col:
            result.add_error(f"Row {row_num}: No Dec column found in CSV record")
            return result
        
        # Store detected columns for mapping
        self.detected_columns['ra'] = ra_col
        self.detected_columns['dec'] = dec_col
        
        ra_value = record.get(ra_col)
        dec_value = record.get(dec_col)
        
        # Rule 3: Coordinate type validation
        if ra_value is None or ra_value == '':
            result.add_error(f"Row {row_num}: RA ({ra_col}) is null or empty")
            return result
        
        if dec_value is None or dec_value == '':
            result.add_error(f"Row {row_num}: Dec ({dec_col}) is null or empty")
            return result
        
        # Rule 7: Check for NaN/Inf and convert to float
        try:
            ra_float = float(ra_value)
            dec_float = float(dec_value)
            
            if not np.isfinite(ra_float):
                result.add_error(f"Row {row_num}: RA ({ra_col}) is NaN or Inf: {ra_value}")
                return result
            
            if not np.isfinite(dec_float):
                result.add_error(f"Row {row_num}: Dec ({dec_col}) is NaN or Inf: {dec_value}")
                return result
            
        except (ValueError, TypeError) as e:
            result.add_error(f"Row {row_num}: Invalid coordinate values: {e}")
            return result
        
        # Rule 2: Coordinate ranges
        if not (0.0 <= ra_float < 360.0):
            result.add_error(f"Row {row_num}: RA out of range [0, 360): {ra_float}")
        
        if not (-90.0 <= dec_float <= 90.0):
            result.add_error(f"Row {row_num}: Dec out of range [-90, 90]: {dec_float}")
        
        # Warn for near-pole objects
        if abs(dec_float) > 85:
            result.add_warning(
                f"Row {row_num}: Near-pole object (dec={dec_float:.2f}°), "
                "verify coordinate precision"
            )
        
        # Rule 4: Magnitude validation (optional field)
        mag_col = self._detect_column_name(record, self.MAG_COLUMN_VARIANTS)
        if mag_col:
            self.detected_columns['magnitude'] = mag_col
            mag_value = record.get(mag_col)
            
            if mag_value is not None and mag_value != '':
                try:
                    mag_float = float(mag_value)
                    if np.isfinite(mag_float):
                        if not (-5.0 <= mag_float <= 30.0):
                            result.add_warning(
                                f"Row {row_num}: Magnitude out of typical range [-5, 30]: {mag_float}"
                            )
                        
                        # Flag suspicious zero magnitude
                        if mag_float == 0.0:
                            result.add_warning(
                                f"Row {row_num}: Magnitude exactly 0.0, likely bad data"
                            )
                    else:
                        result.add_warning(f"Row {row_num}: Magnitude is NaN or Inf: {mag_value}")
                except (ValueError, TypeError):
                    result.add_warning(f"Row {row_num}: Invalid magnitude value: {mag_value}")
        
        # Rule 5: Parallax validation (if present)
        parallax_col = self._detect_column_name(record, self.PARALLAX_COLUMN_VARIANTS)
        if parallax_col:
            self.detected_columns['parallax'] = parallax_col
            parallax_value = record.get(parallax_col)
            
            if parallax_value is not None and parallax_value != '':
                try:
                    parallax_float = float(parallax_value)
                    
                    if np.isfinite(parallax_float):
                        # Negative parallax warning
                        if parallax_float <= 0:
                            result.add_warning(
                                f"Row {row_num}: Non-positive parallax ({parallax_float:.3f} mas), "
                                "cannot compute distance"
                            )
                        
                        # Very large parallax (very nearby)
                        if parallax_float > 1000:
                            result.add_warning(
                                f"Row {row_num}: Very large parallax ({parallax_float:.3f} mas), "
                                "distance < 1 pc - verify data"
                            )
                        
                        # Very small parallax (very distant)
                        if 0 < parallax_float < 0.1:
                            result.add_warning(
                                f"Row {row_num}: Very small parallax ({parallax_float:.3f} mas), "
                                "distance > 10 kpc, high uncertainty expected"
                            )
                except (ValueError, TypeError):
                    result.add_warning(f"Row {row_num}: Invalid parallax value: {parallax_value}")
        
        # Rule 5: Distance validation (if present)
        distance_col = self._detect_column_name(record, self.DISTANCE_COLUMN_VARIANTS)
        if distance_col:
            self.detected_columns['distance'] = distance_col
            distance_value = record.get(distance_col)
            
            if distance_value is not None and distance_value != '':
                try:
                    distance_float = float(distance_value)
                    
                    if np.isfinite(distance_float):
                        if distance_float <= 0:
                            result.add_warning(
                                f"Row {row_num}: Non-positive distance ({distance_float} pc), invalid"
                            )
                        
                        # Very large distance
                        if distance_float > 1e6:
                            result.add_warning(
                                f"Row {row_num}: Very large distance ({distance_float} pc), "
                                "> 1 Mpc - verify data"
                            )
                except (ValueError, TypeError):
                    result.add_warning(f"Row {row_num}: Invalid distance value: {distance_value}")
        
        # Rule 6: Source ID detection (optional)
        source_id_col = self._detect_column_name(record, self.SOURCE_ID_VARIANTS)
        if source_id_col:
            self.detected_columns['source_id'] = source_id_col
        
        return result
    
    def map_to_unified_schema(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map CSV record to unified schema.
        
        Args:
            record: Validated raw record
            
        Returns:
            Dictionary with unified schema fields
        """
        # Get detected column names (from validation)
        ra_col = self.detected_columns.get('ra')
        dec_col = self.detected_columns.get('dec')
        mag_col = self.detected_columns.get('magnitude')
        parallax_col = self.detected_columns.get('parallax')
        distance_col = self.detected_columns.get('distance')
        source_id_col = self.detected_columns.get('source_id')
        
        # Extract and convert values
        ra_deg = float(record[ra_col])
        dec_deg = float(record[dec_col])
        
        # Build unified record with required fields
        unified = {
            'ra_deg': ra_deg,
            'dec_deg': dec_deg,
            'source_id': 'unknown',  # Default, will update if found
            'brightness_mag': 12.0,  # Default, will update if found
            'original_source': self.source_name,
            'raw_frame': 'ICRS',  # CSV data assumed to be ICRS
            'dataset_id': self.dataset_id,
            'observation_time': datetime.now(timezone.utc)
        }
        
        # Optional magnitude
        if mag_col and record.get(mag_col):
            try:
                unified['brightness_mag'] = float(record[mag_col])
            except (ValueError, TypeError):
                pass
        
        # Optional parallax -> distance conversion
        if parallax_col and record.get(parallax_col):
            try:
                parallax_mas = float(record[parallax_col])
                unified['parallax_mas'] = parallax_mas
                
                # Convert to distance if parallax is positive
                if parallax_mas > 0:
                    distance_pc = UnitConverter.parallax_to_distance(parallax_mas)
                    unified['distance_pc'] = distance_pc
            except (ValueError, TypeError):
                pass
        
        # Optional distance (if parallax not available)
        if distance_col and record.get(distance_col) and 'distance_pc' not in unified:
            try:
                distance_pc = float(record[distance_col])
                if distance_pc > 0:
                    unified['distance_pc'] = distance_pc
            except (ValueError, TypeError):
                pass
        
        # Optional source ID
        if source_id_col and record.get(source_id_col):
            unified['source_id'] = str(record[source_id_col])
        
        # Store additional metadata as JSON
        raw_metadata = {}
        
        # Include all other columns as metadata
        for key, value in record.items():
            if key.startswith('_'):
                continue  # Skip internal fields
            
            # Skip already mapped fields
            if key in [ra_col, dec_col, mag_col, parallax_col, distance_col, source_id_col]:
                continue
            
            # Store non-null values
            if value is not None and value != '':
                raw_metadata[key] = value
        
        if raw_metadata:
            unified['raw_metadata'] = raw_metadata
        
        return unified
    def get_catalog_type(self) -> str:
        return "csv"

    def get_source_type(self) -> str:
        return "CSV"

    def _get_raw_config(self) -> Optional[dict]:
        return {
            "column_mapping": self.column_mapping,
            "delimiter": self.detected_delimiter,
            "detected_columns": self.detected_columns,
        }