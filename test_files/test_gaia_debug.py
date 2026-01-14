
import requests

def debug_query():
    url = "https://gea.esac.esa.int/tap-server/tap/sync"
    
    # Try without TOP first to see if that's the keyword causing issues
    # Or keep it simple
    query = "SELECT source_id FROM gaiadr3.gaia_source" 
    # Use maxrec to limit without TOP keyword if needed
    
    params = {
        "REQUEST": "doQuery",
        "LANG": "ADQL",
        "FORMAT": "json",
        "QUERY": query,
        "MAXREC": "1"  # Alternative to TOP
    }
    
    print(f"Query: {query}")
    try:
        response = requests.post(url, data=params, timeout=15)
        print(f"Status: {response.status_code}")
        
        # Print the raw text to see the XML error details
        print("Response Text:")
        print(response.text)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_query()
