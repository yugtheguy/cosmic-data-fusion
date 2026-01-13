"""
Adapter Registry Service

Centralized registry for managing and auto-detecting data source adapters.
Provides a unified interface for registering adapters, discovering available adapters,
and automatically detecting the appropriate adapter based on file characteristics.

Author: Cosmic Data Fusion Team
Date: January 2026
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Type, Tuple
from datetime import datetime, timezone

from .adapters.base_adapter import BaseAdapter
from .adapters.gaia_adapter import GaiaAdapter
from .adapters.sdss_adapter import SDSSAdapter
from .adapters.fits_adapter import FITSAdapter
from .adapters.csv_adapter import CSVAdapter

logger = logging.getLogger(__name__)


class AdapterDetectionError(Exception):
    """Raised when adapter detection fails or is ambiguous."""
    
    def __init__(self, message: str, file_path: str, detection_results: Optional[Dict] = None):
        self.message = message
        self.file_path = file_path
        self.detection_results = detection_results or {}
        super().__init__(self.message)


@dataclass
class AdapterInfo:
    """Information about a registered adapter."""
    name: str
    adapter_class: Type[BaseAdapter]
    file_patterns: List[str]
    description: str
    version: str
    
    def __post_init__(self):
        """Validate adapter info after initialization."""
        if not issubclass(self.adapter_class, BaseAdapter):
            raise ValueError(f"{self.adapter_class} must inherit from BaseAdapter")


class AdapterRegistry:
    """
    Registry for managing data source adapters.
    
    Provides functionality to:
    - Register new adapters
    - Retrieve adapters by name
    - List all available adapters
    - Auto-detect appropriate adapter based on file characteristics
    """
    
    def __init__(self):
        """Initialize an empty adapter registry."""
        self._adapters: Dict[str, AdapterInfo] = {}
        logger.info("AdapterRegistry initialized")
    
    def register(
        self,
        name: str,
        adapter_class: Type[BaseAdapter],
        file_patterns: List[str],
        description: str = "",
        version: str = "1.0.0"
    ) -> None:
        """
        Register a new adapter in the registry.
        
        Args:
            name: Unique identifier for the adapter
            adapter_class: The adapter class (must inherit from BaseAdapter)
            file_patterns: List of file patterns this adapter handles (e.g., ['*.csv', '*.tsv'])
            description: Human-readable description of the adapter
            version: Version string for the adapter
            
        Raises:
            ValueError: If adapter name already exists or adapter_class is invalid
        """
        if name in self._adapters:
            raise ValueError(f"Adapter '{name}' is already registered")
        
        adapter_info = AdapterInfo(
            name=name,
            adapter_class=adapter_class,
            file_patterns=file_patterns,
            description=description,
            version=version
        )
        
        self._adapters[name] = adapter_info
        logger.info(f"Registered adapter: {name} (version {version})")
    
    def get_adapter(self, name: str) -> Type[BaseAdapter]:
        """
        Retrieve an adapter class by name.
        
        Args:
            name: The unique identifier of the adapter
            
        Returns:
            The adapter class
            
        Raises:
            KeyError: If no adapter with the given name exists
        """
        if name not in self._adapters:
            raise KeyError(f"No adapter registered with name '{name}'")
        
        return self._adapters[name].adapter_class
    
    def list_adapters(self) -> List[AdapterInfo]:
        """
        List all registered adapters.
        
        Returns:
            List of AdapterInfo objects for all registered adapters
        """
        return list(self._adapters.values())
    
    def detect_adapter(
        self,
        file_path: str,
        confidence_threshold: float = 0.6
    ) -> Tuple[str, float, str]:
        """
        Auto-detect the appropriate adapter for a given file.
        
        Uses multiple detection strategies:
        1. Magic bytes (binary file headers) - highest confidence (0.99)
        2. File extension matching - high confidence (0.90-0.95)
        3. Content analysis (column names, data patterns) - medium confidence (0.75-0.80)
        
        Args:
            file_path: Path to the file to analyze
            confidence_threshold: Minimum confidence score required (0.0-1.0)
            
        Returns:
            Tuple of (adapter_name, confidence_score, detection_method)
            
        Raises:
            AdapterDetectionError: If detection fails or confidence is below threshold
            FileNotFoundError: If file doesn't exist
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        logger.info(f"Detecting adapter for file: {file_path}")
        
        # Try detection strategies in order of confidence
        detection_results = {}
        
        # Strategy 1: Magic bytes (highest confidence)
        magic_result = self._detect_by_magic_bytes(path)
        if magic_result:
            adapter_name, confidence = magic_result
            detection_results['magic_bytes'] = {'adapter': adapter_name, 'confidence': confidence}
            if confidence >= confidence_threshold:
                logger.info(f"Detected {adapter_name} via magic bytes (confidence: {confidence:.2f})")
                return adapter_name, confidence, 'magic_bytes'
        
        # Strategy 2: File extension (high confidence)
        extension_result = self._detect_by_extension(path)
        if extension_result:
            adapter_name, confidence = extension_result
            detection_results['extension'] = {'adapter': adapter_name, 'confidence': confidence}
            if confidence >= confidence_threshold:
                logger.info(f"Detected {adapter_name} via extension (confidence: {confidence:.2f})")
                return adapter_name, confidence, 'extension'
        
        # Strategy 3: Content analysis (medium confidence)
        content_result = self._detect_by_content_analysis(path)
        if content_result:
            adapter_name, confidence = content_result
            detection_results['content_analysis'] = {'adapter': adapter_name, 'confidence': confidence}
            if confidence >= confidence_threshold:
                logger.info(f"Detected {adapter_name} via content analysis (confidence: {confidence:.2f})")
                return adapter_name, confidence, 'content_analysis'
        
        # No detection met threshold
        raise AdapterDetectionError(
            f"Could not detect adapter with confidence >= {confidence_threshold}",
            file_path=file_path,
            detection_results=detection_results
        )
    
    def _detect_by_extension(self, path: Path) -> Optional[Tuple[str, float]]:
        """
        Detect adapter based on file extension.
        
        Returns:
            Tuple of (adapter_name, confidence) or None
        """
        extension = path.suffix.lower()
        
        # FITS files
        if extension in ['.fits', '.fit', '.fts']:
            return 'fits', 0.95
        
        # CSV/TSV files (but not .txt which is ambiguous)
        if extension in ['.csv', '.tsv']:
            return 'csv', 0.90
        
        # Gaia-specific naming patterns
        if 'gaia' in path.stem.lower() and extension in ['.csv', '.txt']:
            return 'gaia', 0.92
        
        # SDSS-specific naming patterns
        if 'sdss' in path.stem.lower() and extension in ['.csv', '.txt']:
            return 'sdss', 0.92
        
        return None
    
    def _detect_by_magic_bytes(self, path: Path) -> Optional[Tuple[str, float]]:
        """
        Detect adapter based on file magic bytes (binary headers).
        
        Returns:
            Tuple of (adapter_name, confidence) or None
        """
        try:
            with open(path, 'rb') as f:
                header = f.read(80)
            
            # FITS magic bytes: "SIMPLE  = " at start
            if header.startswith(b'SIMPLE  ='):
                return 'fits', 0.99
            
        except Exception as e:
            logger.debug(f"Error reading magic bytes: {e}")
        
        return None
    
    def _detect_by_content_analysis(self, path: Path) -> Optional[Tuple[str, float]]:
        """
        Detect adapter based on file content analysis (column names, data patterns).
        
        Returns:
            Tuple of (adapter_name, confidence) or None
        """
        try:
            # Read first few lines for text files
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                first_lines = [f.readline() for _ in range(10)]
            
            header = first_lines[0].lower() if first_lines else ""
            
            # Parse columns from header (split by common delimiters)
            columns = []
            for delimiter in [',', '\t', '|', ';']:
                if delimiter in header:
                    columns = [col.strip() for col in header.split(delimiter)]
                    break
            
            if not columns:
                return None
            
            # Gaia-specific columns (check first for higher priority)
            gaia_columns = ['source_id', 'ra', 'dec', 'parallax', 'pmra', 'pmdec']
            gaia_matches = sum(1 for col in gaia_columns if col in columns)
            if gaia_matches >= 3:
                return 'gaia', 0.80
            
            # SDSS-specific columns (check before generic CSV)
            # Must have at least 3 of the 5-band photometry columns as exact matches
            sdss_columns = ['objid', 'ra', 'dec', 'u', 'g', 'r', 'i', 'z']
            sdss_matches = sum(1 for col in sdss_columns if col in columns)
            if sdss_matches >= 4:
                return 'sdss', 0.80
            
            # Generic CSV if we have columns (higher priority than partial matches)
            if columns and len(columns) > 1:
                return 'csv', 0.75
            
        except Exception as e:
            logger.debug(f"Error analyzing content: {e}")
        
        return None


# Singleton registry instance
registry = AdapterRegistry()

# Pre-register built-in adapters
registry.register(
    name='gaia',
    adapter_class=GaiaAdapter,
    file_patterns=['*.csv', '*gaia*.csv', '*gaia*.tsv'],
    description='Gaia DR3 catalog adapter with astrometric data support',
    version='1.0.0'
)

registry.register(
    name='sdss',
    adapter_class=SDSSAdapter,
    file_patterns=['*.csv', '*sdss*.csv', '*dr17*.csv'],
    description='SDSS DR17 spectroscopic survey adapter with 5-band photometry',
    version='1.0.0'
)

registry.register(
    name='fits',
    adapter_class=FITSAdapter,
    file_patterns=['*.fits', '*.fit', '*.fts'],
    description='FITS binary table adapter with multi-HDU support',
    version='1.0.0'
)

registry.register(
    name='csv',
    adapter_class=CSVAdapter,
    file_patterns=['*.csv', '*.tsv', '*.txt'],
    description='Generic CSV adapter with auto-delimiter detection and flexible column mapping',
    version='1.0.0'
)

logger.info(f"Pre-registered {len(registry.list_adapters())} built-in adapters")
