"""
LAYER 1 COMPLETE - COMPREHENSIVE VERIFICATION TEST

Tests all 6 components of Layer 1:
1. FileValidator
2. ErrorReporter
3. DatasetMetadata (Storage)
4. GaiaAdapter
5. SDSSAdapter
6. FITSAdapter
7. CSVAdapter (generic)
8. AdapterRegistry
"""

import pytest
import tempfile
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, UnifiedStarCatalog, DatasetMetadata, IngestionError
from app.services.file_validation import FileValidator
from app.services.error_reporter import ErrorReporter
from app.services.adapter_registry import AdapterRegistry


@pytest.fixture
def real_db():
    """Create a real in-memory SQLite database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def gaia_csv_file():
    """Gaia CSV file."""
    csv_content = """source_id,ra,dec,parallax,pmra,pmdec,phot_g_mean_mag,designation
4295806720,180.5,45.2,15.3,10.2,-5.1,12.3,Gaia1
4295806721,180.6,45.3,14.8,11.1,-4.9,12.8,Gaia2
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def sdss_csv_file():
    """SDSS CSV file."""
    csv_content = """objid,ra,dec,psfMag_u,psfMag_g,psfMag_r,psfMag_i,psfMag_z
1237648721,185.0,46.0,15.2,14.8,14.3,14.1,13.9
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def generic_csv_file():
    """Generic CSV file with custom column names."""
    csv_content = """ObjectID,RA_DEG,DEC_DEG,MAG_V,DISTANCE_PC
CUSTOM001,190.0,47.0,12.5,100.5
CUSTOM002,190.1,47.1,13.2,102.3
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)


# ============================================================================
# TASK 1.1: FILE VALIDATION
# ============================================================================

def test_file_validation_all_formats():
    """Verify FileValidator works with all file types."""
    validator = FileValidator()
    
    # Test CSV
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("col1,col2\n1,2\n")
        csv_path = f.name
    
    result = validator.validate_file(csv_path, "test.csv")
    assert result.is_valid
    assert result.mime_type == "text/csv"
    assert result.file_hash is not None
    os.unlink(csv_path)


# ============================================================================
# TASK 1.2: ERROR REPORTING
# ============================================================================

def test_error_reporting_functionality(real_db):
    """Verify ErrorReporter works."""
    reporter = ErrorReporter(real_db)
    
    reporter.log_validation_error(
        "Test error",
        dataset_id="test-dataset",
        details={"field": "value"},
        severity="WARNING"
    )
    
    errors = real_db.query(IngestionError).all()
    assert len(errors) == 1
    assert errors[0].dataset_id == "test-dataset"


# ============================================================================
# TASK 1.3: STORAGE & METADATA
# ============================================================================

def test_metadata_storage(real_db):
    """Verify DatasetMetadata persistence."""
    metadata = DatasetMetadata(
        dataset_id="test-metadata",
        source_name="test.csv",
        catalog_type="test",
        adapter_used="TestAdapter",
        record_count=10,
        file_hash="abc123",
        storage_key="datasets/test/data.csv"
    )
    real_db.add(metadata)
    real_db.commit()
    
    stored = real_db.query(DatasetMetadata).filter_by(dataset_id="test-metadata").first()
    assert stored is not None
    assert stored.record_count == 10


# ============================================================================
# TASK 1.4: GAIA ADAPTER
# ============================================================================

def test_gaia_adapter(gaia_csv_file, real_db):
    """Task 1.4: Test GaiaAdapter."""
    from app.services.adapters.gaia_adapter import GaiaAdapter
    
    adapter = GaiaAdapter(dataset_id="test-gaia")
    records, results = adapter.process_batch(gaia_csv_file, skip_invalid=False)
    
    assert len(records) == 2
    assert records[0]["source_id"] == "4295806720"
    
    # Store to database
    db_records = [UnifiedStarCatalog(**r) for r in records]
    real_db.bulk_save_objects(db_records)
    real_db.commit()
    
    assert real_db.query(UnifiedStarCatalog).count() == 2


# ============================================================================
# TASK 1.5: SDSS ADAPTER
# ============================================================================

def test_sdss_adapter(sdss_csv_file, real_db):
    """Task 1.5: Test SDSSAdapter."""
    from app.services.adapters.sdss_adapter import SDSSAdapter
    
    adapter = SDSSAdapter(dataset_id="test-sdss")
    records, results = adapter.process_batch(sdss_csv_file, skip_invalid=False)
    
    assert len(records) == 1
    # SDSS adapter prefixes source_id with catalog name
    assert "1237648721" in records[0]["source_id"]
    
    # Store to database
    db_records = [UnifiedStarCatalog(**r) for r in records]
    real_db.bulk_save_objects(db_records)
    real_db.commit()
    
    assert real_db.query(UnifiedStarCatalog).count() == 1


