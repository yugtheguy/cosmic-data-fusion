"""
Cluster Visualization Script for COSMIC Data Fusion

Creates a scatter plot showing star clusters detected by DBSCAN algorithm.
Each cluster is shown in a different color, with noise points in gray.

Usage: python visualize_clusters.py
"""

import requests
import matplotlib.pyplot as plt
import numpy as np

# API base URL
BASE_URL = "http://localhost:8001"

def fetch_cluster_data(eps=0.5, min_samples=5):
    """Fetch clustering results from the API."""
    print(f"🔍 Fetching clusters (eps={eps}, min_samples={min_samples})...")
    
    response = requests.post(
        f"{BASE_URL}/ai/clusters",
        json={"eps": eps, "min_samples": min_samples}
    )
    response.raise_for_status()
    return response.json()

def fetch_star_positions():
    """Fetch all star positions from the visualization endpoint."""
    print("⭐ Fetching star positions...")
    
    response = requests.get(f"{BASE_URL}/visualize/sky?limit=10000")
    response.raise_for_status()
    return response.json()

def fetch_all_stars_from_search():
    """Fetch all stars using the search endpoint to get IDs."""
    print("⭐ Fetching all star data with IDs...")
    
    response = requests.get(
        f"{BASE_URL}/search/box",
        params={"ra_min": 0, "ra_max": 359.99, "dec_min": -90, "dec_max": 90, "limit": 10000}
    )
    response.raise_for_status()
    return response.json()

def create_cluster_plot(cluster_data, star_data):
    """Create a scatter plot of clustered stars."""
    
    # Build a mapping of star_id -> (ra, dec, mag)
    star_map = {}
    for star in star_data["stars"]:
        star_map[star["id"]] = {
            "ra": star["ra_deg"],
            "dec": star["dec_deg"],
            "mag": star["brightness_mag"]
        }
    
    # Set up the figure with dark background for astronomy feel
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Color palette for clusters
    colors = plt.cm.Set1(np.linspace(0, 1, 10))
    
    n_clusters = cluster_data["n_clusters"]
    clusters = cluster_data["clusters"]
    cluster_stats = cluster_data["cluster_stats"]
    
    print(f"\n📊 Plotting {n_clusters} clusters + noise...")
    
    # Plot each cluster
    legend_handles = []
    cluster_idx = 0
    
    for cluster_name, star_ids in clusters.items():
        # Get positions for stars in this cluster
        ras = []
        decs = []
        mags = []
        
        for sid in star_ids:
            if sid in star_map:
                ras.append(star_map[sid]["ra"])
                decs.append(star_map[sid]["dec"])
                mags.append(star_map[sid]["mag"])
        
        if not ras:
            continue
            
        # Convert magnitude to marker size (brighter = larger)
        sizes = [max(5, 50 - m*3) for m in mags]
        
        if cluster_name == "noise":
            # Noise points in gray, smaller
            scatter = ax.scatter(
                ras, decs, 
                c='gray', 
                s=[s*0.5 for s in sizes],
                alpha=0.3, 
                label=f'Noise ({len(star_ids)} stars)',
                marker='.'
            )
        else:
            # Cluster points in vibrant colors
            color = colors[cluster_idx % len(colors)]
            stats = cluster_stats[cluster_name]
            
            scatter = ax.scatter(
                ras, decs,
                c=[color],
                s=sizes,
                alpha=0.8,
                label=f'{cluster_name} ({stats["count"]} stars)',
                edgecolors='white',
                linewidths=0.5
            )
            
            # Mark cluster center with an X
            ax.scatter(
                stats["mean_ra"], stats["mean_dec"],
                c=[color],
                s=200,
                marker='X',
                edgecolors='white',
                linewidths=2
            )
            
            cluster_idx += 1
    
    # Customize the plot
    ax.set_xlabel('Right Ascension (degrees)', fontsize=12, color='white')
    ax.set_ylabel('Declination (degrees)', fontsize=12, color='white')
    ax.set_title(
        f'🔭 COSMIC Data Fusion - Star Clusters (DBSCAN)\n'
        f'{n_clusters} clusters found, {cluster_data["n_noise"]} noise points',
        fontsize=14, fontweight='bold', color='cyan'
    )
    
    # Set axis limits for full sky
    ax.set_xlim(0, 360)
    ax.set_ylim(-90, 90)
    
    # Add grid
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Add legend
    ax.legend(
        loc='upper right',
        fontsize=9,
        framealpha=0.7,
        facecolor='black'
    )
    
    # Add parameter info
    params = cluster_data["parameters"]
    ax.text(
        0.02, 0.02,
        f'Parameters: eps={params["eps"]}, min_samples={params["min_samples"]}\n'
        f'Features: {", ".join(params["features_used"])}',
        transform=ax.transAxes,
        fontsize=9,
        color='yellow',
        verticalalignment='bottom',
        bbox=dict(boxstyle='round', facecolor='black', alpha=0.7)
    )
    
    plt.tight_layout()
    return fig

def main():
    print("=" * 60)
    print("🌌 COSMIC Data Fusion - Cluster Visualization")
    print("=" * 60)
    
    try:
        # Fetch data from API
        cluster_data = fetch_cluster_data(eps=0.5, min_samples=5)
        star_data = fetch_all_stars_from_search()
        
        print(f"\n✅ Found {cluster_data['n_clusters']} clusters")
        print(f"✅ Total stars: {cluster_data['total_stars']}")
        print(f"✅ Noise points: {cluster_data['n_noise']}")
        
        # Create visualization
        fig = create_cluster_plot(cluster_data, star_data)
        
        # Save the plot
        output_file = "cluster_visualization.png"
        fig.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='black')
        print(f"\n💾 Saved plot to: {output_file}")
        
        # Show the plot
        print("\n🖼️  Displaying plot...")
        plt.show()
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API server!")
        print("   Make sure the server is running on http://localhost:8001")
        print("   Start with: uvicorn app.main:app --port 8001")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise

if __name__ == "__main__":
    main()
