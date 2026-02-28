"""add_scheme_tables

Revision ID: 66f1615298ee
Revises: c19837e07e4f
Create Date: 2026-02-27 13:38:15.963680

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '66f1615298ee'
down_revision = 'c19837e07e4f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create schemes table
    op.create_table(
        'schemes',
        sa.Column('scheme_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('category', sa.String(50), nullable=False, index=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('benefits', JSONB, nullable=True),
        sa.Column('eligibility_criteria', JSONB, nullable=False),
        sa.Column('required_documents', JSONB, nullable=True),
        sa.Column('application_process', JSONB, nullable=True),
        sa.Column('application_url', sa.String(500), nullable=True),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('state', sa.String(50), nullable=True, index=True),
        sa.Column('last_updated', sa.DateTime, nullable=True),
        sa.Column('source_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    
    # Create scheme_translations table
    op.create_table(
        'scheme_translations',
        sa.Column('translation_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('scheme_id', UUID(as_uuid=True), nullable=False),
        sa.Column('language', sa.String(10), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('benefits', JSONB, nullable=True),
        sa.ForeignKeyConstraint(['scheme_id'], ['schemes.scheme_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('scheme_id', 'language', name='uq_scheme_language')
    )


def downgrade() -> None:
    op.drop_table('scheme_translations')
    op.drop_table('schemes')
