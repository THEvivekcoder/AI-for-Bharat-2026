"""add_verification_tracking_to_schemes

Revision ID: b3b469f277d3
Revises: 0b7af4d608c9
Create Date: 2026-02-27 22:34:01.466163

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3b469f277d3'
down_revision = '0b7af4d608c9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add verification tracking columns to schemes table
    op.add_column('schemes', sa.Column('verification_status', sa.String(20), nullable=True, server_default='unverified'))
    op.add_column('schemes', sa.Column('verified_at', sa.DateTime(), nullable=True))
    op.add_column('schemes', sa.Column('verification_source', sa.String(255), nullable=True))


def downgrade() -> None:
    # Remove verification tracking columns from schemes table
    op.drop_column('schemes', 'verification_source')
    op.drop_column('schemes', 'verified_at')
    op.drop_column('schemes', 'verification_status')
