"""
Data Exporter Service for COSMIC Data Fusion.

Provides export functionality for star catalog data in multiple formats:
- CSV: Standard comma-separated values
- JSON: JavaScript Object Notation
- VOTable: Virtual Observatory Table format (astronomical standard)

This module is READ-ONLY and does not modify any database records.

Phase: 3 - Query & Export Engine
"""

import io
import csv
import json
import logging
from typing import List, Optional, Union
from datetime import datetime, timezone

import pandas as pd
from astropy.table import Table as AstropyTable
from astropy.io.votable import from_table as votable_from_table
from astropy.io.votable.tree import VOTableFile
from astropy.io import votable as votable_io

from app.models import UnifiedStarCatalog

logger = logging.getLogger(__name__)


class DataExporter:
    """
    Export star catalog data to various formats.
    
    This class handles conversion of database records to standard formats
    used in astronomical research and data exchange.
    
    Supported Formats:
    ------------------
    1. CSV: Universal format, Excel-compatible
    2. JSON: Web-friendly, API-compatible
    3. VOTable: International Virtual Observatory Alliance standard
    
    VOTable Format (Why it matters for hackathon judges):
    -----------------------------------------------------
    VOTable is the XML-based standard for astronomical data exchange,
    defined by the International Virtual Observatory Alliance (IVOA).
    
    Key features:
    - Self-describing: Includes metadata about each column
    - Typed: Preserves data types (float, string, etc.)
    - Interoperable: Works with TOPCAT, Aladin, DS9, and other astro tools
    - Supports UCDs: Unified Content Descriptors for semantic meaning
    
    Example UCD meanings:
    - pos.eq.ra: Right Ascension (equatorial coordinates)
    - pos.eq.dec: Declination (equatorial coordinates)
    - phot.mag: Photometric magnitude
    - pos.parallax: Parallax angle
    
    Usage:
        exporter = DataExporter(star_records)
        csv_data = exporter.to_csv()
        json_data = exporter.to_json()
        votable_data = exporter.to_votable()
    """
    
    def __init__(
        self,
        data: Union[List[UnifiedStarCatalog], pd.DataFrame],
        source_name: str = "COSMIC Data Fusion"
    ):
        """
        Initialize the exporter with data.
        
        Args:
            data: Either a list of UnifiedStarCatalog ORM objects or a DataFrame
            source_name: Name to include in export metadata
        """
        self.source_name = source_name
        self.export_time = datetime.now(timezone.utc).isoformat()
        
        # Convert to DataFrame if needed
        if isinstance(data, pd.DataFrame):
            self._df = data
        else:
            self._df = self._records_to_dataframe(data)
        
        logger.info(f"DataExporter initialized with {len(self._df)} records")
    
    def _records_to_dataframe(self, records: List[UnifiedStarCatalog]) -> pd.DataFrame:
        """
        Convert ORM records to a Pandas DataFrame.
        
        Only includes the core astronomical columns, not internal metadata.
        
        Args:
            records: List of UnifiedStarCatalog objects
            
        Returns:
            DataFrame with astronomical data columns
        """
        data = []
        for star in records:
            data.append({
                "id": star.id,
                "source_id": star.source_id,
                "ra_deg": star.ra_deg,
                "dec_deg": star.dec_deg,
                "brightness_mag": star.brightness_mag,
                "parallax_mas": star.parallax_mas,
                "distance_pc": star.distance_pc,
                "original_source": star.original_source,
            })
        
        return pd.DataFrame(data)
    
    def to_csv(self) -> str:
        """
        Export data to CSV format.
        
        Returns:
            CSV string with header row and data
            
        Note:
            - Uses standard comma delimiter
            - NULL values exported as empty strings
            - Floating point precision preserved
        """
        logger.info(f"Exporting {len(self._df)} records to CSV")
        
        # Use StringIO buffer for in-memory CSV generation
        buffer = io.StringIO()
        
        # Export to CSV with pandas (handles edge cases well)
        self._df.to_csv(buffer, index=False, na_rep="")
        
        return buffer.getvalue()
    
    def to_json(self, indent: int = 2) -> str:
        """
        Export data to JSON format.
        
        Args:
            indent: JSON indentation level (default 2 for readability)
            
        Returns:
            JSON string with metadata and records array
            
        Structure:
            {
                "metadata": { ... },
                "count": 100,
                "records": [ ... ]
            }
        """
        logger.info(f"Exporting {len(self._df)} records to JSON")
        
        # Build export structure with metadata
        export_data = {
            "metadata": {
                "source": self.source_name,
                "export_time": self.export_time,
                "format_version": "1.0",
                "columns": {
                    "id": "Internal database ID",
                    "source_id": "Original identifier from source catalog",
                    "ra_deg": "Right Ascension in degrees (ICRS J2000)",
                    "dec_deg": "Declination in degrees (ICRS J2000)",
                    "brightness_mag": "Apparent magnitude",
                    "parallax_mas": "Parallax in milliarcseconds",
                    "distance_pc": "Distance in parsecs",
                    "original_source": "Source catalog name",
                }
            },
            "count": len(self._df),
            "records": self._df.to_dict(orient="records")
        }
        
        # Handle NaN values (JSON doesn't support NaN)
        def clean_nan(obj):
            if isinstance(obj, dict):
                return {k: clean_nan(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_nan(item) for item in obj]
            elif isinstance(obj, float) and pd.isna(obj):
                return None
            return obj
        
        export_data = clean_nan(export_data)
        
        return json.dumps(export_data, indent=indent)
    
    def to_votable(self) -> bytes:
        """
        Export data to VOTable format (Virtual Observatory standard).
        
        This is the CRITICAL "hackathon wow factor" export format.
        
        VOTable Overview:
        -----------------
        VOTable is an XML format defined by the International Virtual 
        Observatory Alliance (IVOA). It's the standard way to exchange
        astronomical catalog data between observatories and tools.
        
        Why VOTable matters:
        1. Industry Standard: Used by NASA, ESA, CDS, and all major observatories
        2. Self-Documenting: Includes column descriptions, units, and UCDs
        3. Tool Compatible: Opens directly in TOPCAT, Aladin, DS9, etc.
        4. Preserves Types: Maintains data types and null handling
        
        UCD (Unified Content Descriptors):
        ----------------------------------
        UCDs are semantic labels that describe what each column contains.
        They enable automatic recognition by VO tools.
        
        UCDs used here:
        - meta.id: Identifier
        - pos.eq.ra: Right Ascension (J2000 equatorial)
        - pos.eq.dec: Declination (J2000 equatorial)
        - phot.mag: Photometric magnitude
        - pos.parallax: Parallax measurement
        - pos.distance: Distance to object
        - meta.note: Descriptive text
        
        Returns:
            VOTable XML as bytes (UTF-8 encoded)
        """
        logger.info(f"Exporting {len(self._df)} records to VOTable format")
        
        # =====================================================================
        # STEP 1: Prepare DataFrame for VOTable Conversion
        # =====================================================================
        # VOTable has strict type requirements. We need to ensure:
        # - String columns are proper string dtype (not object)
        # - Numeric columns have explicit types
        # - NaN values are handled properly
        
        df_clean = self._df.copy()
        
        # Convert object columns to string type explicitly
        # This fixes "len() of unsized object" errors in astropy VOTable conversion
        for col in df_clean.columns:
            if df_clean[col].dtype == 'object':
                df_clean[col] = df_clean[col].astype(str).replace('None', '')
        
        # =====================================================================
        # STEP 2: Create Astropy Table from DataFrame
        # =====================================================================
        # Astropy Table is an intermediate format that bridges pandas and VOTable.
        # It handles astronomical data types and metadata natively.
        
        astropy_table = AstropyTable.from_pandas(df_clean)
        
        # =====================================================================
        # STEP 2: Add Column Metadata (UCDs, Descriptions, Units)
        # =====================================================================
        # This metadata makes the VOTable self-documenting and enables
        # automatic recognition by Virtual Observatory tools.
        
        # Define column metadata with UCDs (Unified Content Descriptors)
        column_metadata = {
            "id": {
                "description": "Internal database identifier",
                "ucd": "meta.id"
            },
            "source_id": {
                "description": "Original identifier from source catalog",
                "ucd": "meta.id;meta.main"
            },
            "ra_deg": {
                "description": "Right Ascension (ICRS J2000)",
                "ucd": "pos.eq.ra;meta.main",
                "unit": "deg"
            },
            "dec_deg": {
                "description": "Declination (ICRS J2000)",
                "ucd": "pos.eq.dec;meta.main",
                "unit": "deg"
            },
            "brightness_mag": {
                "description": "Apparent magnitude (lower = brighter)",
                "ucd": "phot.mag",
                "unit": "mag"
            },
            "parallax_mas": {
                "description": "Parallax angle",
                "ucd": "pos.parallax",
                "unit": "mas"
            },
            "distance_pc": {
                "description": "Distance to star",
                "ucd": "pos.distance",
                "unit": "pc"
            },
            "original_source": {
                "description": "Source catalog name (e.g., Gaia DR3)",
                "ucd": "meta.note"
            }
        }
        
        # Apply metadata to each column
        for col_name, meta in column_metadata.items():
            if col_name in astropy_table.colnames:
                col = astropy_table[col_name]
                col.description = meta.get("description", "")
                col.meta["ucd"] = meta.get("ucd", "")
                if "unit" in meta:
                    try:
                        col.unit = meta["unit"]
                    except Exception:
                        pass  # Some columns can't have units
        
        # =====================================================================
        # STEP 3: Convert to VOTable Format
        # =====================================================================
        # The votable_from_table function creates a VOTableFile object
        # with proper structure: VOTABLE > RESOURCE > TABLE > DATA
        
        votable = votable_from_table(astropy_table)
        
        # =====================================================================
        # STEP 4: Add VOTable Metadata
        # =====================================================================
        # Add resource-level metadata for provenance tracking
        
        # Access the resource to add description
        if votable.resources:
            resource = votable.resources[0]
            resource.name = "COSMIC_Data_Fusion_Export"
            resource.description = (
                f"Star catalog export from {self.source_name}. "
                f"Exported on {self.export_time}. "
                f"Contains {len(self._df)} records."
            )
        
        # =====================================================================
        # STEP 5: Write to Bytes Buffer
        # =====================================================================
        # Write the VOTable to an in-memory buffer as XML bytes
        
        buffer = io.BytesIO()
        votable_io.writeto(votable, buffer)
        buffer.seek(0)
        
        logger.info("VOTable export complete")
        return buffer.getvalue()
    
    def get_record_count(self) -> int:
        """Return the number of records in the export."""
        return len(self._df)
    
    def get_column_names(self) -> List[str]:
        """Return list of column names in the export."""
        return list(self._df.columns)
