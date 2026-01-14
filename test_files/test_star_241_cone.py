
import requests
import json

def test_gaia_cone_search(ra, dec, radius):
    url = "https://gea.esac.esa.int/tap-server/tap/sync"
    
    # Single line query to avoid parsing issues
    query = f"SELECT TOP 5 source_id, ra, dec, phot_g_mean_mag, distance_gspphot FROM gaiadr3.gaia_source WHERE 1=CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {ra}, {dec}, {radius})) ORDER BY DISTANCE(POINT('ICRS', ra, dec), POINT('ICRS', {ra}, {dec})) ASC"
    
    params = {
        "REQUEST": "doQuery",
        "LANG": "ADQL",
        "FORMAT": "json",
        "QUERY": query
    }
    
    print(f"\nQuerying Cone Search: Radius={radius} deg")
    try:
        response = requests.post(url, data=params, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if len(data.get("data", [])) > 0:
                    print(f"Match Found! ({len(data['data'])} stars)")
                    print(json.dumps(data["data"][0], indent=2))
                else:
                    print("No match found.")
            except:
                print("Error parsing JSON")
        else:
            print("Server Error:")
            print(response.text[:200])
            
    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    ra = 56.87129384761
    dec = 24.105237841923
    
    # 5 arcsec (~0.0014 deg)
    test_gaia_cone_search(ra, dec, 0.0014)
    
    # 10 arcsec (~0.0028 deg)
    test_gaia_cone_search(ra, dec, 0.0028)
