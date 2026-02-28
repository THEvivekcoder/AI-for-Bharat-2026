"""add_health_facilities_table

Revision ID: a1b2c3d4e5f6
Revises: 1825c4aef2aa
Create Date: 2026-02-27 20:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '1825c4aef2aa'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create health_facilities table
    op.create_table(
        'health_facilities',
        sa.Column('facility_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('facility_type', sa.String(50), nullable=False, index=True),
        sa.Column('state', sa.String(50), nullable=False, index=True),
        sa.Column('district', sa.String(50), nullable=False, index=True),
        sa.Column('address', sa.Text, nullable=True),
        sa.Column('latitude', sa.Numeric(10, 8), nullable=True),
        sa.Column('longitude', sa.Numeric(11, 8), nullable=True),
        sa.Column('contact', sa.String(100), nullable=True),
        sa.Column('services', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    
    # Create index on location for spatial queries
    op.create_index('idx_health_facilities_location', 'health_facilities', ['state', 'district'])


def downgrade() -> None:
    op.drop_index('idx_health_facilities_location', table_name='health_facilities')
    op.drop_table('health_facilities')
