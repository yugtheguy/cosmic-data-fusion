"""Quick verification that all materialized views were created."""

from app.database import engine
import sqlalchemy as sa

with engine.connect() as conn:
    print("All Materialized Views:")
    result = conn.execute(sa.text(
        "SELECT matviewname FROM pg_matviews WHERE schemaname = 'public' ORDER BY matviewname;"
    ))
    views = [row[0] for row in result]
    for view in views:
        print(f"  ✅ {view}")
    
    print(f"\n✅ Total: {len(views)} materialized views created")

