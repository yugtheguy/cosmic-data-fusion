"""add_discovery_timeline_view

Revision ID: 7f88b0e7c0ad
Revises: 853e5a341132
Create Date: 2026-01-14 20:58:12.999292

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7f88b0e7c0ad'
down_revision = '853e5a341132'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create materialized view for discovery timeline (weekly/monthly trends)."""
    
    # Create mv_discovery_timeline view
    # This provides weekly and monthly aggregations for trend analysis
    # Designed for dashboard visualizations and historical analysis
    op.execute("""
        CREATE MATERIALIZED VIEW mv_discovery_timeline AS
        WITH daily_stats AS (
            -- Daily aggregations per run type
            SELECT 
                DATE_TRUNC('day', created_at) as day,
                run_type,
                COUNT(*) as runs_count,
                SUM(CASE WHEN is_complete THEN 1 ELSE 0 END) as completed_runs,
                SUM(total_stars) as total_stars_analyzed
            FROM discovery_runs
            GROUP BY DATE_TRUNC('day', created_at), run_type
        )
        SELECT 
            -- Weekly aggregations
            DATE_TRUNC('week', day) as period_start,
            run_type,
            SUM(runs_count) as total_runs,
            SUM(completed_runs) as completed_runs,
            SUM(total_stars_analyzed) as total_stars_analyzed,
            'week' as period_type
        FROM daily_stats
        GROUP BY DATE_TRUNC('week', day), run_type
        
        UNION ALL
        
        SELECT 
            -- Monthly aggregations
            DATE_TRUNC('month', day) as period_start,
            run_type,
            SUM(runs_count) as total_runs,
            SUM(completed_runs) as completed_runs,
            SUM(total_stars_analyzed) as total_stars_analyzed,
            'month' as period_type
        FROM daily_stats
        GROUP BY DATE_TRUNC('month', day), run_type
        
        ORDER BY period_start DESC, run_type;
    """)
    
    # Create index to enable CONCURRENTLY refresh
    # Note: composite index on (period_start, run_type, period_type) for uniqueness
    op.execute("""
        CREATE UNIQUE INDEX idx_discovery_timeline_pk 
        ON mv_discovery_timeline (period_start, run_type, period_type);
    """)
    
    print("✅ Created mv_discovery_timeline view")


def downgrade() -> None:
    """Drop discovery timeline view."""
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_discovery_timeline CASCADE;")
    print("✅ Dropped mv_discovery_timeline view")
