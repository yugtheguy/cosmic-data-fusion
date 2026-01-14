"""
Gaia DR3 adapter for COSMIC Data Fusion.

Implements BaseAdapter interface for Gaia DR3 catalog data ingestion.
Handles CSV and FITS file formats, validates Gaia-specific fields,
and transforms data to the unified schema.

IMPORTANT LICENSING NOTE:
Gaia data provided by ESA under the Gaia Archive terms.
See: https://gea.esac.esa.int/archive/
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from io import StringIO

from sqlalchemy.orm import Session

from app.services.adapters.base_adapter import BaseAdapter, ValidationResult
from app.services.utils.unit_converter import UnitConverter

logger = logging.getLogger(__name__)


class GaiaAdapter(BaseAdapter):
    """
    Adapter for ingesting Gaia DR3 catalog data.
    
    Supports:
    - CSV file parsing
    - FITS file parsing (future)
    - Coordinate validation (ICRS)
    - Parallax to distance conversion
    - Metadata enrichment
    
    Gaia DR3 Specifics:
    - Coordinates are already in ICRS J2000
    - Reference epoch is J2016.0
    - G-band magnitude (phot_g_mean_mag)
    - Optional parallax for distance calculation
    """
    
    # Required Gaia columns
    REQUIRED_COLUMNS = ["source_id", "ra", "dec", "phot_g_mean_mag"]
    
    # Optional columns we can use
    OPTIONAL_COLUMNS = ["parallax", "ref_epoch", "pmra", "pmdec"]
    
    # Column mapping: Gaia column -> internal name
    COLUMN_MAPPING = {
        "source_id": "source_id",
        "ra": "ra",
        "dec": "dec",
        "phot_g_mean_mag": "brightness_mag",
        "parallax": "parallax",
        "ref_epoch": "ref_epoch",
        "pmra": "pmra",
        "pmdec": "pmdec",
    }
    
    def __init__(
        self,
        db: Optional[Session] = None,
        error_reporter=None,
        dataset_id: Optional[str] = None,
        apply_parallax_correction: bool = False,
    ):
        """Initialize Gaia adapter.

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
            source_name="Gaia DR3",
            dataset_id=dataset_value,
            db=db_session,
            error_reporter=error_reporter,
        )
        self.apply_parallax_correction = apply_parallax_correction
        
        if apply_parallax_correction:
            logger.warning(
                "Parallax correction requested but not yet implemented. "
                "Using raw parallax values."
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
        # Handle different input types
        if isinstance(input_data, list):
            # Already parsed
            return input_data
        
        if isinstance(input_data, (str, Path)):
            # File path
            return self._parse_csv_file(input_data, **kwargs)
        
        if hasattr(input_data, 'read'):
            # File-like object
            return self._parse_csv_filelike(input_data, **kwargs)
        
        raise ValueError(
            f"Unsupported input type: {type(input_data)}. "
            "Expected file path, file-like object, or list of dicts."
        )
    
    def _parse_csv_file(self, file_path: Union[str, Path], **kwargs) -> List[Dict[str, Any]]:
        """
        Parse CSV file from disk.
        
        Args:
            file_path: Path to CSV file
            **kwargs: encoding, etc.
            
        Returns:
            List of record dictionaries
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")
        
        encoding = kwargs.get('encoding', 'utf-8')
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return self._parse_csv_filelike(f, **kwargs)
        except Exception as e:
            raise ValueError(f"Failed to read CSV file: {e}")
    
    def _parse_csv_filelike(self, file_obj, **kwargs) -> List[Dict[str, Any]]:
        """
        Parse CSV from file-like object.
        
        Args:
            file_obj: File-like object with read() method
            **kwargs: Additional options
            
        Returns:
            List of record dictionaries
        """
        records = []
        
        try:
            # Read content
            if hasattr(file_obj, 'seek'):
                file_obj.seek(0)
            
            content = file_obj.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            
            # Filter out comment lines
            lines = []
            for line in content.split('\n'):
                line_stripped = line.strip()
                if line_stripped and not line_stripped.startswith('#'):
                    lines.append(line)
            
            # Parse CSV
            csv_content = '\n'.join(lines)
            reader = csv.DictReader(StringIO(csv_content))
            
            for row_num, row in enumerate(reader, start=1):
                # Clean keys and values (remove whitespace)
                cleaned_row = {k.strip(): v.strip() for k, v in row.items()}
                
                # Add row number for debugging
                cleaned_row['_row_num'] = row_num
                
                records.append(cleaned_row)
            
            self.logger.info(f"Parsed {len(records)} records from CSV")
            return records
            
        except Exception as e:
            raise ValueError(f"Failed to parse CSV: {e}")
    
    def validate(self, record: Dict[str, Any]) -> ValidationResult:
        """
        Validate a single Gaia record.
        
        Checks:
        - Required fields present
        - Coordinate ranges valid
        - Magnitude reasonable
        - Parallax valid (if present)
        
        Args:
            record: Raw record dictionary
            
        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult()
        row_num = record.get('_row_num', 'unknown')
        
        # Check required fields
        for field in self.REQUIRED_COLUMNS:
            if field not in record or not record[field]:
                result.add_error(f"Row {row_num}: Missing required field '{field}'")
        
        # If we have errors, don't bother with range checks
        if not result.is_valid:
            return result
        
        # Validate RA
        try:
            ra = float(record['ra'])
            if not (0 <= ra < 360):
                result.add_error(f"Row {row_num}: RA out of range [0, 360): {ra}")
        except (ValueError, TypeError) as e:
            result.add_error(f"Row {row_num}: Invalid RA value: {record['ra']}")
        
        # Validate Dec
        try:
            dec = float(record['dec'])
            if not (-90 <= dec <= 90):
                result.add_error(f"Row {row_num}: Dec out of range [-90, 90]: {dec}")
            
            # Warn for near-pole objects (might have coordinate issues)
            if abs(dec) > 85:
                result.add_warning(
                    f"Row {row_num}: Near-pole object (dec={dec:.2f}°), "
                    "verify coordinate precision"
                )
        except (ValueError, TypeError) as e:
            result.add_error(f"Row {row_num}: Invalid Dec value: {record['dec']}")
        
        # Validate magnitude
        try:
            mag = float(record['phot_g_mean_mag'])
            
            # Gaia typical range: -2 to +21 mag
            if mag < -2 or mag > 21:
                result.add_warning(
                    f"Row {row_num}: Magnitude outside typical range [-2, 21]: {mag:.2f}"
                )
            
            # Flag suspicious zero magnitude
            if mag == 0:
                result.add_warning(
                    f"Row {row_num}: Magnitude exactly 0.0, likely bad data"
                )
        except (ValueError, TypeError) as e:
            result.add_error(f"Row {row_num}: Invalid magnitude value: {record['phot_g_mean_mag']}")
        
        # Validate parallax (if present)
        if 'parallax' in record and record['parallax']:
            try:
                parallax = float(record['parallax'])
                
                # Negative parallax is physically meaningless but can occur due to noise
                if parallax <= 0:
                    result.add_warning(
                        f"Row {row_num}: Non-positive parallax ({parallax:.3f} mas), "
                        "cannot compute distance"
                    )
                
                # Very large parallax (very nearby) - sanity check
                if parallax > 1000:
                    result.add_warning(
                        f"Row {row_num}: Very large parallax ({parallax:.3f} mas), "
                        "distance < 1 pc - verify data"
                    )
                
                # Very small parallax (very distant)
                if 0 < parallax < 0.1:
                    result.add_warning(
                        f"Row {row_num}: Very small parallax ({parallax:.3f} mas), "
                        "distance > 10 kpc, high uncertainty expected"
                    )
            except (ValueError, TypeError) as e:
                result.add_warning(f"Row {row_num}: Invalid parallax value: {record['parallax']}")
        
        return result
    
    def map_to_unified_schema(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map Gaia record to unified schema.
        
        Args:
            record: Validated raw record
            
        Returns:
            Dictionary with unified schema fields
        """
        # Extract and convert values
        source_id = str(record['source_id'])
        ra = float(record['ra'])
        dec = float(record['dec'])
        magnitude = float(record['phot_g_mean_mag'])
        
        # Optional parallax and distance
        parallax_mas = None
        distance_pc = None
        
        if 'parallax' in record and record['parallax']:
            try:
                parallax_mas = float(record['parallax'])
                if parallax_mas > 0:
                    distance_pc = UnitConverter.parallax_to_distance(parallax_mas)
            except (ValueError, TypeError):
                pass
        
        # Convert reference epoch to datetime
        observation_time = None
        if 'ref_epoch' in record and record['ref_epoch']:
            try:
                ref_epoch = float(record['ref_epoch'])
                observation_time = self._epoch_to_datetime(ref_epoch)
            except (ValueError, TypeError):
                pass
        
        # Build raw metadata for extra fields
        raw_metadata = {}
        for field in ['pmra', 'pmdec', 'ref_epoch']:
            if field in record and record[field]:
                raw_metadata[field] = record[field]
        
        # Return unified schema
        return {
            'object_id': f"gaia_dr3_{source_id}",
            'source_id': source_id,
            'ra_deg': ra,
            'dec_deg': dec,
            'brightness_mag': magnitude,
            'parallax_mas': parallax_mas,
            'distance_pc': distance_pc,
            'original_source': self.source_name,
            'raw_frame': 'ICRS',  # Gaia is already ICRS J2000
            'observation_time': observation_time,
            'dataset_id': self.dataset_id,
            'raw_metadata': raw_metadata if raw_metadata else None,
        }
    
    def _epoch_to_datetime(self, epoch: float) -> datetime:
        """
        Convert decimal year epoch to datetime.
        
        Args:
            epoch: Decimal year (e.g., 2016.0, 2016.5)
            
        Returns:
            datetime object
        """
        year = int(epoch)
        remainder = epoch - year
        
        # Calculate day of year
        year_start = datetime(year, 1, 1)
        year_end = datetime(year + 1, 1, 1)
        year_duration = (year_end - year_start).total_seconds()
        
        seconds_into_year = remainder * year_duration
        
        return year_start + timedelta(seconds=seconds_into_year)
    
    def get_column_mapping(self) -> Dict[str, str]:
        """
        Get column mapping for this adapter.
        
        Returns:
            Dictionary mapping Gaia columns to unified fields
        """
        return self.COLUMN_MAPPING.copy()

    def get_catalog_type(self) -> str:
        return "gaia"

    def get_source_type(self) -> str:
        return "Gaia DR3"

    def get_license_info(self) -> Optional[str]:
        return "ESA/Gaia DPAC"

    def _get_raw_config(self) -> Optional[dict]:
        return {"apply_parallax_correction": self.apply_parallax_correction}


# Import timedelta for epoch conversion
from datetime import timedelta
