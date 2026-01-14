"""add composite indexes and materialized views

Revision ID: add_discovery_views
Revises: 957601232dc1
Create Date: 2026-01-14 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_discovery_views'
down_revision = '957601232dc1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add composite indexes and is_complete flag for discovery optimization."""
    
    # Add is_complete column to discovery_runs
    op.add_column('discovery_runs', 
        sa.Column('is_complete', sa.Boolean(), nullable=False, server_default='false')
    )
    
    # Create composite indexes for better query performance
    op.create_index(
        'idx_discovery_results_run_anomaly',
        'discovery_results',
        ['run_id', 'is_anomaly'],
        unique=False
    )
    
    op.create_index(
        'idx_discovery_results_run_cluster',
        'discovery_results',
        ['run_id', 'cluster_id'],
        unique=False
    )
    
    op.create_index(
        'idx_discovery_runs_type_created',
        'discovery_runs',
        ['run_type', sa.text('created_at DESC')],
        unique=False
    )
    
    # Create materialized view 1: Discovery Run Statistics
    op.execute("""
        CREATE MATERIALIZED VIEW mv_discovery_run_stats AS
        SELECT 
            dr.run_id,
            dr.run_type,
            dr.created_at,
            dr.total_stars,
            dr.parameters::text as parameters_json,
            -- Anomaly statistics
            COUNT(CASE WHEN dres.is_anomaly = 1 THEN 1 END) as anomaly_count,
            CAST(COUNT(CASE WHEN dres.is_anomaly = 1 THEN 1 END) AS FLOAT) / NULLIF(dr.total_stars, 0) * 100 as anomaly_percentage,
            MIN(CASE WHEN dres.is_anomaly = 1 THEN dres.anomaly_score END) as min_anomaly_score,
            MAX(CASE WHEN dres.is_anomaly = 1 THEN dres.anomaly_score END) as max_anomaly_score,
            AVG(CASE WHEN dres.is_anomaly = 1 THEN dres.anomaly_score END) as avg_anomaly_score,
            -- Cluster statistics
            COUNT(DISTINCT CASE WHEN dres.cluster_id >= 0 THEN dres.cluster_id END) as cluster_count,
            MAX(cluster_sizes.cluster_size) as max_cluster_size,
            MIN(cluster_sizes.cluster_size) as min_cluster_size,
            AVG(cluster_sizes.cluster_size) as avg_cluster_size,
            COUNT(CASE WHEN dres.cluster_id = -1 THEN 1 END) as noise_count
        FROM discovery_runs dr
        LEFT JOIN discovery_results dres ON dr.run_id = dres.run_id
        LEFT JOIN (
            SELECT run_id, cluster_id, COUNT(*) as cluster_size
            FROM discovery_results
            WHERE cluster_id >= 0
            GROUP BY run_id, cluster_id
        ) cluster_sizes ON dr.run_id = cluster_sizes.run_id
        WHERE dr.is_complete = true
        GROUP BY dr.run_id, dr.run_type, dr.created_at, dr.total_stars, dr.parameters::text
    """)
    
    # Create index on materialized view
    op.execute("""
        CREATE UNIQUE INDEX idx_mv_discovery_run_stats_run_id 
        ON mv_discovery_run_stats(run_id)
    """)
    
    op.execute("""
        CREATE INDEX idx_mv_discovery_run_stats_type_created 
        ON mv_discovery_run_stats(run_type, created_at DESC)
    """)
    
    # Create materialized view 2: Cluster Size Distribution
    op.execute("""
        CREATE MATERIALIZED VIEW mv_cluster_size_distribution AS
        SELECT 
            dr.run_id,
            dres.cluster_id,
            COUNT(*) as member_count,
            ARRAY_AGG(dres.star_id ORDER BY dres.star_id) as star_ids_list
        FROM discovery_runs dr
        JOIN discovery_results dres ON dr.run_id = dres.run_id
        WHERE dr.is_complete = true 
          AND dres.cluster_id >= 0
        GROUP BY dr.run_id, dres.cluster_id
    """)
    
    # Create index on cluster distribution view
    op.execute("""
        CREATE UNIQUE INDEX idx_mv_cluster_size_run_cluster 
        ON mv_cluster_size_distribution(run_id, cluster_id)
    """)
    
    # Create materialized view 3: Star Anomaly Frequency
    op.execute("""
        CREATE MATERIALIZED VIEW mv_star_anomaly_frequency AS
        SELECT 
            dres.star_id,
            COUNT(DISTINCT CASE WHEN dres.is_anomaly = 1 THEN dr.run_id END) as anomaly_run_count,
            COUNT(DISTINCT dr.run_id) as total_appearances,
            CAST(COUNT(DISTINCT CASE WHEN dres.is_anomaly = 1 THEN dr.run_id END) AS FLOAT) / 
                NULLIF(COUNT(DISTINCT dr.run_id), 0) * 100 as anomaly_percentage,
            AVG(CASE WHEN dres.is_anomaly = 1 THEN dres.anomaly_score END) as mean_anomaly_score,
            BOOL_OR(CASE WHEN dres.is_anomaly = 1 AND dr.created_at > CURRENT_DATE - INTERVAL '30 days' 
                    THEN true ELSE false END) as recent_anomaly_flag,
            MAX(CASE WHEN dres.is_anomaly = 1 THEN dr.run_id END) as last_anomaly_run_id
        FROM discovery_results dres
        JOIN discovery_runs dr ON dres.run_id = dr.run_id
        WHERE dr.is_complete = true
        GROUP BY dres.star_id
    """)
    
    # Create index on star frequency view
    op.execute("""
        CREATE UNIQUE INDEX idx_mv_star_anomaly_frequency_star_id 
        ON mv_star_anomaly_frequency(star_id)
    """)
    
    op.execute("""
        CREATE INDEX idx_mv_star_anomaly_frequency_count 
        ON mv_star_anomaly_frequency(anomaly_run_count DESC)
    """)


def downgrade() -> None:
    """Remove materialized views, indexes, and is_complete column."""
    
    # Drop materialized views
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_star_anomaly_frequency CASCADE")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_cluster_size_distribution CASCADE")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_discovery_run_stats CASCADE")
    
    # Drop composite indexes
    op.drop_index('idx_discovery_runs_type_created', table_name='discovery_runs')
    op.drop_index('idx_discovery_results_run_cluster', table_name='discovery_results')
    op.drop_index('idx_discovery_results_run_anomaly', table_name='discovery_results')
    
    # Drop is_complete column
    op.drop_column('discovery_runs', 'is_complete')
