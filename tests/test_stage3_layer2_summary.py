"""
Stage 3: Layer 2 - Harmonization Verification
Tests cross-match, coordinate transformation, schema mapping, and unit conversion.
"""

import pytest
import subprocess
import sys
from sqlalchemy import text
from app.database import engine


class TestLayer2HarmonizationSummary:
    """Verify all Layer 2 harmonization components are working."""
    
    def test_cross_match_engine(self):
        """Verify cross-match engine with Union-Find algorithm works."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest",
             "tests/test_cross_match.py",
             "-v", "--tb=line"],
            capture_output=True,
            text=True
        )
        
        assert "9 passed" in result.stdout, f"Cross-match tests failed:\n{result.stdout}"
        print(f"✅ Cross-match engine: 9/9 tests passed")
    
    def test_schema_mapper(self):
        """Verify schema mapper with 40+ column variants works."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest",
             "tests/test_schema_mapper.py",
             "-v", "--tb=line"],
            capture_output=True,
            text=True
        )
        
        assert "13 passed" in result.stdout, f"Schema mapper tests failed:\n{result.stdout}"
        print(f"✅ Schema mapper: 13/13 tests passed")
    
    def test_ra_wraparound_handling(self):
        """Verify RA wraparound edge case handling."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest",
             "tests/test_ra_wraparound.py",
             "-v", "--tb=line"],
            capture_output=True,
            text=True
        )
        
        assert "6 passed" in result.stdout, f"RA wraparound tests failed:\n{result.stdout}"
        print(f"✅ RA wraparound: 6/6 tests passed")
    
    def test_magnitude_unit_converter(self):
        """Verify magnitude/flux conversions and band transformations."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest",
             "tests/test_unit_converter_magnitude.py",
             "-v", "--tb=line"],
            capture_output=True,
            text=True
        )
        
        assert "28 passed" in result.stdout, f"Magnitude converter tests failed:\n{result.stdout}"
        print(f"✅ Magnitude converter: 28/28 tests passed")
    
    def test_epoch_harmonizer(self):
        """Verify coordinate validation and epoch conversion."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest",
             "tests/test_epoch_converter.py",
             "-v", "--tb=line"],
            capture_output=True,
            text=True
        )
        
        assert "9 passed" in result.stdout, f"Epoch converter tests failed:\n{result.stdout}"
        print(f"✅ Epoch harmonizer: 9/9 tests passed")
    
    def test_cross_match_with_real_data(self):
        """Test cross-match engine with actual ingested data."""
        from app.services.harmonizer import CrossMatchService
        from app.database import SessionLocal
        from app.models import UnifiedStarCatalog
        
        db = SessionLocal()
        try:
            # Get all stars from database
            stars = db.query(UnifiedStarCatalog).all()
            
            if len(stars) < 2:
                print(f"  [SKIP] Need at least 2 stars for cross-match, found {len(stars)}")
                pytest.skip("Insufficient data for cross-match test")
                return
            
            print(f"\n  Running cross-match on {len(stars)} stars...")
            
            # Run cross-match with 1 arcsec threshold
            service = CrossMatchService(db)
            result = service.perform_cross_match(radius_arcsec=1.0)
            
            print(f"  Total stars: {result['total_stars']}")
            print(f"  Groups created: {result['groups_created']}")
            print(f"  Stars in groups: {result['stars_in_groups']}")
            print(f"  Isolated stars: {result['isolated_stars']}")
            print(f"  [OK] Cross-match executed successfully")
            
            assert result['total_stars'] > 0, "Should have processed stars"
            assert result['groups_created'] >= 0, "Groups count should be non-negative"
            
        finally:
            db.close()
    
    def test_coordinate_transformation_integration(self):
        """Verify coordinate transformations work with database records."""
        from app.services.epoch_converter import EpochHarmonizer
        from app.database import SessionLocal
        from app.models import UnifiedStarCatalog
        
        db = SessionLocal()
        try:
            # Get a sample star
            star = db.query(UnifiedStarCatalog).first()
            
            if not star:
                print("  [SKIP] No stars in database for coordinate transformation test")
                pytest.skip("No data in database")
                return
            
            print(f"\n  Testing coordinate transformations on star:")
            print(f"    Original: RA={star.ra_deg:.4f}°, Dec={star.dec_deg:.4f}°")
            print(f"    Magnitude: {star.brightness_mag:.2f}")
            
            # Test validation with database session
            harmonizer = EpochHarmonizer(db)
            
            # Validate coordinates
            is_valid, errors = harmonizer.validate_coordinates(star.ra_deg, star.dec_deg)
            assert is_valid, f"Coordinates should be valid: {errors}"
            
            # Run batch magnitude validation
            mag_report = harmonizer.validate_magnitude()
            assert mag_report['total_stars'] > 0, "Should have stars to validate"
            
            print(f"  [OK] Coordinate and magnitude validation passed")
            print(f"    Validated {mag_report['valid_stars']}/{mag_report['total_stars']} magnitudes")
            
        finally:
            db.close()
    
    def test_layer2_summary_stats(self):
        """Provide summary statistics for Layer 2."""
        print(f"\n{'='*60}")
        print("LAYER 2 HARMONIZATION VERIFICATION SUMMARY")
        print(f"{'='*60}")
        
        with engine.connect() as conn:
            # Count total records
            total_records = conn.execute(text("SELECT COUNT(*) FROM unified_star_catalog")).scalar()
            
            # Count fusion groups (cross-matched stars)
            fusion_groups = conn.execute(
                text("SELECT COUNT(DISTINCT fusion_group_id) FROM unified_star_catalog WHERE fusion_group_id IS NOT NULL")
            ).scalar()
            
            # Check coordinate ranges
            coord_stats = conn.execute(text("""
                SELECT 
                    MIN(ra_deg) as min_ra,
                    MAX(ra_deg) as max_ra,
                    MIN(dec_deg) as min_dec,
                    MAX(dec_deg) as max_dec,
                    MIN(brightness_mag) as min_mag,
                    MAX(brightness_mag) as max_mag
                FROM unified_star_catalog
            """)).fetchone()
            
            print(f"Total Records: {total_records}")
            print(f"Fusion Groups (Cross-Matched): {fusion_groups}")
            if coord_stats:
                print(f"RA Range: [{coord_stats[0]:.2f}°, {coord_stats[1]:.2f}°]")
                print(f"Dec Range: [{coord_stats[2]:.2f}°, {coord_stats[3]:.2f}°]")
                print(f"Magnitude Range: [{coord_stats[4]:.2f}, {coord_stats[5]:.2f}]")
            print(f"{'='*60}")
            
            # Verify coordinate integrity
            assert total_records > 0, "Should have records from Layer 1"
            if coord_stats:
                assert 0 <= coord_stats[0] <= 360, "RA min should be valid"
                assert 0 <= coord_stats[1] <= 360, "RA max should be valid"
                assert -90 <= coord_stats[2] <= 90, "Dec min should be valid"
                assert -90 <= coord_stats[3] <= 90, "Dec max should be valid"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
