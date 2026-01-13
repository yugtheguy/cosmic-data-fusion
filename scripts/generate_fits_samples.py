"""
Generate sample FITS files for testing the FITS adapter.

Creates realistic astronomical FITS binary tables with:
- Hipparcos-style data
- 2MASS-style data
- Edge cases for validation testing
"""

import numpy as np
from astropy.io import fits
from astropy.table import Table
from pathlib import Path


def create_hipparcos_sample():
    """
    Create sample Hipparcos-style FITS file.
    
    Columns: HIP (ID), RAJ2000, DEJ2000, Vmag, Parallax, pmRA, pmDE
    """
    n_records = 50
    
    # Generate realistic data
    data = {
        'HIP': np.arange(1, n_records + 1),
        'RAJ2000': np.random.uniform(0, 360, n_records),
        'DEJ2000': np.random.uniform(-90, 90, n_records),
        'Vmag': np.random.uniform(3, 12, n_records),
        'Parallax': np.random.uniform(1, 100, n_records),  # mas
        'pmRA': np.random.uniform(-50, 50, n_records),  # mas/yr
        'pmDE': np.random.uniform(-50, 50, n_records),  # mas/yr
    }
    
    # Create table
    table = Table(data)
    
    # Create primary HDU (empty)
    primary_hdu = fits.PrimaryHDU()
    primary_hdu.header['ORIGIN'] = 'Hipparcos Sample'
    primary_hdu.header['TELESCOP'] = 'Hipparcos'
    primary_hdu.header['RADESYS'] = 'ICRS'
    primary_hdu.header['EQUINOX'] = 2000.0
    
    # Create binary table HDU
    table_hdu = fits.BinTableHDU(table, name='STARS')
    table_hdu.header['EXTNAME'] = 'STARS'
    
    # Create HDU list
    hdul = fits.HDUList([primary_hdu, table_hdu])
    
    return hdul


def create_2mass_sample():
    """
    Create sample 2MASS-style FITS file.
    
    Columns: designation, ra, dec, j_m (Jmag), h_m (Hmag), k_m (Kmag)
    """
    n_records = 50
    
    # Generate realistic data
    data = {
        'designation': [f'2MASS J{i:08d}' for i in range(n_records)],
        'ra': np.random.uniform(0, 360, n_records),
        'dec': np.random.uniform(-90, 90, n_records),
        'j_m': np.random.uniform(10, 16, n_records),
        'h_m': np.random.uniform(9, 15, n_records),
        'k_m': np.random.uniform(9, 15, n_records),
    }
    
    # Create table
    table = Table(data)
    
    # Create primary HDU (empty)
    primary_hdu = fits.PrimaryHDU()
    primary_hdu.header['ORIGIN'] = '2MASS Sample'
    primary_hdu.header['TELESCOP'] = '2MASS'
    primary_hdu.header['RADESYS'] = 'ICRS'
    primary_hdu.header['DATE-OBS'] = '2000-01-01'
    
    # Create binary table HDU
    table_hdu = fits.BinTableHDU(table, name='CATALOG')
    
    # Create HDU list
    hdul = fits.HDUList([primary_hdu, table_hdu])
    
    return hdul


def create_edge_cases_sample():
    """
    Create FITS file with edge cases for validation testing.
    
    Includes:
    - Valid records
    - Missing magnitude
    - Negative parallax
    - Out-of-range coordinates
    - NaN values
    """
    data = {
        'source_id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'RA': [45.0, 180.0, 359.9, -10.0, 400.0, 56.7, 120.3, np.nan, 200.0, 90.0],
        'DEC': [30.0, -45.0, 85.0, 100.0, 0.0, 24.1, -89.5, 45.0, np.nan, 0.0],
        'Gmag': [10.5, 12.3, np.nan, 8.9, 15.2, 6.5, 40.0, 11.1, 9.8, -10.0],
        'Parallax': [50.0, 10.5, 5.2, -2.0, 0.0, 25.3, 1500.0, 8.7, 12.4, 3.1],
    }
    
    # Create table
    table = Table(data)
    
    # Create primary HDU
    primary_hdu = fits.PrimaryHDU()
    primary_hdu.header['ORIGIN'] = 'Edge Cases Sample'
    primary_hdu.header['RADESYS'] = 'ICRS'
    
    # Create binary table HDU
    table_hdu = fits.BinTableHDU(table, name='TESTDATA')
    
    # Create HDU list
    hdul = fits.HDUList([primary_hdu, table_hdu])
    
    return hdul


def create_multi_extension_sample():
    """
    Create multi-extension FITS file for testing extension selection.
    """
    # Primary HDU (empty)
    primary_hdu = fits.PrimaryHDU()
    primary_hdu.header['ORIGIN'] = 'Multi-Extension Sample'
    
    # Extension 1: Metadata
    meta_data = {
        'key': ['CATALOG', 'VERSION', 'DATE'],
        'value': ['TEST', '1.0', '2026-01-13']
    }
    meta_table = Table(meta_data)
    meta_hdu = fits.BinTableHDU(meta_table, name='METADATA')
    
    # Extension 2: Stars (actual data)
    star_data = {
        'ID': np.arange(1, 21),
        'RA_ICRS': np.random.uniform(0, 360, 20),
        'DEC_ICRS': np.random.uniform(-90, 90, 20),
        'MAG_V': np.random.uniform(8, 14, 20),
    }
    star_table = Table(star_data)
    star_hdu = fits.BinTableHDU(star_table, name='STARS')
    
    # Extension 3: More stars
    star_data2 = {
        'objid': np.arange(21, 31),
        'ra': np.random.uniform(0, 360, 10),
        'dec': np.random.uniform(-90, 90, 10),
        'magnitude': np.random.uniform(10, 16, 10),
    }
    star_table2 = Table(star_data2)
    star_hdu2 = fits.BinTableHDU(star_table2, name='FAINT_STARS')
    
    # Create HDU list
    hdul = fits.HDUList([primary_hdu, meta_hdu, star_hdu, star_hdu2])
    
    return hdul


def main():
    """Generate all sample FITS files."""
    output_dir = Path('app/data')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Generating sample FITS files...")
    
    # Hipparcos sample
    print("  Creating hipparcos_sample.fits...")
    hdul = create_hipparcos_sample()
    hdul.writeto(output_dir / 'hipparcos_sample.fits', overwrite=True)
    print(f"    ✓ Created with {len(hdul[1].data)} records")
    
    # 2MASS sample
    print("  Creating 2mass_sample.fits...")
    hdul = create_2mass_sample()
    hdul.writeto(output_dir / '2mass_sample.fits', overwrite=True)
    print(f"    ✓ Created with {len(hdul[1].data)} records")
    
    # Edge cases
    print("  Creating fits_edge_cases.fits...")
    hdul = create_edge_cases_sample()
    hdul.writeto(output_dir / 'fits_edge_cases.fits', overwrite=True)
    print(f"    ✓ Created with {len(hdul[1].data)} records")
    
    # Multi-extension
    print("  Creating fits_multi_extension.fits...")
    hdul = create_multi_extension_sample()
    hdul.writeto(output_dir / 'fits_multi_extension.fits', overwrite=True)
    print(f"    ✓ Created with {len(hdul)} HDUs")
    
    print("\n✅ All sample FITS files generated successfully!")
    print(f"   Location: {output_dir.absolute()}")


if __name__ == '__main__':
    main()
