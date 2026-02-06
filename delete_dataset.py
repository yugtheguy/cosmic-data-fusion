import sqlite3

conn = sqlite3.connect('cosmic_data_fusion.db')
cursor = conn.cursor()

dataset_id = 'e59fed94-7a74-4b36-9757-4441cf01a6a9'

# Delete from unified_star_catalog first (foreign key constraint)
cursor.execute('DELETE FROM unified_star_catalog WHERE dataset_id = ?', (dataset_id,))
deleted_stars = cursor.rowcount
print(f"Deleted {deleted_stars} stars from unified_star_catalog")

# Delete from dataset_metadata
cursor.execute('DELETE FROM dataset_metadata WHERE dataset_id = ?', (dataset_id,))
deleted_metadata = cursor.rowcount
print(f"Deleted {deleted_metadata} dataset metadata records")

# Commit the changes
conn.commit()
print("Dataset deleted successfully!")

conn.close()