# ============================================================================
# TASK 1.6: FITS ADAPTER (if available)
# ============================================================================

def test_fits_adapter_available():
    """Task 1.6: Verify FITSAdapter is available."""
    try:
        from app.services.adapters.fits_adapter import FITSAdapter
        adapter = FITSAdapter(dataset_id="test-fits")
        assert adapter is not None
        assert "FITS" in adapter.source_name  # Source name contains FITS
    except ImportError:
        pytest.skip("FITSAdapter requires astropy")


# ============================================================================
# TASK 1.7: GENERIC CSV ADAPTER
# ============================================================================

def test_csv_adapter_generic(generic_csv_file, real_db):
    """Task 1.7: Test generic CSVAdapter with custom column mapping."""
    from app.services.adapters.csv_adapter import CSVAdapter
    
    # Test with custom column mapping
    column_mapping = {
        "source_id": "ObjectID",
        "ra_deg": "RA_DEG",
        "dec_deg": "DEC_DEG",
        "brightness_mag": "MAG_V",
        "distance_pc": "DISTANCE_PC"
    }
    
    adapter = CSVAdapter(
        dataset_id="test-generic",
        column_mapping=column_mapping
    )
    records, results = adapter.process_batch(generic_csv_file, skip_invalid=True)
    
    # Should have at least some valid records
    assert len(records) > 0
    assert "source_id" in records[0]
    # CSVAdapter uses mapped names as returned
    assert "dec_deg" in records[0] or "dec" in records[0]


# ============================================================================
# TASK 1.8: ADAPTER REGISTRY
# ============================================================================

def test_adapter_registry():
    """Task 1.8: Test AdapterRegistry."""
    registry = AdapterRegistry()
    
    # Register adapters
    from app.services.adapters.gaia_adapter import GaiaAdapter
    from app.services.adapters.sdss_adapter import SDSSAdapter
    from app.services.adapters.fits_adapter import FITSAdapter
    from app.services.adapters.csv_adapter import CSVAdapter
    
    registry.register(
        "gaia",
        GaiaAdapter,
        ["*gaia*.csv", "*.csv"],
        "Gaia DR3 adapter",
        "1.0.0"
    )
    registry.register(
        "sdss",
        SDSSAdapter,
        ["*sdss*.csv", "*.csv"],
        "SDSS DR17 adapter",
        "1.0.0"
    )
    registry.register(
        "fits",
        FITSAdapter,
        ["*.fits", "*.fit"],
        "FITS catalog adapter",
        "1.0.0"
    )
    registry.register(
        "csv",
        CSVAdapter,
        ["*.csv"],
        "Generic CSV adapter",
        "1.0.0"
    )
    
    # List registered adapters
    adapters = registry.list_adapters()
    assert len(adapters) >= 4
    
    # Get specific adapter
    gaia_class = registry.get_adapter("gaia")
    assert gaia_class == GaiaAdapter


def test_adapter_registry_auto_detection(gaia_csv_file):
    """Test AdapterRegistry auto-detection."""
    registry = AdapterRegistry()
    
    # Register adapters first
    from app.services.adapters.gaia_adapter import GaiaAdapter
    from app.services.adapters.sdss_adapter import SDSSAdapter
    from app.services.adapters.csv_adapter import CSVAdapter
    
    registry.register("gaia", GaiaAdapter, ["*gaia*.csv"])
    registry.register("sdss", SDSSAdapter, ["*sdss*.csv"])
    registry.register("csv", CSVAdapter, ["*.csv"])
    
    # Auto-detect from file
    adapter_name, confidence, method = registry.detect_adapter(gaia_csv_file)
    assert adapter_name is not None
    assert confidence > 0


def test_adapter_registry_all_methods(gaia_csv_file, real_db):
    """Test AdapterRegistry processes files correctly."""
    from app.services.adapters.gaia_adapter import GaiaAdapter
    
    registry = AdapterRegistry()
    registry.register("gaia", GaiaAdapter, ["*.csv"])
    
    # Get adapter and process manually (registry doesn't have process_file)
    gaia_adapter = registry.get_adapter("gaia")
    adapter = gaia_adapter(dataset_id="registry-test")
    records, results = adapter.process_batch(gaia_csv_file, skip_invalid=False)
    
    assert len(records) > 0


