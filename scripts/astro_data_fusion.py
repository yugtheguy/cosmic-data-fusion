"""
Astronomical Data Fusion Engine
Demonstrates harmonizing incompatible astronomical datasets using astropy and pandas.
"""

import pandas as pd
import numpy as np
from astropy.coordinates import SkyCoord, Galactic
from astropy import units as u

# =============================================================================
# Step 1: Simulate Two Incompatible Datasets
# =============================================================================

# Dataset A: Visible Light observations (Equatorial coordinates, Flux in Jansky)
dataset_a = {
    'Source_ID': ['VIS-001', 'VIS-002', 'VIS-003', 'VIS-004'],
    'Right_Ascension': [83.633, 201.365, 10.684, 266.417],  # degrees
    'Declination': [22.014, -43.019, 41.269, -29.008],      # degrees
    'Flux_Jy': [1.0e-3, 5.5e-4, 2.3e-3, 8.7e-4]            # Jansky
}

# Dataset B: X-Ray observations (Galactic coordinates, AB Magnitude)
dataset_b = {
    'Object_Name': ['XR-Alpha', 'XR-Beta', 'XR-Gamma'],
    'Galactic_Longitude': [120.5, 45.2, 330.8],   # degrees (l)
    'Galactic_Latitude': [25.3, -10.7, 55.1],     # degrees (b)
    'AB_Magnitude': [18.5, 20.1, 16.8]
}

print("=" * 70)
print("ASTRONOMICAL DATA FUSION ENGINE")
print("=" * 70)

print("\n--- Original Dataset A (Visible Light) ---")
df_a = pd.DataFrame(dataset_a)
print(df_a.to_string(index=False))

print("\n--- Original Dataset B (X-Ray) ---")
df_b = pd.DataFrame(dataset_b)
print(df_b.to_string(index=False))

# =============================================================================
# Step 2: Harmonization Functions
# =============================================================================

def convert_galactic_to_equatorial(gal_lon, gal_lat):
    """
    Convert Galactic coordinates (l, b) to Equatorial coordinates (RA, Dec).
    
    Parameters:
        gal_lon: Galactic longitude in degrees
        gal_lat: Galactic latitude in degrees
    
    Returns:
        tuple: (Right Ascension, Declination) in degrees
    """
    # Create SkyCoord object with Galactic frame
    galactic_coord = SkyCoord(
        l=gal_lon * u.degree,
        b=gal_lat * u.degree,
        frame='galactic'
    )
    
    # Transform to ICRS (Equatorial) frame
    equatorial_coord = galactic_coord.icrs
    
    return equatorial_coord.ra.degree, equatorial_coord.dec.degree


def convert_flux_to_ab_magnitude(flux_jy):
    """
    Convert Flux in Jansky to AB Magnitude.
    
    The AB magnitude system is defined such that:
    AB_mag = -2.5 * log10(flux_Jy) + 8.90
    
    Parameters:
        flux_jy: Flux in Jansky (can be array-like)
    
    Returns:
        AB Magnitude value(s)
    """
    # Using astropy units for proper conversion
    flux = np.array(flux_jy) * u.Jy
    
    # AB magnitude zero point: 3631 Jy
    # AB_mag = -2.5 * log10(F_nu / 3631 Jy)
    ab_mag = -2.5 * np.log10(flux.value / 3631.0)
    
    return ab_mag


def harmonize_dataset_a(df):
    """
    Harmonize Dataset A: Convert Flux to AB Magnitude.
    Coordinates are already in Equatorial (RA/Dec).
    """
    df_harmonized = df.copy()
    
    # Convert Flux (Jansky) to AB Magnitude
    df_harmonized['AB_Magnitude'] = convert_flux_to_ab_magnitude(df['Flux_Jy'])
    
    # Drop the original Flux column
    df_harmonized = df_harmonized.drop(columns=['Flux_Jy'])
    
    # Add source type for tracking
    df_harmonized['Source_Type'] = 'Visible_Light'
    
    return df_harmonized


def harmonize_dataset_b(df):
    """
    Harmonize Dataset B: Convert Galactic to Equatorial coordinates
    and standardize column names.
    """
    df_harmonized = df.copy()
    
    # Convert Galactic coordinates to Equatorial
    ra_list = []
    dec_list = []
    
    for _, row in df.iterrows():
        ra, dec = convert_galactic_to_equatorial(
            row['Galactic_Longitude'],
            row['Galactic_Latitude']
        )
        ra_list.append(ra)
        dec_list.append(dec)
    
    df_harmonized['Right_Ascension'] = ra_list
    df_harmonized['Declination'] = dec_list
    
    # Standardize column names: rename Object_Name to Source_ID
    df_harmonized = df_harmonized.rename(columns={'Object_Name': 'Source_ID'})
    
    # Drop original Galactic coordinate columns
    df_harmonized = df_harmonized.drop(columns=['Galactic_Longitude', 'Galactic_Latitude'])
    
    # Add source type for tracking
    df_harmonized['Source_Type'] = 'X-Ray'
    
    return df_harmonized


# =============================================================================
# Step 3: Apply Harmonization and Merge
# =============================================================================

print("\n" + "=" * 70)
print("HARMONIZATION PROCESS")
print("=" * 70)

# Harmonize both datasets
print("\n[1] Converting Dataset A flux values to AB Magnitude...")
df_a_harmonized = harmonize_dataset_a(df_a)

print("[2] Converting Dataset B Galactic coordinates to Equatorial (RA/Dec)...")
print("[3] Standardizing Dataset B column names (Object_Name -> Source_ID)...")
df_b_harmonized = harmonize_dataset_b(df_b)

print("\n--- Harmonized Dataset A ---")
print(df_a_harmonized.to_string(index=False))

print("\n--- Harmonized Dataset B ---")
print(df_b_harmonized.to_string(index=False))

# Merge into a single DataFrame
# Reorder columns for consistency
column_order = ['Source_ID', 'Right_Ascension', 'Declination', 'AB_Magnitude', 'Source_Type']

df_a_harmonized = df_a_harmonized[column_order]
df_b_harmonized = df_b_harmonized[column_order]

# Concatenate the harmonized datasets
fused_df = pd.concat([df_a_harmonized, df_b_harmonized], ignore_index=True)

# =============================================================================
# Final Output
# =============================================================================

print("\n" + "=" * 70)
print("FUSED ASTRONOMICAL DATA TABLE")
print("=" * 70)
print("\nAll sources now share:")
print("  • Coordinate System: Equatorial (RA/Dec in degrees)")
print("  • Brightness Unit: AB Magnitude")
print("  • Identifier Column: Source_ID")

print("\n" + "-" * 70)
print(fused_df.to_string(index=False))
print("-" * 70)

print(f"\nTotal sources in fused catalog: {len(fused_df)}")
print(f"  - From Visible Light: {len(fused_df[fused_df['Source_Type'] == 'Visible_Light'])}")
print(f"  - From X-Ray: {len(fused_df[fused_df['Source_Type'] == 'X-Ray'])}")

# Optional: Save to CSV
fused_df.to_csv('fused_astronomical_catalog.csv', index=False)
print("\n[✓] Fused catalog saved to 'fused_astronomical_catalog.csv'")
