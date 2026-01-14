"""
LAYER 1 END-TO-END VERIFICATION TEST - NO MOCKS

This test verifies the complete Layer 1 pipeline with REAL components
using actual test data files that match adapter requirements.
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


# ============================================================================
# REAL DATABASE SETUP (No mocking)
# ============================================================================

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


# ============================================================================
# REAL CSV FILES MATCHING ADAPTER SCHEMAS
# ============================================================================

@pytest.fixture
def real_gaia_csv_file():
    """Create a real Gaia CSV file that matches GaiaAdapter schema."""
    csv_content = """source_id,ra,dec,parallax,pmra,pmdec,phot_g_mean_mag,designation
4295806720,180.5,45.2,15.3,10.2,-5.1,12.3,Gaia DR3 1
4295806721,180.6,45.3,14.8,11.1,-4.9,12.8,Gaia DR3 2
4295806722,180.7,45.4,15.1,10.5,-5.3,12.5,Gaia DR3 3
4295806723,180.8,45.5,15.4,10.8,-5.0,12.2,Gaia DR3 4
4295806724,180.9,45.6,14.9,11.2,-4.8,13.1,Gaia DR3 5
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        f.flush()
        temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def real_sdss_csv_file():
    """Create a real SDSS CSV file that matches SDSSAdapter schema."""
    csv_content = """objid,ra,dec,psfMag_u,psfMag_g,psfMag_r,psfMag_i,psfMag_z
1237648721,185.0,46.0,15.2,14.8,14.3,14.1,13.9
1237648722,185.1,46.1,15.5,14.9,14.4,14.2,14.0
1237648723,185.2,46.2,15.1,14.7,14.2,14.0,13.8
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        f.flush()
        temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def real_fits_file():
    """Use actual Hipparcos FITS file from app/data."""
    fits_path = Path(__file__).parent.parent / "app" / "data" / "hipparcos_sample.fits"
    if not fits_path.exists():
        pytest.skip(f"FITS file not found: {fits_path}")
    return str(fits_path)


@pytest.fixture
def real_generic_csv_file():
    """Create a real generic CSV file that CSVAdapter can auto-detect."""
    csv_content = """ra,dec,mag,parallax,source_id
190.0,47.0,13.5,8.2,custom_001
190.1,47.1,13.8,8.5,custom_002
190.2,47.2,13.2,8.1,custom_003
190.3,47.3,13.9,8.7,custom_004
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        f.flush()
        temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.unlink(temp_path)


# ============================================================================
# TEST 1: FILE VALIDATION WITH REAL FILES
# ============================================================================

def test_file_validation_with_real_gaia_file(real_gaia_csv_file):
    """Test FileValidator with real Gaia CSV file."""
    validator = FileValidator()
    
    # Validate using file path (NO MOCKS)
    result = validator.validate_file(
        file_path=real_gaia_csv_file,
        filename="gaia.csv"
    )
    
    # Verify validation passed
    assert result.is_valid, f"Validation failed: {result.errors}"
    assert result.file_hash is not None
    assert len(result.file_hash) == 64  # SHA256
    assert result.mime_type == 'text/csv'
    assert result.file_size > 0
    print(f"✅ Task 1.1 - Gaia file validation passed")
    print(f"   File hash: {result.file_hash[:16]}...")


def test_file_validation_with_real_sdss_file(real_sdss_csv_file):
    """Test FileValidator with real SDSS CSV file."""
    validator = FileValidator()
    
    result = validator.validate_file(
        file_path=real_sdss_csv_file,
        filename="sdss.csv"
    )
    
    assert result.is_valid, f"Validation failed: {result.errors}"
    assert result.file_hash is not None
    assert result.mime_type == 'text/csv'
    print(f"✅ Task 1.1 - SDSS file validation passed")
    print(f"   File hash: {result.file_hash[:16]}...")


