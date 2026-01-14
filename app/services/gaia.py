
import logging
from typing import Optional, Dict, Any
import warnings

# Suppress astroquery warnings about configuration
warnings.filterwarnings("ignore", module="astroquery")

try:
    from astroquery.gaia import Gaia
    import astropy.units as u
    from astropy.coordinates import SkyCoord
except ImportError:
    raise ImportError("astroquery not installed. Please run 'pip install astroquery'")

logger = logging.getLogger(__name__)

class GaiaService:
    """
    Service to interact with the ESA Gaia Archive via Astroquery.
    Robust handling of TAP protocol, ADQL, and connection retries.
    """
    
    @classmethod
    def fetch_star_data(cls, source_id: str, ra: Optional[float] = None, dec: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch real-time data for a star from Gaia DR3.
        """
        try:
            # 1. Primary Query: Exact ID
            # We use launch_job for full control over ADQL
            query_id = f"""
            SELECT TOP 1
                source_id, ra, dec, phot_g_mean_mag, 
                parallax, parallax_error, radial_velocity,
                teff_gspphot, distance_gspphot
            FROM gaiadr3.gaia_source 
            WHERE source_id = {source_id}
            """
            
            logger.info(f"Querying Gaia (Astroquery) for source_id: {source_id}")
            job = Gaia.launch_job(query_id)
            results = job.get_results()
            
            if len(results) > 0:
                logger.info("Match found by ID.")
                return cls._parse_row(results[0])
            
            # 2. Fallback Query: Spatial Cone Search
            if ra is not None and dec is not None:
                logger.info(f"Direct ID match failed. Attempting cone search at {ra}, {dec}")
                
                # Use SkyCoord for convenient coordinate object
                coord = SkyCoord(ra=ra, dec=dec, unit=(u.degree, u.degree), frame='icrs')
                
                # Perform an async cone search with 10 arcseconds radius
                # search_async returns a job, we get_results() to get the table
                job_cone = Gaia.cone_search_async(coord, radius=10 * u.arcsec)
                results_cone = job_cone.get_results()
                
            # Check if critical data is missing (common for bright stars in Gaia)
            # If parallax is None or Masked, try SIMBAD fallback
            parsed_data = cls._parse_row(results[0]) if len(results) > 0 else (
                cls._parse_row(results_cone[0]) if 'results_cone' in locals() and len(results_cone) > 0 else None
            )

            if parsed_data and (parsed_data.get("parallax") is None or parsed_data.get("distance") is None):
                logger.info("Gaia data missing parallax/distance (bright star?). Attempting SIMBAD fallback.")
                simbad_data = cls._fetch_simbad_data(ra, dec)
                if simbad_data:
                    # Merge Simbad data (prefer Simbad for distance/plx if Gaia is missing)
                    if parsed_data.get("parallax") is None:
                        parsed_data["parallax"] = simbad_data.get("parallax")
                    if parsed_data.get("distance") is None:
                        parsed_data["distance"] = simbad_data.get("distance")
                    if parsed_data.get("mag") is None:
                        parsed_data["mag"] = simbad_data.get("mag")
                    parsed_data["data_source"] = "Gaia DR3 + SIMBAD"

            return parsed_data

        except Exception as e:
            logger.error(f"Astroquery error: {e}")
            return None

    @classmethod
    def _fetch_simbad_data(cls, ra: float, dec: float) -> Optional[Dict[str, Any]]:
        """Fetch basic data from SIMBAD for bright stars."""
        try:
            from astroquery.simbad import Simbad
            from astropy.coordinates import SkyCoord
            import astropy.units as u
            
            # Add fields we need
            custom_simbad = Simbad()
            custom_simbad.add_votable_fields('plx', 'plx_error', 'flux(V)', 'distance')
            
            coord = SkyCoord(ra=ra, dec=dec, unit=(u.degree, u.degree), frame='icrs')
            result_table = custom_simbad.query_region(coord, radius=1 * u.arcmin)
            
            if result_table and len(result_table) > 0:
                row = result_table[0]
                # Convert distance from some unit? Simbad often doesn't give direct distance, 
                # but gives Parallax (plx_value).
                
                # Helper to find column ignoring case
                def get_col(name):
                    for col in row.colnames:
                        if col.lower() == name.lower():
                            return row[col]
                    return None

                plx = get_col('PLX_VALUE')
                # Handle masked values
                if hasattr(plx, 'mask') and plx.mask:
                    plx = None
                
                mag = get_col('FLUX_V')
                if hasattr(mag, 'mask') and mag.mask:
                    mag = None

                dist = None
                if plx:
                    try:
                        plx = float(plx)
                        if plx > 0:
                            dist = 1000.0 / plx
                    except:
                        plx = None

                return {
                    "parallax": plx,
                    "distance": dist,
                    "mag": float(mag) if mag is not None else None
                }
            return None
        except Exception as e:
            logger.error(f"Simbad fallback error: {e}")
            return None

    @classmethod
    def _parse_row(cls, row) -> Dict[str, Any]:
        """
        Parse Astropy Table row into dictionary.
        Handles masked values and different column names from Cone Search.
        """
        # Helper to get value safely, handling masked arrays
        def get_val(key):
            if key not in row.colnames:
                return None
            val = row[key]
            # Check if masked
            if hasattr(val, 'mask') and val.mask:
                return None
            try:
                # Handle generic numpy scaler
                if hasattr(val, 'item'):
                    return val.item()
                return float(val)
            except:
                return str(val)

        return {
            "source_id": str(row['source_id']),
            "ra": get_val('ra'),
            "dec": get_val('dec'),
            "mag": get_val('phot_g_mean_mag'),
            "parallax": get_val('parallax'),
            "parallax_error": get_val('parallax_error'),
            "radial_velocity": get_val('radial_velocity'),
            "teff": get_val('teff_gspphot'),
            "distance": get_val('distance_gspphot') or get_val('dist')
        }
