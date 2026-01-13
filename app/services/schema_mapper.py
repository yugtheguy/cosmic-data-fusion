"""
Schema Mapper Service for automatic column detection and mapping.

This service analyzes astronomical data files (CSV, FITS, etc.) to automatically
detect and map columns to the unified schema (ra, dec, parallax, magnitude, etc.).
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
from pathlib import Path


class StandardColumn(str, Enum):
    """Standard column names in the unified schema."""
    RA = "ra"
    DEC = "dec"
    PARALLAX = "parallax"
    PMRA = "pmra"
    PMDEC = "pmdec"
    MAGNITUDE = "magnitude"
    SOURCE_ID = "source_id"


class ConfidenceLevel(str, Enum):
    """Confidence levels for column mapping suggestions."""
    HIGH = "high"      # >= 0.90
    MEDIUM = "medium"  # 0.75 - 0.89
    LOW = "low"        # < 0.75


@dataclass
class ColumnSuggestion:
    """Represents a column mapping suggestion with confidence."""
    source_column: str
    target_column: StandardColumn
    confidence: float
    confidence_level: ConfidenceLevel
    reason: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "source_column": self.source_column,
            "target_column": self.target_column.value,
            "confidence": round(self.confidence, 2),
            "confidence_level": self.confidence_level.value,
            "reason": self.reason
        }


@dataclass
class MappingSuggestion:
    """Complete mapping suggestion for a dataset."""
    mappings: Dict[str, StandardColumn]  # source_column -> target_column
    suggestions: List[ColumnSuggestion]
    unmapped_columns: List[str]
    warnings: List[str]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "mappings": {k: v.value for k, v in self.mappings.items()},
            "suggestions": [s.to_dict() for s in self.suggestions],
            "unmapped_columns": self.unmapped_columns,
            "warnings": self.warnings
        }


class SchemaMapper:
    """
    Service for automatic schema detection and mapping.
    
    Provides methods to:
    - Suggest mappings from column headers
    - Analyze sample data for better detection
    - Generate preview of mapping results
    - Apply and persist mappings to datasets
    """
    
    # Column name variants for detection (from adapter heuristics)
    RA_VARIANTS = [
        'ra', 'ra_icrs', 'raj2000', 'ra2000', 'ra_deg', 'radeg',
        'right_ascension', 'rightascension', 'alpha', 'ra_j2000'
    ]
    
    DEC_VARIANTS = [
        'dec', 'de', 'decj2000', 'dec2000', 'dec_deg', 'decdeg',
        'declination', 'delta', 'dec_j2000', 'de_icrs'
    ]
    
    PARALLAX_VARIANTS = [
        'parallax', 'plx', 'par', 'parallax_mas'
    ]
    
    PMRA_VARIANTS = [
        'pmra', 'pm_ra', 'mu_ra', 'mura', 'pmra_cosdec', 'proper_motion_ra'
    ]
    
    PMDEC_VARIANTS = [
        'pmdec', 'pm_dec', 'mu_dec', 'mudec', 'proper_motion_dec'
    ]
    
    MAGNITUDE_VARIANTS = [
        'magnitude', 'mag', 'phot_g_mean_mag', 'g_mag', 'gmag',
        'v_mag', 'vmag', 'u', 'g', 'r', 'i', 'z'
    ]
    
    SOURCE_ID_VARIANTS = [
        'source_id', 'sourceid', 'id', 'star_id', 'object_id', 'designation'
    ]
    
    # Mapping of standard columns to their variants
    COLUMN_VARIANTS = {
        StandardColumn.RA: RA_VARIANTS,
        StandardColumn.DEC: DEC_VARIANTS,
        StandardColumn.PARALLAX: PARALLAX_VARIANTS,
        StandardColumn.PMRA: PMRA_VARIANTS,
        StandardColumn.PMDEC: PMDEC_VARIANTS,
        StandardColumn.MAGNITUDE: MAGNITUDE_VARIANTS,
        StandardColumn.SOURCE_ID: SOURCE_ID_VARIANTS,
    }
    
    def __init__(self):
        """Initialize the schema mapper."""
        pass
    
    def suggest_from_header(
        self,
        columns: List[str],
        existing_mapping: Optional[Dict[str, str]] = None
    ) -> MappingSuggestion:
        """
        Suggest column mappings based on column headers.
        
        Args:
            columns: List of column names from the source file
            existing_mapping: Optional existing mapping to preserve
            
        Returns:
            MappingSuggestion with detected mappings and confidence scores
        """
        mappings = {}
        suggestions = []
        unmapped_columns = []
        warnings = []
        used_targets = set()  # Track which target columns are already mapped
        
        # First, preserve any existing mappings
        if existing_mapping:
            for source_col, target_col in existing_mapping.items():
                if source_col in columns:
                    try:
                        target_enum = StandardColumn(target_col)
                        mappings[source_col] = target_enum
                        used_targets.add(target_enum)
                        suggestions.append(ColumnSuggestion(
                            source_column=source_col,
                            target_column=target_enum,
                            confidence=1.0,
                            confidence_level=ConfidenceLevel.HIGH,
                            reason="User-provided mapping (preserved)"
                        ))
                    except ValueError:
                        warnings.append(f"Invalid target column in existing mapping: {target_col}")
        
        # Process each source column
        for source_column in columns:
            # Skip if already mapped
            if source_column in mappings:
                continue
            
            source_lower = source_column.lower().strip()
            best_match = None
            best_confidence = 0.0
            best_reason = ""
            
            # Try to find best match among standard columns
            for target_col in StandardColumn:
                # Skip if this target is already used
                if target_col in used_targets:
                    continue
                
                # Check for exact match
                if source_lower == target_col.value:
                    confidence, reason = self._calculate_confidence(
                        source_column, target_col, "exact"
                    )
                    if confidence > best_confidence:
                        best_match = target_col
                        best_confidence = confidence
                        best_reason = reason
                    continue
                
                # Check variants
                variants = self.COLUMN_VARIANTS.get(target_col, [])
                if source_lower in variants:
                    confidence, reason = self._calculate_confidence(
                        source_column, target_col, "variant"
                    )
                    if confidence > best_confidence:
                        best_match = target_col
                        best_confidence = confidence
                        best_reason = reason
                    continue
                
                # Check for partial matches (substring)
                for variant in variants:
                    if variant in source_lower or source_lower in variant:
                        confidence, reason = self._calculate_confidence(
                            source_column, target_col, "partial"
                        )
                        if confidence > best_confidence:
                            best_match = target_col
                            best_confidence = confidence
                            best_reason = reason
                        break
            
            # If we found a reasonable match, add it
            if best_match and best_confidence >= 0.50:
                mappings[source_column] = best_match
                used_targets.add(best_match)
                confidence_level = self._get_confidence_level(best_confidence)
                
                suggestion = ColumnSuggestion(
                    source_column=source_column,
                    target_column=best_match,
                    confidence=best_confidence,
                    confidence_level=confidence_level,
                    reason=best_reason
                )
                suggestions.append(suggestion)
                
                # Warn if confidence is low
                if confidence_level == ConfidenceLevel.LOW:
                    warnings.append(
                        f"Low confidence ({best_confidence:.2f}) for mapping "
                        f"'{source_column}' -> '{best_match.value}'. Please verify."
                    )
            else:
                # No good match found
                unmapped_columns.append(source_column)
        
        # Check for missing critical columns
        if StandardColumn.RA not in used_targets:
            warnings.append("No RA (Right Ascension) column detected. This is required for ingestion.")
        if StandardColumn.DEC not in used_targets:
            warnings.append("No Dec (Declination) column detected. This is required for ingestion.")
        
        return MappingSuggestion(
            mappings=mappings,
            suggestions=suggestions,
            unmapped_columns=unmapped_columns,
            warnings=warnings
        )
    
    def suggest_from_sample_rows(
        self,
        df: pd.DataFrame,
        existing_mapping: Optional[Dict[str, str]] = None
    ) -> MappingSuggestion:
        """
        Suggest column mappings by analyzing sample data rows.
        
        Args:
            df: DataFrame with sample rows from the source file
            existing_mapping: Optional existing mapping to preserve
            
        Returns:
            MappingSuggestion with detected mappings including value-based analysis
        """
        # Start with header-based suggestions
        header_suggestion = self.suggest_from_header(
            columns=df.columns.tolist(),
            existing_mapping=existing_mapping
        )
        
        # Enhance with sample-based analysis
        mappings = dict(header_suggestion.mappings)
        suggestions = list(header_suggestion.suggestions)
        unmapped_columns = list(header_suggestion.unmapped_columns)
        warnings = list(header_suggestion.warnings)
        
        # Analyze unmapped columns using value heuristics
        for col in unmapped_columns[:]:  # Iterate over copy
            try:
                # Skip non-numeric columns
                if not pd.api.types.is_numeric_dtype(df[col]):
                    continue
                
                # Get sample values (drop NaN)
                values = df[col].dropna()
                if len(values) == 0:
                    continue
                
                col_min = values.min()
                col_max = values.max()
                col_mean = values.mean()
                
                # Check if this looks like RA (0-360 range)
                if StandardColumn.RA not in mappings.values():
                    if 0 <= col_min and col_max <= 360 and col_mean > 90:
                        # Likely RA (increased mean threshold to avoid catching Dec)
                        mappings[col] = StandardColumn.RA
                        suggestions.append(ColumnSuggestion(
                            source_column=col,
                            target_column=StandardColumn.RA,
                            confidence=0.75,
                            confidence_level=ConfidenceLevel.MEDIUM,
                            reason=f"Numeric range ({col_min:.2f} to {col_max:.2f}) suggests RA in degrees"
                        ))
                        unmapped_columns.remove(col)
                        warnings.append(
                            f"Column '{col}' detected as RA based on value range. "
                            "Please verify this is correct."
                        )
                        continue
                
                # Check if this looks like Dec (-90 to 90 range)
                if StandardColumn.DEC not in mappings.values():
                    if -90 <= col_min and col_max <= 90:
                        # Likely Dec (removed mean constraint as it's too restrictive)
                        mappings[col] = StandardColumn.DEC
                        suggestions.append(ColumnSuggestion(
                            source_column=col,
                            target_column=StandardColumn.DEC,
                            confidence=0.75,
                            confidence_level=ConfidenceLevel.MEDIUM,
                            reason=f"Numeric range ({col_min:.2f} to {col_max:.2f}) suggests Dec in degrees"
                        ))
                        unmapped_columns.remove(col)
                        warnings.append(
                            f"Column '{col}' detected as Dec based on value range. "
                            "Please verify this is correct."
                        )
                        continue
                
                # Check if this looks like parallax (small positive values)
                if StandardColumn.PARALLAX not in mappings.values():
                    if 0 < col_min and col_max < 100 and col_mean < 10:
                        # Likely parallax in mas
                        mappings[col] = StandardColumn.PARALLAX
                        suggestions.append(ColumnSuggestion(
                            source_column=col,
                            target_column=StandardColumn.PARALLAX,
                            confidence=0.70,
                            confidence_level=ConfidenceLevel.LOW,
                            reason=f"Small positive values ({col_min:.2f} to {col_max:.2f}) suggest parallax"
                        ))
                        unmapped_columns.remove(col)
                        warnings.append(
                            f"Column '{col}' tentatively detected as parallax. "
                            "Low confidence - please verify."
                        )
                        continue
                
                # Check if this looks like magnitude (typically 0-30 range)
                if StandardColumn.MAGNITUDE not in mappings.values():
                    if -5 < col_min and col_max < 30:
                        # Likely magnitude
                        mappings[col] = StandardColumn.MAGNITUDE
                        suggestions.append(ColumnSuggestion(
                            source_column=col,
                            target_column=StandardColumn.MAGNITUDE,
                            confidence=0.70,
                            confidence_level=ConfidenceLevel.LOW,
                            reason=f"Value range ({col_min:.2f} to {col_max:.2f}) suggests magnitude"
                        ))
                        unmapped_columns.remove(col)
                        warnings.append(
                            f"Column '{col}' tentatively detected as magnitude. "
                            "Low confidence - please verify."
                        )
                        continue
                        
            except Exception as e:
                # Skip columns that cause errors
                warnings.append(f"Could not analyze column '{col}': {str(e)}")
                continue
        
        return MappingSuggestion(
            mappings=mappings,
            suggestions=suggestions,
            unmapped_columns=unmapped_columns,
            warnings=warnings
        )
    
    def preview_mapping_from_file(
        self,
        file_path: str,
        sample_size: int = 100
    ) -> MappingSuggestion:
        """
        Preview mapping suggestions for a file without ingesting it.
        
        Args:
            file_path: Path to the file to analyze
            sample_size: Number of rows to sample for analysis
            
        Returns:
            MappingSuggestion with complete mapping preview
        """
        path = Path(file_path)
        
        # Check file exists
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine file type and read sample
        file_extension = path.suffix.lower()
        
        try:
            if file_extension == '.csv':
                # Read CSV file (skip comment lines that start with #)
                df = pd.read_csv(file_path, nrows=sample_size, comment='#')
            elif file_extension in ['.fits', '.fit']:
                # Read FITS file
                from astropy.io import fits
                with fits.open(file_path) as hdul:
                    # Usually data is in first extension with data
                    for hdu in hdul:
                        if hasattr(hdu, 'data') and hdu.data is not None:
                            # Convert FITS table to DataFrame
                            data = hdu.data
                            if len(data) > 0:
                                # Take sample
                                sample_data = data[:sample_size] if len(data) > sample_size else data
                                df = pd.DataFrame(sample_data)
                                break
                    else:
                        raise ValueError("No data found in FITS file")
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            # Use sample-based detection
            return self.suggest_from_sample_rows(df)
            
        except Exception as e:
            raise RuntimeError(f"Failed to read file {file_path}: {str(e)}") from e
    
    def apply_mapping(
        self,
        dataset_id: str,
        mapping: Dict[str, str],
        confidence_threshold: float = 0.75
    ) -> bool:
        """
        Apply and persist a column mapping to a dataset.
        
        Args:
            dataset_id: UUID of the dataset
            mapping: Column mapping dictionary (source -> target)
            confidence_threshold: Minimum confidence to auto-apply
            
        Returns:
            True if mapping was applied successfully
        """
        # TODO: Implement persistence logic
        # This will be implemented in Stage 4
        raise NotImplementedError("apply_mapping will be implemented in Stage 4")
    
    def _calculate_confidence(
        self,
        source_column: str,
        target_column: StandardColumn,
        match_type: str
    ) -> Tuple[float, str]:
        """
        Calculate confidence score and reason for a column match.
        
        Args:
            source_column: Source column name
            target_column: Target standard column
            match_type: Type of match (exact, variant, heuristic, etc.)
            
        Returns:
            Tuple of (confidence_score, reason_string)
        """
        source_lower = source_column.lower().strip()
        
        if match_type == "exact":
            return (0.99, f"Exact match with standard column '{target_column.value}'")
        
        variants = self.COLUMN_VARIANTS.get(target_column, [])
        if source_lower in variants:
            # Higher confidence for earlier matches in variant list
            position = variants.index(source_lower)
            confidence = 0.95 - (position * 0.01)  # 0.95 for first, decreasing
            confidence = max(confidence, 0.85)  # Floor at 0.85
            return (confidence, f"Matches known variant '{source_lower}' for {target_column.value}")
        
        # Partial match
        for variant in variants:
            if variant in source_lower or source_lower in variant:
                return (0.75, f"Partial match with variant '{variant}' for {target_column.value}")
        
        return (0.50, f"Low confidence match for {target_column.value}")
    
    def _get_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Convert numeric confidence to confidence level."""
        if confidence >= 0.90:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.75:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