# ============================================================================
# TEST 2: DATABASE PERSISTENCE WITH REAL DATA
# ============================================================================

def test_error_logging_persists_to_real_database(real_db):
    """Test ErrorReporter writes to REAL database."""
    error_reporter = ErrorReporter(real_db)
    
    # Log errors (NO MOCKS)
    error_reporter.log_validation_error(
        message="Test validation error",
        dataset_id="db-test-001",
        details={"filename": "test.csv"},
        severity="ERROR"
    )
    
    # Query database directly
    errors = real_db.query(IngestionError).filter_by(
        dataset_id="db-test-001"
    ).all()
    
    # Verify actual persistence
    assert len(errors) == 1
    assert errors[0].error_type == "VALIDATION"
    assert errors[0].message == "Test validation error"
    print("✅ Task 1.2 - Error persisted to real database")


def test_dataset_metadata_persists_to_real_database(real_db):
    """Test DatasetMetadata persists to REAL database."""
    
    dataset = DatasetMetadata(
        dataset_id="meta-test-001",
        source_name="real_data.csv",
        catalog_type="gaia",
        adapter_used="GaiaAdapter",
        record_count=100,
        original_filename="real_data.csv",
        file_size_bytes=5120,
        file_hash="a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
        storage_key="datasets/meta-test-001/files/data.csv",
        license_info="ESA/Gaia DPAC"
    )
    
    real_db.add(dataset)
    real_db.commit()
    
    # Query back
    retrieved = real_db.query(DatasetMetadata).filter_by(
        dataset_id="meta-test-001"
    ).first()
    
    # Verify all fields persisted
    assert retrieved is not None
    assert retrieved.source_name == "real_data.csv"
    assert retrieved.record_count == 100
    assert retrieved.file_hash == "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"
    assert retrieved.storage_key == "datasets/meta-test-001/files/data.csv"
    print("✅ Task 1.3 - Metadata persisted to real database")


# ============================================================================
# TEST 3: REAL ADAPTERS WITH REAL DATA
# ============================================================================

def test_gaia_adapter_processes_real_file(real_gaia_csv_file, real_db):
    """Test GaiaAdapter with real file path."""
    from app.services.adapters.gaia_adapter import GaiaAdapter
    
    # Process with REAL adapter (NO MOCKS)
    adapter = GaiaAdapter(dataset_id="real-gaia-test")
    valid_records, validation_results = adapter.process_batch(
        real_gaia_csv_file,
        skip_invalid=False
    )
    
    # Verify records extracted
    assert len(valid_records) == 5
    
    # Insert into REAL database
    db_records = [UnifiedStarCatalog(**r) for r in valid_records]
    real_db.bulk_save_objects(db_records)
    real_db.commit()
    
    # Query back from database
    saved = real_db.query(UnifiedStarCatalog).filter_by(
        dataset_id="real-gaia-test"
    ).all()
    
    assert len(saved) == 5
    assert saved[0].ra_deg is not None
    assert saved[0].dec_deg is not None
    print(f"✅ GaiaAdapter - 5 real records processed and saved to database")


def test_sdss_adapter_processes_real_file(real_sdss_csv_file, real_db):
    """Test SDSSAdapter with real file path."""
    from app.services.adapters.sdss_adapter import SDSSAdapter
    
    adapter = SDSSAdapter(dataset_id="real-sdss-test")
    valid_records, validation_results = adapter.process_batch(
        real_sdss_csv_file,
        skip_invalid=False
    )
    
    assert len(valid_records) == 3
    
    db_records = [UnifiedStarCatalog(**r) for r in valid_records]
    real_db.bulk_save_objects(db_records)
    real_db.commit()
    
    saved = real_db.query(UnifiedStarCatalog).filter_by(
        dataset_id="real-sdss-test"
    ).all()
    
    assert len(saved) == 3
    print(f"✅ SDSSAdapter - 3 real records processed and saved to database")


