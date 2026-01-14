
import requests
import json

def test_gaia_cone_search(ra, dec, radius=0.01):
    url = "https://gea.esac.esa.int/tap-server/tap/sync"
    
    # ADQL Cone Search
    query = f"""
    SELECT TOP 1 source_id, ra, dec, phot_g_mean_mag, parallax, distance_gspphot 
    FROM gaiadr3.gaia_source 
    WHERE 1=CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {ra}, {dec}, {radius}))
    ORDER BY DISTANCE(POINT('ICRS', ra, dec), POINT('ICRS', {ra}, {dec})) ASC
    """
    
    params = {
        "REQUEST": "doQuery",
        "LANG": "ADQL",
        "FORMAT": "json",
        "QUERY": query
    }
    
    print(f"Querying Cone Search: {ra}, {dec}")
    try:
        response = requests.post(url, data=params, timeout=15)
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            if len(data.get("data", [])) > 0:
                print("Match Found:")
                print(json.dumps(data["data"][0], indent=2))
            else:
                print("No match found in radius.")
        except:
            print(response.text[:500])
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_gaia_cone_search(152.09328374612, 11.967812374819)
