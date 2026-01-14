
import requests
import json

def test_cone_maxrec():
    url = "https://gea.esac.esa.int/tap-server/tap/sync"
    ra = 56.87129384761
    dec = 24.105237841923
    radius = 0.005 # ~18 arcsec
    
    # Query without TOP
    query = f"SELECT source_id, distance_gspphot FROM gaiadr3.gaia_source WHERE 1=CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {ra}, {dec}, {radius}))"
    
    params = {
        "REQUEST": "doQuery",
        "LANG": "ADQL",
        "FORMAT": "json",
        "QUERY": query,
        "MAXREC": "5"
    }
    
    print(f"Query: {query}")
    try:
        response = requests.post(url, data=params, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("SUCCESS")
            try:
                data = response.json()
                print(json.dumps(data, indent=2))
            except:
                print(response.text[:200])
        else:
            print("FAILED")
            print(response.text[:500])
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_cone_maxrec()