def test_fits_adapter_processes_real_file(real_fits_file, real_db):
    """Test FITSAdapter with real Hipparcos FITS file."""
    try:
        from app.services.adapters.fits_adapter import FITSAdapter
    except ImportError:
        pytest.skip("FITSAdapter requires astropy")
    
    adapter = FITSAdapter(dataset_id="real-fits-test")
    valid_records, validation_results = adapter.process_batch(
        real_fits_file,
        skip_invalid=True,
        extension=1  # Use first extension HDU
    )
    
    # Hipparcos sample should have records
    assert len(valid_records) > 0
    print(f"  Parsed {len(valid_records)} records from FITS file")
    
    # Insert into database
    db_records = [UnifiedStarCatalog(**r) for r in valid_records[:10]]  # Limit to 10 for test
    real_db.bulk_save_objects(db_records)
    real_db.commit()
    
    saved = real_db.query(UnifiedStarCatalog).filter_by(
        dataset_id="real-fits-test"
    ).all()
    
    assert len(saved) == 10
    assert saved[0].ra_deg is not None
    assert saved[0].dec_deg is not None
    print(f"✅ FITSAdapter - {len(saved)} real records processed and saved to database")


def test_csv_adapter_processes_real_file(real_generic_csv_file, real_db):
    """Test generic CSVAdapter with auto-detection."""
    from app.services.adapters.csv_adapter import CSVAdapter
    
    adapter = CSVAdapter(dataset_id="real-csv-test")
    valid_records, validation_results = adapter.process_batch(
        real_generic_csv_file,
        skip_invalid=False
    )
    
    assert len(valid_records) == 4
    
    db_records = [UnifiedStarCatalog(**r) for r in valid_records]
    real_db.bulk_save_objects(db_records)
    real_db.commit()
    
    saved = real_db.query(UnifiedStarCatalog).filter_by(
        dataset_id="real-csv-test"
    ).all()
    
    assert len(saved) == 4
    assert saved[0].ra_deg is not None
    assert saved[0].dec_deg is not None
    print(f"✅ CSVAdapter - 4 real records processed and saved to database")


# ============================================================================
# TEST 4: COMPLETE END-TO-END PIPELINE
# ============================================================================

def test_complete_e2e_pipeline_gaia(real_gaia_csv_file, real_db):
    """Complete pipeline: validate → process → insert → metadata → errors."""
    from app.services.adapters.gaia_adapter import GaiaAdapter
    
    print("\n" + "="*70)
    print("COMPLETE END-TO-END PIPELINE TEST (GAIA)")
    print("="*70)
    
    # 1. VALIDATE FILE (REAL)
    validator = FileValidator()
    validation_result = validator.validate_file(
        file_path=real_gaia_csv_file,
        filename="gaia_e2e.csv"
    )
    
    assert validation_result.is_valid
    file_hash = validation_result.file_hash
    print(f"1. ✅ File validated - hash: {file_hash[:16]}...")
    
    # 2. PROCESS WITH ADAPTER (REAL)
    adapter = GaiaAdapter(dataset_id="e2e-gaia-test")
    valid_records, validation_results = adapter.process_batch(
        real_gaia_csv_file,
        skip_invalid=False
    )
    
    assert len(valid_records) == 5
    print(f"2. ✅ Adapter processed {len(valid_records)} records")
    
    # 3. INSERT TO DATABASE (REAL)
    db_records = [UnifiedStarCatalog(**r) for r in valid_records]
    real_db.bulk_save_objects(db_records)
    real_db.commit()
    
    saved_count = real_db.query(UnifiedStarCatalog).filter_by(
        dataset_id="e2e-gaia-test"
    ).count()
    
    assert saved_count == 5
    print(f"3. ✅ {saved_count} records inserted to real database")
    
    # 4. LOG ERRORS (REAL)
    error_reporter = ErrorReporter(real_db)
    error_reporter.log_validation_error(
        message="Test validation in pipeline",
        dataset_id="e2e-gaia-test",
        details={},
        severity="WARNING"
    )
    
    errors = real_db.query(IngestionError).filter_by(
        dataset_id="e2e-gaia-test"
    ).all()
    
    assert len(errors) == 1
    print(f"4. ✅ Errors logged to real database")
    
    # 5. CREATE METADATA (REAL)
    dataset = DatasetMetadata(
        dataset_id="e2e-gaia-test",
        source_name="gaia_e2e.csv",
        catalog_type="gaia",
        adapter_used="GaiaAdapter",
        record_count=5,
        original_filename="gaia_e2e.csv",
        file_size_bytes=1024,
        file_hash=file_hash,
        storage_key="datasets/e2e-gaia-test/files/data.csv",
        license_info="ESA/Gaia DPAC"
    )
    
    real_db.add(dataset)
    real_db.commit()
    
    metadata = real_db.query(DatasetMetadata).filter_by(
        dataset_id="e2e-gaia-test"
    ).first()
    
    assert metadata is not None
    assert metadata.record_count == 5
    assert metadata.file_hash == file_hash
    print(f"5. ✅ Metadata created with file_hash={file_hash[:16]}...")
    
    print("\n✅ COMPLETE END-TO-END PIPELINE SUCCESSFUL")
    print("="*70)


