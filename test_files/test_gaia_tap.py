
import requests
import json

def test_gaia_query(source_id):
    url = "https://gea.esac.esa.int/tap-server/tap/sync"
    
    query = f"SELECT source_id, ra, dec, phot_g_mean_mag FROM gaiadr3.gaia_source WHERE source_id = {source_id}"
    
    params = {
        "REQUEST": "doQuery",
        "LANG": "ADQL",
        "FORMAT": "json",
        "QUERY": query
    }
    
    print(f"Querying: {query}")
    try:
        response = requests.post(url, data=params, timeout=15)
        print(f"Status Code: {response.status_code}")
        print("Response Headers:", response.headers)
        
        try:
            data = response.json()
            print("Response JSON:")
            print(json.dumps(data, indent=2))
        except json.JSONDecodeError:
            print("Response Text (Not JSON):")
            print(response.text[:500])
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Test with the ID from the user's DB
    test_gaia_query(3864972938605115776)
