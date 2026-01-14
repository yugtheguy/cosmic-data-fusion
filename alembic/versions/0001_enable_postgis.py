"""enable postgis

Revision ID: 0001_enable_postgis
Revises: 
Create Date: 2026-01-14 00:00:00.000000
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '0001_enable_postgis'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Enable PostGIS extension on PostgreSQL databases
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis;')


def downgrade():
    # Remove PostGIS extension (if desired)
    op.execute('DROP EXTENSION IF EXISTS postgis;')
