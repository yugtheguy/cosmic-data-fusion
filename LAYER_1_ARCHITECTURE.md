# Layer 1 Architecture Diagram

## Service Layer Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    INGESTION ENDPOINTS                          │
│                  (FastAPI Routers)                              │
│                                                                 │
│  POST /ingest/gaia          POST /ingest/sdss                  │
│  POST /ingest/star          GET  /health                       │
│                                                                 │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER                              │
│                    (Business Logic)                             │
│                                                                 │
│  ┌──────────────────────┐  ┌──────────────────────┐            │
│  │  FileValidator       │  │  ErrorReporter       │            │
│  ├──────────────────────┤  ├──────────────────────┤            │
│  │ • MIME detection     │  │ • Log validation err │            │
│  │ • Size validation    │  │ • Log parsing errors │            │
│  │ • Encoding detect    │  │ • CSV export         │            │
│  │ • SHA256 hashing     │  │ • Error statistics   │            │
│  └──────────────────────┘  └──────────────────────┘            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         StorageService (MinIO/S3)                        │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ • Upload file with metadata                             │  │
│  │ • Download/retrieve files                               │  │
│  │ • Presigned URL generation                              │  │
│  │ • File deletion (single & bulk)                          │  │
│  │ • Metadata retrieval                                    │  │
│  │ • Dataset file listing                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Adapter Layer                                    │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ • GaiaAdapter (Gaia DR3 data)                           │  │
│  │ • SDSSAdapter (SDSS DR17 data)                          │  │
│  │ • FITSAdapter (FITS binary format)                      │  │
│  │ • CSVAdapter (CSV tabular data)                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                    DATABASE LAYER                               │
│                   (SQLAlchemy ORM)                              │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ UnifiedStarCat   │  │ DatasetMetadata  │  │ IngestionErr │ │
│  ├──────────────────┤  ├──────────────────┤  ├──────────────┤ │
│  │ • record_id      │  │ • dataset_id     │  │ • error_id   │ │
│  │ • ra_deg         │  │ • source_name    │  │ • error_type │ │
│  │ • dec_deg        │  │ • catalog_type   │  │ • severity   │ │
│  │ • magnitude      │  │ • file_hash      │  │ • message    │ │
│  │ • star_id        │  │ • storage_key    │  │ • details    │ │
│  │ • source_table   │  │ • record_count   │  │ • dataset_id │ │
│  │ • dataset_id     │  │ • license_info   │  │ • source_row │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│                                                                 │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                  STORAGE LAYER                                  │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │    PostgreSQL    │  │     MinIO        │  │  File Cache  │ │
│  │   (Metadata)     │  │   (Raw Files)    │  │  (Optional)  │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│                                                                 │
└──────────────────────────────────────────────────────────────────┘
```

## Data Flow: File Upload to Persistence

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. FILE UPLOAD                                                  │
│    POST /ingest/gaia (multipart/form-data with file)           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. FILE VALIDATION (FileValidator)                             │
│    ├─ Check MIME type (CSV, FITS, JSON, VotTable)            │
│    ├─ Validate file size (max 500MB)                          │
│    ├─ Detect encoding (UTF-8, ASCII, ISO-8859-1)             │
│    ├─ Calculate SHA256 hash                                   │
│    └─ Return validation result with file_hash                 │
│                                                                 │
│    If invalid:                                                  │
│    └─ ErrorReporter.log_validation_error()                    │
│    └─ Return 400 Bad Request                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. ADAPTER PROCESSING                                           │
│    ├─ GaiaAdapter.process_batch()                             │
│    │  └─ Parse CSV/FITS format                                │
│    │  └─ Validate each record                                 │
│    │  └─ Transform to unified schema                          │
│    │                                                            │
│    └─ SDSSAdapter.process_batch()                             │
│       └─ Same as above for SDSS data                          │
│                                                                 │
│    If parsing errors:                                           │
│    └─ ErrorReporter.log_parsing_error()                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. DATABASE INSERTION                                           │
│    ├─ Create UnifiedStarCatalog records                        │
│    ├─ Bulk insert (optimized)                                 │
│    ├─ Commit transaction                                       │
│    │                                                            │
│    └─ If database error:                                       │
│       └─ ErrorReporter.log_database_error()                   │
│       └─ Rollback transaction                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. FILE STORAGE (StorageService → MinIO)                       │
│    ├─ Upload file to MinIO bucket                             │
│    ├─ Store metadata (original_filename, dataset_id, hash)    │
│    ├─ Generate storage_key for retrieval                      │
│    │                                                            │
│    └─ If storage error:                                        │
│       └─ Log warning (data already in DB)                     │
│       └─ Continue (file storage is optional for data safety)  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. METADATA REGISTRATION (DatasetMetadata)                     │
│    ├─ Create DatasetMetadata record                           │
│    ├─ Store file_hash (for duplicate detection)               │
│    ├─ Store storage_key (for file retrieval)                  │
│    ├─ Store catalog_type, adapter_used, record_count          │
│    └─ Commit transaction                                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ SUCCESS RESPONSE (200 OK)                                       │
│ {                                                               │
│   "success": true,                                             │
│   "message": "Successfully ingested N records...",             │
│   "ingested_count": 100,                                       │
│   "failed_count": 2,                                           │
│   "dataset_id": "uuid",                                        │
│   "file_hash": "sha256_hex",                                   │
│   "storage_key": "datasets/uuid/files/..."                    │
│ }                                                               │
└─────────────────────────────────────────────────────────────────┘
```

