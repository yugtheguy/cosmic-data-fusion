"""
Stage 1: Adapter Registry Unit Tests
Tests core registry functionality: initialization, registration, retrieval, listing
"""

import pytest
from app.services.adapter_registry import (
    AdapterRegistry,
    AdapterInfo,
    AdapterDetectionError,
    registry as global_registry
)
from app.services.adapters.base_adapter import BaseAdapter
from app.services.adapters.gaia_adapter import GaiaAdapter
from app.services.adapters.sdss_adapter import SDSSAdapter
from app.services.adapters.fits_adapter import FITSAdapter
from app.services.adapters.csv_adapter import CSVAdapter


class TestRegistryCreation:
    """Test registry initialization and global singleton."""
    
    def test_registry_initialization(self):
        """Test creating a new registry instance."""
        reg = AdapterRegistry()
        assert reg is not None
        assert len(reg.list_adapters()) == 0
    
    def test_global_registry_exists(self):
        """Test that global singleton registry exists and has pre-registered adapters."""
        assert global_registry is not None
        adapters = global_registry.list_adapters()
        assert len(adapters) == 4
        
        # Verify all built-in adapters are registered
        adapter_names = {adapter.name for adapter in adapters}
        assert adapter_names == {'gaia', 'sdss', 'fits', 'csv'}


class TestAdapterRegistration:
    """Test adapter registration functionality."""
    
    def test_register_adapter_success(self):
        """Test successful adapter registration."""
        reg = AdapterRegistry()
        
        reg.register(
            name='test_adapter',
            adapter_class=CSVAdapter,
            file_patterns=['*.test'],
            description='Test adapter',
            version='1.0.0'
        )
        
        adapters = reg.list_adapters()
        assert len(adapters) == 1
        assert adapters[0].name == 'test_adapter'
        assert adapters[0].adapter_class == CSVAdapter
        assert adapters[0].file_patterns == ['*.test']
        assert adapters[0].description == 'Test adapter'
        assert adapters[0].version == '1.0.0'
    
    def test_register_duplicate_adapter_raises_error(self):
        """Test that registering duplicate adapter name raises ValueError."""
        reg = AdapterRegistry()
        
        reg.register(
            name='duplicate',
            adapter_class=CSVAdapter,
            file_patterns=['*.csv'],
            description='First adapter'
        )
        
        with pytest.raises(ValueError, match="Adapter 'duplicate' is already registered"):
            reg.register(
                name='duplicate',
                adapter_class=GaiaAdapter,
                file_patterns=['*.csv'],
                description='Second adapter'
            )
    
    def test_register_invalid_adapter_class(self):
        """Test that registering non-BaseAdapter class raises ValueError."""
        reg = AdapterRegistry()
        
        class NotAnAdapter:
            pass
        
        with pytest.raises(ValueError, match="must inherit from BaseAdapter"):
            reg.register(
                name='invalid',
                adapter_class=NotAnAdapter,
                file_patterns=['*.txt'],
                description='Invalid adapter'
            )


class TestAdapterRetrieval:
    """Test adapter retrieval functionality."""
    
    def test_get_adapter_success(self):
        """Test successful adapter retrieval by name."""
        reg = AdapterRegistry()
        reg.register(
            name='test',
            adapter_class=CSVAdapter,
            file_patterns=['*.csv'],
            description='Test'
        )
        
        adapter_class = reg.get_adapter('test')
        assert adapter_class == CSVAdapter
    
    def test_get_adapter_not_found(self):
        """Test that getting non-existent adapter raises KeyError."""
        reg = AdapterRegistry()
        
        with pytest.raises(KeyError, match="No adapter registered with name 'nonexistent'"):
            reg.get_adapter('nonexistent')
    
    def test_get_global_adapters(self):
        """Test retrieving all pre-registered adapters from global registry."""
        assert global_registry.get_adapter('gaia') == GaiaAdapter
        assert global_registry.get_adapter('sdss') == SDSSAdapter
        assert global_registry.get_adapter('fits') == FITSAdapter
        assert global_registry.get_adapter('csv') == CSVAdapter


class TestListAdapters:
    """Test adapter listing functionality."""
    
    def test_list_empty_registry(self):
        """Test listing adapters from empty registry."""
        reg = AdapterRegistry()
        adapters = reg.list_adapters()
        assert len(adapters) == 0
        assert adapters == []
    
    def test_list_multiple_adapters(self):
        """Test listing multiple registered adapters."""
        reg = AdapterRegistry()
        
        reg.register('adapter1', CSVAdapter, ['*.csv'], 'First')
        reg.register('adapter2', GaiaAdapter, ['*.gaia'], 'Second')
        reg.register('adapter3', SDSSAdapter, ['*.sdss'], 'Third')
        
        adapters = reg.list_adapters()
        assert len(adapters) == 3
        
        names = {adapter.name for adapter in adapters}
        assert names == {'adapter1', 'adapter2', 'adapter3'}
    
    def test_list_returns_adapter_info_objects(self):
        """Test that list_adapters returns AdapterInfo objects with all fields."""
        reg = AdapterRegistry()
        reg.register(
            name='test',
            adapter_class=CSVAdapter,
            file_patterns=['*.csv', '*.tsv'],
            description='Test adapter',
            version='2.0.0'
        )
        
        adapters = reg.list_adapters()
        assert len(adapters) == 1
        
        info = adapters[0]
        assert isinstance(info, AdapterInfo)
        assert info.name == 'test'
        assert info.adapter_class == CSVAdapter
        assert info.file_patterns == ['*.csv', '*.tsv']
        assert info.description == 'Test adapter'
        assert info.version == '2.0.0'


class TestAdapterInfo:
    """Test AdapterInfo dataclass."""
    
    def test_adapter_info_creation(self):
        """Test creating AdapterInfo with valid data."""
        info = AdapterInfo(
            name='test',
            adapter_class=CSVAdapter,
            file_patterns=['*.csv'],
            description='Test',
            version='1.0.0'
        )
        
        assert info.name == 'test'
        assert info.adapter_class == CSVAdapter
        assert info.file_patterns == ['*.csv']
        assert info.description == 'Test'
        assert info.version == '1.0.0'
    
    def test_adapter_info_invalid_class(self):
        """Test that AdapterInfo raises error for invalid adapter class."""
        class NotAnAdapter:
            pass
        
        with pytest.raises(ValueError, match="must inherit from BaseAdapter"):
            AdapterInfo(
                name='invalid',
                adapter_class=NotAnAdapter,
                file_patterns=['*.txt'],
                description='Invalid',
                version='1.0.0'
            )
