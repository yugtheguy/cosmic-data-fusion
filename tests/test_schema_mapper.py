"""
Unit tests for SchemaMapper service.

Tests column detection logic with various header formats.
"""

import pytest
from app.services.schema_mapper import SchemaMapper, StandardColumn, ConfidenceLevel


class TestHeaderBasedDetection:
    """Test header-only column detection."""
    
    def test_exact_match_high_confidence(self):
        """Test exact matches have highest confidence."""
        mapper = SchemaMapper()
        suggestion = mapper.suggest_from_header(['ra', 'dec', 'magnitude'])
        
        # Should detect all three columns
        assert len(suggestion.mappings) == 3
        assert suggestion.mappings.get('ra') == StandardColumn.RA
        assert suggestion.mappings.get('dec') == StandardColumn.DEC
        assert suggestion.mappings.get('magnitude') == StandardColumn.MAGNITUDE
        
        # All should have high confidence
        for sug in suggestion.suggestions:
            assert sug.confidence >= 0.90
            assert sug.confidence_level == ConfidenceLevel.HIGH
    
    def test_gaia_columns(self):
        """Test Gaia DR3 column names."""
        mapper = SchemaMapper()
        columns = ['source_id', 'ra', 'dec', 'parallax', 'pmra', 'pmdec', 'phot_g_mean_mag']
        suggestion = mapper.suggest_from_header(columns)
        
        # Should detect all major columns
        assert suggestion.mappings.get('source_id') == StandardColumn.SOURCE_ID
        assert suggestion.mappings.get('ra') == StandardColumn.RA
        assert suggestion.mappings.get('dec') == StandardColumn.DEC
        assert suggestion.mappings.get('parallax') == StandardColumn.PARALLAX
        assert suggestion.mappings.get('pmra') == StandardColumn.PMRA
        assert suggestion.mappings.get('pmdec') == StandardColumn.PMDEC
        assert suggestion.mappings.get('phot_g_mean_mag') == StandardColumn.MAGNITUDE
    
    def test_sdss_columns(self):
        """Test SDSS column names."""
        mapper = SchemaMapper()
        columns = ['ra', 'dec', 'u', 'g', 'r', 'i', 'z', 'objid']
        suggestion = mapper.suggest_from_header(columns)
        
        # Should detect coordinates and at least one magnitude
        assert suggestion.mappings.get('ra') == StandardColumn.RA
        assert suggestion.mappings.get('dec') == StandardColumn.DEC
        # Should pick one of the photometric bands
        mag_columns = ['u', 'g', 'r', 'i', 'z']
        has_magnitude = any(suggestion.mappings.get(col) == StandardColumn.MAGNITUDE for col in mag_columns)
        assert has_magnitude
    
    def test_case_insensitive_matching(self):
        """Test case-insensitive column matching."""
        mapper = SchemaMapper()
        columns = ['RA', 'Dec', 'MAGNITUDE', 'SOURCE_ID']
        suggestion = mapper.suggest_from_header(columns)
        
        # Should match regardless of case
        assert len(suggestion.mappings) >= 3
    
    def test_variant_detection(self):
        """Test detection of column name variants."""
        mapper = SchemaMapper()
        columns = ['raj2000', 'decj2000', 'plx', 'gmag']
        suggestion = mapper.suggest_from_header(columns)
        
        # Should detect variants
        assert suggestion.mappings.get('raj2000') == StandardColumn.RA
        assert suggestion.mappings.get('decj2000') == StandardColumn.DEC
        assert suggestion.mappings.get('plx') == StandardColumn.PARALLAX
        assert suggestion.mappings.get('gmag') == StandardColumn.MAGNITUDE
    
    def test_ambiguous_columns(self):
        """Test handling of ambiguous column names."""
        mapper = SchemaMapper()
        columns = ['id', 'x', 'y', 'value']
        suggestion = mapper.suggest_from_header(columns)
        
        # Should have warnings for low confidence
        # Or unmapped columns
        assert len(suggestion.warnings) > 0 or len(suggestion.unmapped_columns) > 0
    
    def test_preserve_existing_mapping(self):
        """Test that existing mappings are preserved."""
        mapper = SchemaMapper()
        columns = ['custom_ra', 'custom_dec', 'custom_mag']
        existing = {
            'custom_ra': 'ra',
            'custom_dec': 'dec'
        }
        
        suggestion = mapper.suggest_from_header(columns, existing_mapping=existing)
        
        # Should preserve existing mappings
        assert suggestion.mappings.get('custom_ra') == StandardColumn.RA
        assert suggestion.mappings.get('custom_dec') == StandardColumn.DEC


class TestSampleBasedDetection:
    """Test sample data analysis for better detection."""
    
    @pytest.mark.skip(reason="To be implemented in Stage 3")
    def test_numeric_range_validation(self):
        """Test validation using numeric ranges (RA 0-360, Dec -90 to 90)."""
        pass
    
    @pytest.mark.skip(reason="To be implemented in Stage 3")
    def test_unit_detection(self):
        """Test detection of units from data ranges."""
        pass


class TestFilePreview:
    """Test file preview functionality."""
    
    @pytest.mark.skip(reason="To be implemented in Stage 3")
    def test_csv_file_preview(self):
        """Test previewing a CSV file."""
        pass
    
    @pytest.mark.skip(reason="To be implemented in Stage 3")
    def test_sample_size_limiting(self):
        """Test that sample size is respected."""
        pass


class TestMappingPersistence:
    """Test applying and persisting mappings."""
    
    def test_apply_mapping_to_dataset(self):
        """Test applying mapping to an existing dataset."""
        from app.database import SessionLocal
        from app.repository.dataset_repository import DatasetRepository
        from app.services.schema_mapper import SchemaMapper
        
        db = SessionLocal()
        try:
            # Create a test dataset
            repo = DatasetRepository(db)
            dataset = repo.create({
                'source_name': 'Test Mapping',
                'catalog_type': 'csv',
                'adapter_used': 'CSVAdapter',
                'record_count': 0
            })
            
            # Apply mapping
            mapper = SchemaMapper()
            mapping = {'ra': 'ra', 'dec': 'dec', 'mag': 'magnitude'}
            result = mapper.apply_mapping(
                dataset_id=str(dataset.dataset_id),
                mapping=mapping,
                db_session=db
            )
            
            assert result is True
            
            # Verify it was persisted
            updated = repo.get_by_id(str(dataset.dataset_id))
            assert updated.column_mappings is not None
            
            import json
            stored = json.loads(updated.column_mappings)
            assert stored == mapping
        finally:
            db.close()
    
    def test_confidence_threshold(self):
        """Test that low confidence mappings require explicit acceptance."""
        # This is currently a validation test - threshold is used for warnings
        # In Stage 5, we'll enhance to prevent auto-apply below threshold
        from app.services.schema_mapper import SchemaMapper
        mapper = SchemaMapper()
        
        # Low confidence detection should generate warnings
        columns = ['unknown_col1', 'unknown_col2']
        result = mapper.suggest_from_header(columns)
        
        # Should have warnings about missing required columns
        assert len(result.warnings) > 0
        assert any('RA' in w for w in result.warnings)
        assert any('Dec' in w for w in result.warnings)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
