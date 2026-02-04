from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord
import astropy.units as u

PLEIADES_RA = 56.75
PLEIADES_DEC = 24.1167
SEARCH_RADIUS = 0.5
LIMIT_PER_CATALOG = 1

def debug_catalog(catalog_id, name):
    print(f"\nFetching {name}...")
    Vizier.ROW_LIMIT = LIMIT_PER_CATALOG
    coord = SkyCoord(ra=PLEIADES_RA, dec=PLEIADES_DEC, unit=(u.deg, u.deg), frame='icrs')
    result = Vizier.query_region(coord, radius=SEARCH_RADIUS*u.deg, catalog=catalog_id)
    if result:
        print(f"Columns: {result[0].colnames}")
        print(f"First Row: {result[0][0]}")
        for col in result[0].colnames:
            val = result[0][0][col]
            print(f"  {col}: {val} (type: {type(val)})")
    else:
        print("No result")

debug_catalog("II/246/out", "2MASS")
debug_catalog("I/259/tyc2", "Tycho-2")
