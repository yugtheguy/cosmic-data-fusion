"""Quick test to verify materialized views were created"""
from sqlalchemy import create_engine, text

engine = create_engine('postgresql+psycopg2://postgres:Lokesh%406789@localhost:5432/cosmic')
with engine.connect() as conn:
    result = conn.execute(text("SELECT matviewname FROM pg_matviews WHERE schemaname = 'public'"))
    print('\nMaterialized Views Created:')
    for row in result:
        print(f'  ✅ {row[0]}')
    
    # Check indexes
    result2 = conn.execute(text("""
        SELECT indexname FROM pg_indexes 
        WHERE schemaname = 'public' 
        AND tablename IN ('discovery_runs', 'discovery_results')
        AND indexname LIKE 'idx_%'
    """))
    print('\nComposite Indexes Created:')
    for row in result2:
        print(f'  ✅ {row[0]}')
