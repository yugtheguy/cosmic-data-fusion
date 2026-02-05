"""Test FITS file preview functionality"""
import sys
sys.path.insert(0, '.')

from app.services.adapters.fits_adapter import FITSAdapter

try:
    adapter = FITSAdapter()
    result = adapter.preview("app/data/2mass_sample.fits", limit=5)
    
    print(f"✓ Preview successful!")
    print(f"  Source columns: {len(result.get('source_columns', []))}")
    print(f"  Samples: {len(result.get('samples', []))}")
    print(f"  Valid: {result.get('validation_summary', {}).get('valid', 0)}")
    print(f"  Invalid: {result.get('validation_summary', {}).get('invalid', 0)}")
    
    if result.get('sample_errors'):
        print(f"\n⚠ Errors found:")
        for error in result['sample_errors'][:3]:
            print(f"  - {error}")
            
except Exception as e:
    print(f"✗ Preview failed: {e}")
    import traceback
    traceback.print_exc()
