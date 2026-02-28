"""add_last_updated_to_mandi_price_and_job_posting

Revision ID: 0b7af4d608c9
Revises: 960621aea9ec
Create Date: 2026-02-27 22:30:37.961081

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0b7af4d608c9'
down_revision = '960621aea9ec'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add last_updated column to mandi_prices table (if it exists)
    # This migration assumes the table was created in a previous migration
    try:
        op.add_column('mandi_prices', sa.Column('last_updated', sa.DateTime(), nullable=True))
    except Exception:
        pass  # Table might not exist yet
    
    # Add last_updated column to job_postings table (if it exists)
    try:
        op.add_column('job_postings', sa.Column('last_updated', sa.DateTime(), nullable=True))
    except Exception:
        pass  # Table might not exist yet


def downgrade() -> None:
    # Remove last_updated column from job_postings table
    try:
        op.drop_column('job_postings', 'last_updated')
    except Exception:
        pass
    
    # Remove last_updated column from mandi_prices table
    try:
        op.drop_column('mandi_prices', 'last_updated')
    except Exception:
        pass
