
try:
    from astroquery.gaia import Gaia
    import astropy.units as u
    from astropy.coordinates import SkyCoord
    print("Astroquery imported successfully.")
except ImportError:
    print("Astroquery NOT found.")
    exit(1)

def test_astroquery():
    print("Launching test job...")
    # Simple query to check connection
    query = "SELECT TOP 1 source_id FROM gaiadr3.gaia_source"
    try:
        job = Gaia.launch_job(query)
        r = job.get_results()
        print("Success! Retrieved row:")
        print(r)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_astroquery()
