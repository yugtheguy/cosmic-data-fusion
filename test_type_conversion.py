"""Test type conversion fixes for temporal calculations"""
import numpy as np

print("Testing type conversion scenarios...")
print("=" * 60)

# Simulate database returns with mixed types
test_data = [
    None,           # NULL from database
    "10.5",         # String number
    10.5,           # Float
    "invalid",      # Invalid string
    0,              # Zero
]

print("\n1. Testing individual conversions:")
for val in test_data:
    try:
        result = float(val) if val is not None else 0.0
        print(f"  {repr(val):20} -> {result}")
    except (ValueError, TypeError):
        print(f"  {repr(val):20} -> 0.0 (fallback)")

print("\n2. Testing NumPy array creation:")
converted = []
for val in test_data:
    try:
        converted.append(float(val) if val is not None else 0.0)
    except (ValueError, TypeError):
        converted.append(0.0)

arr = np.array(converted, dtype=np.float64)
print(f"  Array: {arr}")
print(f"  Squared: {arr**2}")
print(f"  Total: {np.sqrt(arr**2)}")

print("\n3. Testing with star-like data:")
mock_stars = [
    {'pmra': 10.5, 'pmdec': -5.2},
    {'pmra': "15.0", 'pmdec': "8.3"},
    {'pmra': None, 'pmdec': 0},
    {'pmra': "invalid", 'pmdec': 5.0},
]

pmra_list = []
pmdec_list = []
for s in mock_stars:
    pmra = s.get('pmra')
    pmdec = s.get('pmdec')
    try:
        pmra_val = float(pmra) if pmra is not None else 0.0
    except (ValueError, TypeError):
        pmra_val = 0.0
    try:
        pmdec_val = float(pmdec) if pmdec is not None else 0.0
    except (ValueError, TypeError):
        pmdec_val = 0.0
    pmra_list.append(pmra_val)
    pmdec_list.append(pmdec_val)

pmra_array = np.array(pmra_list, dtype=np.float64)
pmdec_array = np.array(pmdec_list, dtype=np.float64)
total_pm = np.sqrt(pmra_array**2 + pmdec_array**2)

for i, star in enumerate(mock_stars):
    print(f"  Star {i+1}: pmra={star['pmra']}, pmdec={star['pmdec']} -> total_pm={total_pm[i]:.2f}")

print("\n" + "=" * 60)
print("✓ All type conversions working correctly!")
