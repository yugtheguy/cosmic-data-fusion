"""Test animation endpoint."""
import requests
import json

# Test the animation endpoint
try:
    response = requests.get(
        "http://localhost:8000/temporal/animation",
        params={
            "start_epoch": -1000,
            "end_epoch": 2000,
            "frame_count": 10,
            "limit": 20
        }
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nAnimation Summary:")
        print(f"  Start Epoch: {data['start_epoch']}")
        print(f"  End Epoch: {data['end_epoch']}")
        print(f"  Frame Count: {data['frame_count']}")
        print(f"  Stars per Frame: {data['stars_per_frame']}")
        print(f"  Encoding: {data['metadata'].get('encoding', 'N/A')}")
        print(f"  Time per Frame: {data['metadata'].get('time_per_frame', 'N/A')} years")
        
        if data['frames']:
            print(f"\n  First Frame (epoch {data['frames'][0]['epoch']}):")
            for pos in data['frames'][0]['positions'][:3]:
                print(f"    Star {pos['id']}: RA={pos.get('ra', 'delta')}, Dec={pos.get('dec', 'delta')}")
            
            if len(data['frames']) > 1:
                print(f"\n  Second Frame (delta encoded, epoch {data['frames'][1]['epoch']}):")
                for pos in data['frames'][1]['positions'][:3]:
                    if 'dra' in pos:
                        print(f"    Star {pos['id']}: dRA={pos['dra']}, dDec={pos['ddec']}")
                    else:
                        print(f"    Star {pos['id']}: RA={pos.get('ra')}")
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