def test_complete_e2e_pipeline_sdss(real_sdss_csv_file, real_db):
    """Complete pipeline for SDSS."""
    from app.services.adapters.sdss_adapter import SDSSAdapter
    
    print("\n" + "="*70)
    print("COMPLETE END-TO-END PIPELINE TEST (SDSS)")
    print("="*70)
    
    # 1. VALIDATE
    validator = FileValidator()
    validation_result = validator.validate_file(
        file_path=real_sdss_csv_file,
        filename="sdss_e2e.csv"
    )
    
    assert validation_result.is_valid
    file_hash = validation_result.file_hash
    print(f"1. ✅ File validated - hash: {file_hash[:16]}...")
    
    # 2. PROCESS
    adapter = SDSSAdapter(dataset_id="e2e-sdss-test")
    valid_records, _ = adapter.process_batch(
        real_sdss_csv_file,
        skip_invalid=False
    )
    
    assert len(valid_records) == 3
    print(f"2. ✅ Adapter processed {len(valid_records)} records")
    
    # 3. INSERT
    db_records = [UnifiedStarCatalog(**r) for r in valid_records]
    real_db.bulk_save_objects(db_records)
    real_db.commit()
    
    saved_count = real_db.query(UnifiedStarCatalog).filter_by(
        dataset_id="e2e-sdss-test"
    ).count()
    
    assert saved_count == 3
    print(f"3. ✅ {saved_count} records inserted to real database")
    
    # 4. CREATE METADATA
    dataset = DatasetMetadata(
        dataset_id="e2e-sdss-test",
        source_name="sdss_e2e.csv",
        catalog_type="sdss",
        adapter_used="SDSSAdapter",
        record_count=3,
        file_hash=file_hash,
        storage_key="datasets/e2e-sdss-test/files/data.csv",
        license_info="SDSS DR17"
    )
    
    real_db.add(dataset)
    real_db.commit()
    
    print(f"4. ✅ Metadata created")
    print("\n✅ COMPLETE END-TO-END PIPELINE SUCCESSFUL")
    print("="*70)


