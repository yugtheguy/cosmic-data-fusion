
import warnings
warnings.filterwarnings("ignore")
from astroquery.gaia import Gaia
import astropy.units as u
from astropy.coordinates import SkyCoord

def debug_star_241():
    # Coordinates for Star 241
    ra = 56.87129384761
    dec = 24.105237841923
    
    print(f"Querying Gaia Cone Search at RA={ra}, Dec={dec}...")
    
    coord = SkyCoord(ra=ra, dec=dec, unit=(u.degree, u.degree), frame='icrs')
    job = Gaia.cone_search_async(coord, radius=10 * u.arcsec)
    results = job.get_results()
    
    with open("debug_output.txt", "w") as f:
        if len(results) > 0:
            row = results[0]
            f.write("\n--- Match Found ---\n")
            f.write(f"Source ID: {row['source_id']}\n")
            f.write(f"Magnitude: {row['phot_g_mean_mag']}\n")
            
            # Check parallax
            plx = row['parallax']
            f.write(f"Parallax: {plx} (Masked: {getattr(plx, 'mask', False)})\n")
            
            # Check distance fields
            if 'distance_gspphot' in row.colnames:
                dist = row['distance_gspphot']
                f.write(f"Distance (gspphot): {dist} (Masked: {getattr(dist, 'mask', False)})\n")
            else:
                f.write("Distance (gspphot) column NOT present\n")
        else:
            f.write("No match found in Gaia.\n")
            
    print("Debug output written to debug_output.txt")

if __name__ == "__main__":
    debug_star_241()
