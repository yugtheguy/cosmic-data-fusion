"""
Configuration settings for COSMIC Data Fusion.

Controls feature flags and behavior toggles.
"""

import os
from typing import Literal

# ============================================================
# DATA LOADING CONFIGURATION
# ============================================================

# Enable/disable pre-bundled sample data loading
ENABLE_BUNDLED_DATA = os.getenv("COSMIC_ENABLE_BUNDLED_DATA", "false").lower() == "true"

# Enable/disable specific sample dataset loaders
ENABLE_GAIA_SAMPLE_LOADER = os.getenv("COSMIC_ENABLE_GAIA_SAMPLE_LOADER", "false").lower() == "true"
ENABLE_SDSS_SAMPLE_LOADER = os.getenv("COSMIC_ENABLE_SDSS_SAMPLE_LOADER", "false").lower() == "true"

# ============================================================
# API CONFIGURATION
# ============================================================

# API port
API_PORT = int(os.getenv("COSMIC_API_PORT", "8000"))

# API host
API_HOST = os.getenv("COSMIC_API_HOST", "0.0.0.0")

# Database configuration
DATABASE_URL = os.getenv(
    "COSMIC_DATABASE_URL",
    "sqlite:///./cosmic_data_fusion.db"
)

# ============================================================
# INGESTION CONFIGURATION
# ============================================================

# Maximum file upload size (in bytes)
MAX_UPLOAD_SIZE_MB = int(os.getenv("COSMIC_MAX_UPLOAD_SIZE_MB", "500"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# Maximum records to ingest in a single operation
MAX_INGEST_RECORDS = int(os.getenv("COSMIC_MAX_INGEST_RECORDS", "50000"))

# ============================================================
# LOGGING CONFIGURATION
# ============================================================

LOG_LEVEL = os.getenv("COSMIC_LOG_LEVEL", "INFO")

# ============================================================
# FEATURE FLAGS
# ============================================================

# Enable natural language query support
ENABLE_NL_QUERY = os.getenv("COSMIC_ENABLE_NL_QUERY", "true").lower() == "true"

# Enable AI discovery features
ENABLE_AI_DISCOVERY = os.getenv("COSMIC_ENABLE_AI_DISCOVERY", "true").lower() == "true"

# Enable harmonization features
ENABLE_HARMONIZATION = os.getenv("COSMIC_ENABLE_HARMONIZATION", "true").lower() == "true"


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_config_summary() -> dict:
    """
    Get current configuration summary.
    
    Returns:
        Dictionary with configuration values
    """
    return {
        "bundled_data_enabled": ENABLE_BUNDLED_DATA,
        "gaia_sample_loader_enabled": ENABLE_GAIA_SAMPLE_LOADER,
        "sdss_sample_loader_enabled": ENABLE_SDSS_SAMPLE_LOADER,
        "max_upload_size_mb": MAX_UPLOAD_SIZE_MB,
        "max_ingest_records": MAX_INGEST_RECORDS,
        "features": {
            "nl_query": ENABLE_NL_QUERY,
            "ai_discovery": ENABLE_AI_DISCOVERY,
            "harmonization": ENABLE_HARMONIZATION,
        }
    }