def test_complete_e2e_pipeline_fits(real_fits_file, real_db):
    """Complete pipeline for FITS files."""
    try:
        from app.services.adapters.fits_adapter import FITSAdapter
    except ImportError:
        pytest.skip("FITSAdapter requires astropy")
    
    print("\n" + "="*70)
    print("COMPLETE END-TO-END PIPELINE TEST (FITS)")
    print("="*70)
    
    # 1. VALIDATE
    validator = FileValidator()
    validation_result = validator.validate_file(
        file_path=real_fits_file,
        filename="hipparcos_e2e.fits"
    )
    
    assert validation_result.is_valid
    file_hash = validation_result.file_hash
    print(f"1. ✅ File validated - hash: {file_hash[:16]}...")
    
    # 2. PROCESS
    adapter = FITSAdapter(dataset_id="e2e-fits-test")
    valid_records, _ = adapter.process_batch(
        real_fits_file,
        skip_invalid=True,
        extension=1
    )
    
    assert len(valid_records) > 0
    record_count = min(len(valid_records), 15)  # Limit to 15 for testing
    print(f"2. ✅ Adapter processed {record_count} records (limited from {len(valid_records)})")
    
    # 3. INSERT
    db_records = [UnifiedStarCatalog(**r) for r in valid_records[:record_count]]
    real_db.bulk_save_objects(db_records)
    real_db.commit()
    
    saved_count = real_db.query(UnifiedStarCatalog).filter_by(
        dataset_id="e2e-fits-test"
    ).count()
    
    assert saved_count == record_count
    print(f"3. ✅ {saved_count} records inserted to real database")
    
    # 4. CREATE METADATA
    dataset = DatasetMetadata(
        dataset_id="e2e-fits-test",
        source_name="hipparcos_e2e.fits",
        catalog_type="fits",
        adapter_used="FITSAdapter",
        record_count=record_count,
        file_hash=file_hash,
        storage_key="datasets/e2e-fits-test/files/data.fits",
        license_info="ESA Hipparcos"
    )
    
    real_db.add(dataset)
    real_db.commit()
    
    print(f"4. ✅ Metadata created")
    print("\n✅ COMPLETE END-TO-END PIPELINE SUCCESSFUL (FITS)")
    print("="*70)


def test_complete_e2e_pipeline_csv(real_generic_csv_file, real_db):
    """Complete pipeline for generic CSV files."""
    from app.services.adapters.csv_adapter import CSVAdapter
    
    print("\n" + "="*70)
    print("COMPLETE END-TO-END PIPELINE TEST (GENERIC CSV)")
    print("="*70)
    
    # 1. VALIDATE
    validator = FileValidator()
    validation_result = validator.validate_file(
        file_path=real_generic_csv_file,
        filename="custom_e2e.csv"
    )
    
    assert validation_result.is_valid
    file_hash = validation_result.file_hash
    print(f"1. ✅ File validated - hash: {file_hash[:16]}...")
    
    # 2. PROCESS
    adapter = CSVAdapter(dataset_id="e2e-csv-test")
    valid_records, _ = adapter.process_batch(
        real_generic_csv_file,
        skip_invalid=False
    )
    
    assert len(valid_records) == 4
    print(f"2. ✅ Adapter processed {len(valid_records)} records")
    
    # 3. INSERT
    db_records = [UnifiedStarCatalog(**r) for r in valid_records]
    real_db.bulk_save_objects(db_records)
    real_db.commit()
    
    saved_count = real_db.query(UnifiedStarCatalog).filter_by(
        dataset_id="e2e-csv-test"
    ).count()
    
    assert saved_count == 4
    print(f"3. ✅ {saved_count} records inserted to real database")
    
    # 4. CREATE METADATA
    dataset = DatasetMetadata(
        dataset_id="e2e-csv-test",
        source_name="custom_e2e.csv",
        catalog_type="csv",
        adapter_used="CSVAdapter",
        record_count=4,
        file_hash=file_hash,
        storage_key="datasets/e2e-csv-test/files/data.csv",
        license_info="Custom Catalog"
    )
    
    real_db.add(dataset)
    real_db.commit()
    
    print(f"4. ✅ Metadata created")
    print("\n✅ COMPLETE END-TO-END PIPELINE SUCCESSFUL (CSV)")
    print("="*70)


