"""
Script to analyze database statistics for NL query thresholds
"""
from app.database import SessionLocal
from app.models import UnifiedStarCatalog
from sqlalchemy import func
import json

db = SessionLocal()

# Get magnitude statistics
mag_stats = db.query(
    func.min(UnifiedStarCatalog.brightness_mag),
    func.max(UnifiedStarCatalog.brightness_mag),
    func.avg(UnifiedStarCatalog.brightness_mag)
).first()

# Get proper motion statistics
pm_stats = db.query(
    func.min(UnifiedStarCatalog.total_pm),
    func.max(UnifiedStarCatalog.total_pm),
    func.avg(UnifiedStarCatalog.total_pm)
).filter(UnifiedStarCatalog.total_pm.isnot(None)).first()

# Get percentiles for magnitude
mag_percentiles = {}
for p in [1, 10, 25, 50, 75, 90, 99]:
    result = db.execute(f"""
        SELECT brightness_mag 
        FROM unified_star_catalog 
        WHERE brightness_mag IS NOT NULL
        ORDER BY brightness_mag 
        LIMIT 1 OFFSET (SELECT COUNT(*) * {p}/100 FROM unified_star_catalog WHERE brightness_mag IS NOT NULL)
    """).first()
    if result:
        mag_percentiles[f'p{p}'] = result[0]

# Get percentiles for proper motion
pm_percentiles = {}
for p in [1, 10, 25, 50, 75, 90, 99]:
    result = db.execute(f"""
        SELECT total_pm 
        FROM unified_star_catalog 
        WHERE total_pm IS NOT NULL
        ORDER BY total_pm DESC
        LIMIT 1 OFFSET (SELECT COUNT(*) * {p}/100 FROM unified_star_catalog WHERE total_pm IS NOT NULL)
    """).first()
    if result:
        pm_percentiles[f'p{p}'] = result[0]

stats = {
    "magnitude": {
        "min": float(mag_stats[0]) if mag_stats[0] else None,
        "max": float(mag_stats[1]) if mag_stats[1] else None,
        "avg": float(mag_stats[2]) if mag_stats[2] else None,
        "percentiles": {k: float(v) for k, v in mag_percentiles.items()}
    },
    "proper_motion": {
        "min": float(pm_stats[0]) if pm_stats[0] else None,
        "max": float(pm_stats[1]) if pm_stats[1] else None,
        "avg": float(pm_stats[2]) if pm_stats[2] else None,
        "percentiles": {k: float(v) for k, v in pm_percentiles.items()}
    }
}

print(json.dumps(stats, indent=2))

db.close()
