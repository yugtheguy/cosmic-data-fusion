"""
Generic CSV ingestion service for COSMIC Data Fusion.

Provides reusable CSV parsing utilities that can be extended
for specific data sources (Gaia, 2MASS, etc.).

This module handles:
- Safe CSV file reading
- Column validation
- Data type conversion
- Error handling for malformed data
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)


class CSVIngestionError(Exception):
    """Exception raised for CSV ingestion errors."""
    pass


class CSVIngestionService:
    """
    Generic CSV file parser with validation and transformation support.
    
    Designed to be extended or configured for specific astronomical
    catalog formats while keeping common parsing logic centralized.
    """
    
    def __init__(
        self,
        required_columns: List[str],
        column_mapping: Optional[Dict[str, str]] = None,
        type_converters: Optional[Dict[str, Callable]] = None
    ):
        """
        Initialize CSV ingestion service.
        
        Args:
            required_columns: List of column names that must be present
            column_mapping: Optional dict mapping source columns to target names
            type_converters: Optional dict mapping column names to converter functions
        """
        self.required_columns = required_columns
        self.column_mapping = column_mapping or {}
        self.type_converters = type_converters or {}
    
    def validate_columns(self, header: List[str]) -> None:
        """
        Validate that all required columns are present.
        
        Args:
            header: List of column names from CSV header
            
        Raises:
            CSVIngestionError: If required columns are missing
        """
        missing = set(self.required_columns) - set(header)
        if missing:
            raise CSVIngestionError(
                f"Missing required columns: {', '.join(sorted(missing))}"
            )
    
    def convert_value(self, column: str, value: str) -> Any:
        """
        Convert a string value using the appropriate converter.
        
        Args:
            column: Column name
            value: String value from CSV
            
        Returns:
            Converted value
            
        Raises:
            CSVIngestionError: If conversion fails
        """
        if column in self.type_converters:
            try:
                return self.type_converters[column](value)
            except (ValueError, TypeError) as e:
                raise CSVIngestionError(
                    f"Failed to convert column '{column}' value '{value}': {e}"
                )
        return value
    
    def map_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        """
        Map and convert a single CSV row.
        
        Args:
            row: Dictionary from csv.DictReader
            
        Returns:
            Mapped and converted dictionary
        """
        result = {}
        
        for source_col, value in row.items():
            # Apply column mapping if defined
            target_col = self.column_mapping.get(source_col, source_col)
            
            # Convert value type
            converted = self.convert_value(source_col, value)
            result[target_col] = converted
        
        return result
    
    def read_csv(
        self,
        file_path: Path,
        skip_errors: bool = False,
        max_rows: Optional[int] = None
    ) -> tuple[List[Dict[str, Any]], List[tuple[int, str]]]:
        """
        Read and parse a CSV file.
        
        Args:
            file_path: Path to the CSV file
            skip_errors: If True, skip rows with errors instead of raising
            max_rows: Maximum number of rows to read (None = all)
            
        Returns:
            Tuple of (parsed_rows, errors) where errors is list of (row_num, message)
            
        Raises:
            CSVIngestionError: If file cannot be read or has invalid structure
        """
        if not file_path.exists():
            raise CSVIngestionError(f"CSV file not found: {file_path}")
        
        parsed_rows: List[Dict[str, Any]] = []
        errors: List[tuple[int, str]] = []
        
        logger.info(f"Reading CSV file: {file_path}")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                # Skip comment lines at the start of the file
                lines = []
                for line in f:
                    if not line.strip().startswith("#"):
                        lines.append(line)
                
                # Parse CSV from non-comment lines
                reader = csv.DictReader(lines)
                
                # Validate header
                if reader.fieldnames is None:
                    raise CSVIngestionError("CSV file has no header row")
                
                self.validate_columns(list(reader.fieldnames))
                
                # Process rows
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is 1)
                    if max_rows is not None and len(parsed_rows) >= max_rows:
                        logger.info(f"Reached max_rows limit: {max_rows}")
                        break
                    
                    try:
                        mapped_row = self.map_row(row)
                        parsed_rows.append(mapped_row)
                    except CSVIngestionError as e:
                        if skip_errors:
                            errors.append((row_num, str(e)))
                            logger.warning(f"Row {row_num}: {e}")
                        else:
                            raise CSVIngestionError(f"Row {row_num}: {e}")
        
        except UnicodeDecodeError as e:
            raise CSVIngestionError(f"File encoding error: {e}")
        except csv.Error as e:
            raise CSVIngestionError(f"CSV parsing error: {e}")
        
        logger.info(
            f"CSV parsing complete: {len(parsed_rows)} rows parsed, "
            f"{len(errors)} errors"
        )
        
        return parsed_rows, errors


def safe_float(value: str) -> float:
    """
    Safely convert a string to float, handling various formats.
    
    Handles:
    - Standard floats: "123.456"
    - Negative with special minus: "−28.9" (Unicode minus)
    - Scientific notation: "1.23e-4"
    
    Args:
        value: String representation of a float
        
    Returns:
        Float value
        
    Raises:
        ValueError: If conversion fails
    """
    # Replace Unicode minus sign with standard ASCII minus
    # Gaia data sometimes uses Unicode minus (U+2212) instead of ASCII minus (U+002D)
    cleaned = value.strip().replace("−", "-").replace("–", "-")
    return float(cleaned)


def safe_int(value: str) -> int:
    """
    Safely convert a string to integer.
    
    Args:
        value: String representation of an integer
        
    Returns:
        Integer value
    """
    return int(value.strip())


def safe_string(value: str) -> str:
    """
    Clean and return a string value.
    
    Args:
        value: Input string
        
    Returns:
        Cleaned string
    """
    return value.strip()