# ============================================================================
# TEST 5: DATA INTEGRITY VERIFICATION
# ============================================================================

def test_file_hash_consistency(real_gaia_csv_file):
    """Verify file hash is consistent for same file."""
    validator = FileValidator()
    
    hash1 = validator.validate_file(real_gaia_csv_file, "test.csv").file_hash
    hash2 = validator.validate_file(real_gaia_csv_file, "test.csv").file_hash
    
    assert hash1 == hash2
    print(f"✅ File hash consistency: {hash1[:16]}... == {hash2[:16]}...")


def test_data_transformation_consistency(real_gaia_csv_file, real_db):
    """Verify same input produces same output."""
    from app.services.adapters.gaia_adapter import GaiaAdapter
    
    adapter1 = GaiaAdapter(dataset_id="consistency-1")
    records1, _ = adapter1.process_batch(real_gaia_csv_file, skip_invalid=False)
    
    adapter2 = GaiaAdapter(dataset_id="consistency-2")
    records2, _ = adapter2.process_batch(real_gaia_csv_file, skip_invalid=False)
    
    assert len(records1) == len(records2)
    assert records1[0]['ra_deg'] == records2[0]['ra_deg']
    print(f"✅ Data transformation consistency verified")


# ============================================================================
# TEST 6: DATASET ISOLATION
# ============================================================================

def test_multiple_datasets_isolated(real_gaia_csv_file, real_sdss_csv_file, real_db):
    """Verify different datasets don't interfere."""
    from app.services.adapters.gaia_adapter import GaiaAdapter
    from app.services.adapters.sdss_adapter import SDSSAdapter
    
    # Process Gaia
    gaia_adapter = GaiaAdapter(dataset_id="isolated-gaia")
    gaia_records, _ = gaia_adapter.process_batch(real_gaia_csv_file, skip_invalid=False)
    gaia_db = [UnifiedStarCatalog(**r) for r in gaia_records]
    real_db.bulk_save_objects(gaia_db)
    real_db.commit()
    
    # Process SDSS
    sdss_adapter = SDSSAdapter(dataset_id="isolated-sdss")
    sdss_records, _ = sdss_adapter.process_batch(real_sdss_csv_file, skip_invalid=False)
    sdss_db = [UnifiedStarCatalog(**r) for r in sdss_records]
    real_db.bulk_save_objects(sdss_db)
    real_db.commit()
    
    # Verify isolation
    gaia_count = real_db.query(UnifiedStarCatalog).filter_by(
        dataset_id="isolated-gaia"
    ).count()
    
    sdss_count = real_db.query(UnifiedStarCatalog).filter_by(
        dataset_id="isolated-sdss"
    ).count()
    
    total = real_db.query(UnifiedStarCatalog).count()
    
    assert gaia_count == 5
    assert sdss_count == 3
    assert total == 8
    
    print(f"✅ Dataset isolation: {gaia_count} Gaia + {sdss_count} SDSS = {total} total")


# ============================================================================
# TEST 7: FINAL SUMMARY VERIFICATION
# ============================================================================

