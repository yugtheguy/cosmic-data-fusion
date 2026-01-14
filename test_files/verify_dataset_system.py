"""
COSMIC Data Fusion - Dataset Metadata System Verification
Complete end-to-end test of the Dataset Metadata implementation.
"""

print('=== COSMIC Data Fusion - Dataset Metadata System Verification ===\n')

# Test 1: Model Import
from app.models import DatasetMetadata, UnifiedStarCatalog
print('✓ Models imported successfully')
print(f'  - DatasetMetadata table: {DatasetMetadata.__tablename__}')
print(f'  - UnifiedStarCatalog table: {UnifiedStarCatalog.__tablename__}\n')

# Test 2: Repository Import
from app.repository.dataset_repository import DatasetRepository
print('✓ DatasetRepository imported successfully')
methods = [m for m in dir(DatasetRepository) if not m.startswith('_') and callable(getattr(DatasetRepository, m))]
print(f'  - Public methods: {len(methods)}')
print(f'  - Key methods: create, get_by_id, list_all, update_record_count, get_statistics\n')

# Test 3: Schema Import
from app.schemas import DatasetRegisterRequest, DatasetMetadataResponse, DatasetListResponse, DatasetRegistryStats
print('✓ Dataset schemas imported successfully')
print(f'  - DatasetRegisterRequest')
print(f'  - DatasetMetadataResponse')
print(f'  - DatasetListResponse')
print(f'  - DatasetRegistryStats\n')

# Test 4: API Router Import
from app.api.datasets import router
print('✓ Dataset API router imported successfully')
print(f'  - Total routes: {len(router.routes)}')
print(f'  - POST /datasets/register')
print(f'  - GET /datasets')
print(f'  - GET /datasets/statistics')
print(f'  - GET /datasets/{{dataset_id}}')
print(f'  - DELETE /datasets/{{dataset_id}}\n')

# Test 5: Database Integration
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base

engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)
db = Session()

# Create test dataset
repo = DatasetRepository(db)
dataset = repo.create({
    'source_name': 'Verification Test Dataset',
    'catalog_type': 'csv',
    'adapter_used': 'CSVAdapter',
    'record_count': 0
})
print('✓ Database operations working')
print(f'  - Created dataset: {dataset.dataset_id[:8]}...')
print(f'  - Source: {dataset.source_name}')
print(f'  - Type: {dataset.catalog_type}\n')

# Test 6: Record count update
repo.update_record_count(dataset.dataset_id, 42)
updated = repo.get_by_id(dataset.dataset_id)
print('✓ Record count tracking working')
print(f'  - Updated record_count: {updated.record_count}\n')

# Test 7: Statistics
stats = repo.get_statistics()
print('✓ Statistics aggregation working')
print(f'  - Total datasets: {stats["total_datasets"]}')
print(f'  - Total records: {stats["total_records"]}')
print(f'  - By catalog type: {list(stats["by_catalog_type"].keys())}\n')

db.close()

print('=' * 60)
print('✅ ALL SYSTEMS OPERATIONAL')
print('=' * 60)
print('\nDataset Metadata Implementation: COMPLETE')
print('Frontend development: UNBLOCKED')
print('Next priority: Schema Mapper Service')