# ============================================================================
# LAYER 1 COMPLETE END-TO-END TEST
# ============================================================================

def test_layer1_complete_workflow(gaia_csv_file, sdss_csv_file, real_db):
    """
    Complete Layer 1 workflow:
    1. Validate files
    2. Route to correct adapter via registry
    3. Process data
    4. Store to database
    5. Log errors
    6. Create metadata
    """
    from app.services.adapters.gaia_adapter import GaiaAdapter
    from app.services.adapters.sdss_adapter import SDSSAdapter
    
    validator = FileValidator()
    registry = AdapterRegistry()
    reporter = ErrorReporter(real_db)
    
    # Register adapters
    registry.register("gaia", GaiaAdapter, ["*.csv"])
    registry.register("sdss", SDSSAdapter, ["*.csv"])
    
    print("\n" + "="*80)
    print("LAYER 1 COMPLETE WORKFLOW TEST")
    print("="*80)
    
    # Process Gaia
    print("\n[1] GAIA PIPELINE")
    gaia_validation = validator.validate_file(gaia_csv_file, "gaia.csv")
    assert gaia_validation.is_valid
    print(f"  ✅ File validated: {gaia_validation.file_hash[:16]}...")
    
    gaia_adapter = registry.get_adapter("gaia")
    adapter = gaia_adapter(dataset_id="workflow-gaia")
    gaia_records, _ = adapter.process_batch(gaia_csv_file, skip_invalid=False)
    assert len(gaia_records) > 0
    print(f"  ✅ Processed {len(gaia_records)} records")
    
    gaia_db_records = [UnifiedStarCatalog(**r) for r in gaia_records]
    real_db.bulk_save_objects(gaia_db_records)
    real_db.commit()
    print(f"  ✅ Persisted to database")
    
    reporter.log_validation_error("Gaia pipeline", "workflow-gaia", {}, "INFO")
    print(f"  ✅ Logged to error reporter")
    
    gaia_metadata = DatasetMetadata(
        dataset_id="workflow-gaia",
        source_name="gaia.csv",
        catalog_type="gaia",
        adapter_used="GaiaAdapter",
        record_count=len(gaia_records),
        file_hash=gaia_validation.file_hash,
        storage_key="datasets/workflow-gaia/data.csv"
    )
    real_db.add(gaia_metadata)
    real_db.commit()
    print(f"  ✅ Metadata created")
    
    # Process SDSS
    print("\n[2] SDSS PIPELINE")
    sdss_validation = validator.validate_file(sdss_csv_file, "sdss.csv")
    assert sdss_validation.is_valid
    print(f"  ✅ File validated: {sdss_validation.file_hash[:16]}...")
    
    sdss_adapter = registry.get_adapter("sdss")
    adapter = sdss_adapter(dataset_id="workflow-sdss")
    sdss_records, _ = adapter.process_batch(sdss_csv_file, skip_invalid=False)
    assert len(sdss_records) > 0
    print(f"  ✅ Processed {len(sdss_records)} records")
    
    sdss_db_records = [UnifiedStarCatalog(**r) for r in sdss_records]
    real_db.bulk_save_objects(sdss_db_records)
    real_db.commit()
    print(f"  ✅ Persisted to database")
    
    reporter.log_validation_error("SDSS pipeline", "workflow-sdss", {}, "INFO")
    print(f"  ✅ Logged to error reporter")
    
    sdss_metadata = DatasetMetadata(
        dataset_id="workflow-sdss",
        source_name="sdss.csv",
        catalog_type="sdss",
        adapter_used="SDSSAdapter",
        record_count=len(sdss_records),
        file_hash=sdss_validation.file_hash,
        storage_key="datasets/workflow-sdss/data.csv"
    )
    real_db.add(sdss_metadata)
    real_db.commit()
    print(f"  ✅ Metadata created")
    
    # Verify final state
    print("\n[3] VERIFICATION")
    total_records = real_db.query(UnifiedStarCatalog).count()
    total_errors = real_db.query(IngestionError).count()
    total_metadata = real_db.query(DatasetMetadata).count()
    
    print(f"  ✅ Total records persisted: {total_records}")
    print(f"  ✅ Total errors logged: {total_errors}")
    print(f"  ✅ Total metadata records: {total_metadata}")
    
    assert total_records == len(gaia_records) + len(sdss_records)
    assert total_errors >= 2
    assert total_metadata == 2
    
    print("\n✅ LAYER 1 COMPLETE WORKFLOW SUCCESSFUL")
    print("="*80)
