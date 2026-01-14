
from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord
import astropy.units as u
import warnings

warnings.filterwarnings("ignore")

def test_simbad():
    print("Testing Simbad query...")
    try:
        ra = 56.87129384761
        dec = 24.105237841923
        
        custom_simbad = Simbad()
        # Add fields we need
        custom_simbad.add_votable_fields('plx', 'plx_error', 'flux(V)', 'distance')
        
        print(f"Querying region RA={ra}, Dec={dec}...")
        coord = SkyCoord(ra=ra, dec=dec, unit=(u.degree, u.degree), frame='icrs')
        result_table = custom_simbad.query_region(coord, radius=1 * u.arcmin)
        
        if result_table and len(result_table) > 0:
            print("Match Found:")
            row = result_table[0]
            print(f"Columns: {result_table.colnames}")
            print(row)
            
            plx = row['PLX_VALUE'] if 'PLX_VALUE' in row.colnames and not row['PLX_VALUE'] is None else None
            print(f"Parallax Value: {plx}")
        else:
            print("No match found.")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simbad()