def test_layer1_final_verification(real_gaia_csv_file, real_sdss_csv_file, real_db):
    """
    FINAL LAYER 1 VERIFICATION
    
    ✅ All 3 tasks complete and working together:
       Task 1.1: File Validation (real files, real validation)
       Task 1.2: Error Reporting (real database persistence)
       Task 1.3: Storage (real metadata, real database)
       
    ✅ No mocks, no test doubles
    ✅ Real data flowing through entire pipeline
    ✅ Real database persistence at every step
    """
    
    print("\n" + "="*80)
    print("LAYER 1 FINAL VERIFICATION - COMPLETE END-TO-END, NO MOCKS")
    print("="*80)
    
    # Instantiate all services with REAL components (no mocks)
    validator = FileValidator()
    error_reporter = ErrorReporter(real_db)
    
    from app.services.adapters.gaia_adapter import GaiaAdapter
    from app.services.adapters.sdss_adapter import SDSSAdapter
    
    # Test Gaia pipeline
    print("\n[GAIA PIPELINE]")
    gaia_val = validator.validate_file(real_gaia_csv_file, "gaia.csv")
    assert gaia_val.is_valid
    print(f"  ✅ File validated: {gaia_val.file_hash[:16]}...")
    
    gaia_adapter = GaiaAdapter(dataset_id="final-gaia")
    gaia_records, _ = gaia_adapter.process_batch(real_gaia_csv_file, skip_invalid=False)
    assert len(gaia_records) == 5
    print(f"  ✅ {len(gaia_records)} records processed")
    
    gaia_db = [UnifiedStarCatalog(**r) for r in gaia_records]
    real_db.bulk_save_objects(gaia_db)
    real_db.commit()
    print(f"  ✅ Records persisted to database")
    
    error_reporter.log_validation_error(
        "Gaia test",
        dataset_id="final-gaia",
        details={},
        severity="WARNING"
    )
    print(f"  ✅ Errors logged to database")
    
    gaia_meta = DatasetMetadata(
        dataset_id="final-gaia",
        source_name="gaia.csv",
        catalog_type="gaia",
        adapter_used="GaiaAdapter",
        record_count=5,
        file_hash=gaia_val.file_hash,
        storage_key="datasets/final-gaia/files/data.csv"
    )
    real_db.add(gaia_meta)
    real_db.commit()
    print(f"  ✅ Metadata created")
    
    # Test SDSS pipeline
    print("\n[SDSS PIPELINE]")
    sdss_val = validator.validate_file(real_sdss_csv_file, "sdss.csv")
    assert sdss_val.is_valid
    print(f"  ✅ File validated: {sdss_val.file_hash[:16]}...")
    
    sdss_adapter = SDSSAdapter(dataset_id="final-sdss")
    sdss_records, _ = sdss_adapter.process_batch(real_sdss_csv_file, skip_invalid=False)
    assert len(sdss_records) == 3
    print(f"  ✅ {len(sdss_records)} records processed")
    
    sdss_db = [UnifiedStarCatalog(**r) for r in sdss_records]
    real_db.bulk_save_objects(sdss_db)
    real_db.commit()
    print(f"  ✅ Records persisted to database")
    
    sdss_meta = DatasetMetadata(
        dataset_id="final-sdss",
        source_name="sdss.csv",
        catalog_type="sdss",
        adapter_used="SDSSAdapter",
        record_count=3,
        file_hash=sdss_val.file_hash,
        storage_key="datasets/final-sdss/files/data.csv"
    )
    real_db.add(sdss_meta)
    real_db.commit()
    print(f"  ✅ Metadata created")
    
    # Final verification
    print("\n[FINAL VERIFICATION]")
    gaia_total = real_db.query(UnifiedStarCatalog).filter_by(dataset_id="final-gaia").count()
    sdss_total = real_db.query(UnifiedStarCatalog).filter_by(dataset_id="final-sdss").count()
    errors_count = real_db.query(IngestionError).count()
    meta_count = real_db.query(DatasetMetadata).count()
    
    print(f"  ✅ Gaia records in DB: {gaia_total}")
    print(f"  ✅ SDSS records in DB: {sdss_total}")
    print(f"  ✅ Errors tracked: {errors_count}")
    print(f"  ✅ Metadata entries: {meta_count}")
    
    assert gaia_total == 5
    assert sdss_total == 3
    assert errors_count >= 1
    assert meta_count >= 2
    
    print("\n" + "="*80)
    print("✅ LAYER 1 VERIFICATION COMPLETE")
    print("✅ ALL 3 TASKS WORKING END-TO-END WITH REAL DATA, NO MOCKS")
    print("✅ READY FOR LAYER 2")
    print("="*80 + "\n")
