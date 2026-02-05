"""Check FITS file column types"""
from astropy.io import fits
from astropy.table import Table

with fits.open('app/data/2mass_sample.fits') as hdul:
    table = Table(hdul[1].data)
    print(f"Columns: {len(table.colnames)}")
    for col in table.colnames[:10]:
        sample_val = table[col][0]
        print(f"  {col}: {type(sample_val).__name__} = {sample_val}")
