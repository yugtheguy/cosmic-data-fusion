"""add_anomaly_overlap_matrix_view

Revision ID: 853e5a341132
Revises: add_discovery_views
Create Date: 2026-01-14 20:53:06.100731

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '853e5a341132'
down_revision = 'add_discovery_views'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create materialized view for anomaly overlap matrix."""
    
    # Create mv_anomaly_overlap_matrix view
    # This pre-computes overlaps between anomaly detection runs
    # Optimizes compare_runs() method by replacing Python set operations with SQL
    op.execute("""
        CREATE MATERIALIZED VIEW mv_anomaly_overlap_matrix AS
        WITH run_anomalies AS (
            -- Get all anomaly stars per run
            SELECT 
                run_id,
                ARRAY_AGG(star_id) as anomaly_star_ids,
                COUNT(*) as anomaly_count
            FROM discovery_results
            WHERE is_anomaly = 1  -- INTEGER column, not BOOLEAN
            GROUP BY run_id
        )
        SELECT 
            r1.run_id as run_1_id,
            r1.anomaly_count as run_1_count,
            r2.run_id as run_2_id,
            r2.anomaly_count as run_2_count,
            -- Count overlapping stars (set intersection)
            (
                SELECT COUNT(*) 
                FROM UNNEST(r1.anomaly_star_ids) star_id 
                WHERE star_id = ANY(r2.anomaly_star_ids)
            ) as overlap_count,
            -- Array of overlapping star IDs
            (
                SELECT ARRAY_AGG(star_id) 
                FROM UNNEST(r1.anomaly_star_ids) star_id 
                WHERE star_id = ANY(r2.anomaly_star_ids)
            ) as overlapping_star_ids,
            -- Stars unique to run 1
            (
                SELECT COUNT(*) 
                FROM UNNEST(r1.anomaly_star_ids) star_id 
                WHERE NOT (star_id = ANY(r2.anomaly_star_ids))
            ) as run_1_unique_count,
            -- Stars unique to run 2
            (
                SELECT COUNT(*) 
                FROM UNNEST(r2.anomaly_star_ids) star_id 
                WHERE NOT (star_id = ANY(r1.anomaly_star_ids))
            ) as run_2_unique_count,
            -- Jaccard similarity: |intersection| / |union|
            CASE 
                WHEN r1.anomaly_count + r2.anomaly_count = 0 THEN 0.0
                ELSE 
                    CAST(
                        (SELECT COUNT(*) FROM UNNEST(r1.anomaly_star_ids) star_id WHERE star_id = ANY(r2.anomaly_star_ids))
                        AS FLOAT
                    ) / CAST(
                        r1.anomaly_count + r2.anomaly_count - 
                        (SELECT COUNT(*) FROM UNNEST(r1.anomaly_star_ids) star_id WHERE star_id = ANY(r2.anomaly_star_ids))
                        AS FLOAT
                    )
            END as jaccard_similarity,
            NOW() as last_updated
        FROM 
            run_anomalies r1
        CROSS JOIN 
            run_anomalies r2
        WHERE 
            r1.run_id < r2.run_id  -- Only compare each pair once (avoid duplicates)
        ORDER BY 
            r1.run_id, r2.run_id;
    """)
    
    # Create unique index to enable CONCURRENTLY refresh
    op.execute("""
        CREATE UNIQUE INDEX idx_anomaly_overlap_pk 
        ON mv_anomaly_overlap_matrix (run_1_id, run_2_id);
    """)
    
    print("✅ Created mv_anomaly_overlap_matrix view")


def downgrade() -> None:
    """Drop anomaly overlap matrix view."""
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_anomaly_overlap_matrix CASCADE;")
    print("✅ Dropped mv_anomaly_overlap_matrix view")
