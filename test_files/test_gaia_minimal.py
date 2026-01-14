
import requests

url = "https://gea.esac.esa.int/tap-server/tap/sync"

def run_query(label, query):
    print(f"\n--- {label} ---")
    print(f"Query: {query}")
    params = {
        "REQUEST": "doQuery",
        "LANG": "ADQL",
        "FORMAT": "json",
        "QUERY": query
    }
    try:
        response = requests.post(url, data=params, timeout=15)
        if response.status_code == 200:
            print("SUCCESS")
            # print(response.text[:100])
        else:
            print(f"FAILED ({response.status_code})")
            print(response.text.split('\n')[0][:200]) # Print first line of error
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    ra = 56.87129384761
    dec = 24.105237841923
    
    # 1. Simplest possible query
    run_query("Basis", "SELECT TOP 1 source_id FROM gaiadr3.gaia_source")
    
    # 2. Add Geometry
    q_geo = f"SELECT TOP 1 source_id FROM gaiadr3.gaia_source WHERE 1=CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {ra}, {dec}, 0.01))"
    run_query("Geometry", q_geo)
    
    # 3. Full original query
    q_full = f"SELECT TOP 1 source_id FROM gaiadr3.gaia_source WHERE 1=CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {ra}, {dec}, 0.01)) ORDER BY DISTANCE(POINT('ICRS', ra, dec), POINT('ICRS', {ra}, {dec})) ASC"
    run_query("Full", q_full)