## Error Tracking Pipeline

```
┌──────────────────────────────────────────────────────────┐
│ ERROR OCCURS AT ANY STAGE                                │
└──────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────┐
│ ErrorReporter Service                                    │
├──────────────────────────────────────────────────────────┤
│ Categorizes error:                                       │
│  • VALIDATION - File validation failed                  │
│  • PARSING - Record parsing/schema mismatch             │
│  • ENCODING - Character encoding issue                  │
│  • DATABASE - Insert/transaction error                  │
│  • TYPE_MISMATCH - Data type validation                │
│  • UNKNOWN - Unexpected error                           │
│                                                          │
│ Assigns severity:                                        │
│  • ERROR - Standard error                               │
│  • WARNING - Recoverable issue                          │
│  • CRITICAL - System failure                            │
└──────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────┐
│ IngestionError ORM Model (PostgreSQL)                    │
├──────────────────────────────────────────────────────────┤
│ Persists:                                                │
│  • error_type (categorized)                             │
│  • severity (level)                                      │
│  • message (human-readable)                             │
│  • details (JSON with full context)                     │
│  • source_row (where in file)                           │
│  • dataset_id (which import)                            │
│  • timestamp (when it occurred)                         │
└──────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────┐
│ Error API Endpoints                                      │
├──────────────────────────────────────────────────────────┤
│ GET  /errors/dataset/{id}              (list errors)     │
│ GET  /errors/summary/{id}              (statistics)      │
│ GET  /errors/export/{id}               (CSV download)    │
│ DELETE /errors/{id}                    (delete single)    │
│ DELETE /errors/dataset/{id}            (delete all)       │
└──────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────┐
│ User/Admin Access                                        │
├──────────────────────────────────────────────────────────┤
│ • Review what went wrong                                 │
│ • Identify patterns                                      │
│ • Improve data quality                                   │
│ • Audit ingestion process                                │
│ • Export errors for reporting                            │
└──────────────────────────────────────────────────────────┘
```

## File Storage Architecture

```
┌──────────────────────────────────────────────────────────┐
│ StorageService                                           │
├──────────────────────────────────────────────────────────┤
│ Configuration:                                           │
│  • MINIO_ENDPOINT (localhost:9000)                      │
│  • MINIO_ACCESS_KEY (minioadmin)                        │
│  • MINIO_SECRET_KEY (minioadmin)                        │
│  • MINIO_BUCKET (astronomical-data)                     │
│  • MINIO_SECURE (false for local, true for prod)        │
│                                                          │
│ Can be overridden via environment variables             │
└──────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────┐
│ MinIO Object Storage (S3-compatible)                     │
├──────────────────────────────────────────────────────────┤
│ Bucket: astronomical-data/                              │
│                                                          │
│ File organization:                                       │
│ datasets/                                               │
│ ├─ {dataset_id_1}/                                     │
│ │  └─ files/                                            │
│ │     ├─ 20240115_144530_gaia_dr3.csv                  │
│ │     └─ 20240115_150245_sdss_dr17.fits                │
│ │                                                        │
│ └─ {dataset_id_2}/                                     │
│    └─ files/                                            │
│       └─ 20240116_100000_ngc2244.csv                    │
│                                                          │
│ File metadata stored:                                    │
│  • original-filename                                    │
│  • dataset-id                                           │
│  • file-hash                                            │
│  • content-type                                         │
└──────────────────────────────────────────────────────────┘
```

## Integration Summary

```
┌─────────────────────────────────────────────────────────────┐
│ UNIFIED INGESTION PIPELINE (Gaia & SDSS)                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  File Upload → Validation → Processing → DB Insert          │
│       ↓            ↓             ↓            ↓             │
│    (1)         (2)          (3)          (4)                │
│     │           │            │            │                 │
│     ├→ File stored in MinIO ←─┤─────────────→ Metadata DB  │
│     │           ↑                                           │
│     └─ SHA256 ──┴─ All tracked via ErrorReporter           │
│                                                              │
│ Each stage:                                                  │
│  ✓ Validates input                                         │
│  ✓ Logs errors (if any)                                    │
│  ✓ Provides audit trail                                    │
│  ✓ Maintains data integrity                                │
│  ✓ Stores for recovery/reprocessing                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Relationships

### FileValidator → ErrorReporter
- If file invalid → ErrorReporter.log_validation_error()
- Severity: ERROR
- Blocks further processing

### Adapter → ErrorReporter
- If parsing fails → ErrorReporter.log_parsing_error()
- Severity: ERROR or WARNING
- May allow skip_invalid to continue

### StorageService → DatasetMetadata
- File uploaded → storage_key returned
- storage_key stored in DatasetMetadata
- file_hash also stored for duplicate detection

### ErrorReporter → IngestionError (DB)
- Each error logged → new IngestionError record
- Linked to dataset_id for traceability
- Queryable via error API endpoints

---

## Deployment Architecture

```
Development Setup:
├─ FastAPI app (local)
├─ PostgreSQL (local)
└─ MinIO (docker container)

Production Setup:
├─ FastAPI app (container/VM)
├─ PostgreSQL (managed RDS)
└─ MinIO (S3 or MinIO Enterprise)
```

All configurations via environment variables - same code runs everywhere!
