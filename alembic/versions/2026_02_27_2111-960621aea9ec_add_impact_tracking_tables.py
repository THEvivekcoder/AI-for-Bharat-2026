"""add_impact_tracking_tables

Revision ID: 960621aea9ec
Revises: a1b2c3d4e5f6
Create Date: 2026-02-27 21:11:02.284575

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '960621aea9ec'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create interactions table
    op.create_table(
        'interactions',
        sa.Column('interaction_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_data', JSONB, nullable=True),
        sa.Column('language', sa.String(10), nullable=True),
        sa.Column('timestamp', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create indexes for interactions table
    op.create_index('idx_interactions_user_id', 'interactions', ['user_id'])
    op.create_index('idx_interactions_event_type', 'interactions', ['event_type'])
    op.create_index('idx_interactions_language', 'interactions', ['language'])
    op.create_index('idx_interactions_timestamp', 'interactions', ['timestamp'])
    op.create_index('idx_interactions_user_timestamp', 'interactions', ['user_id', 'timestamp'])
    op.create_index('idx_interactions_event_type_timestamp', 'interactions', ['event_type', 'timestamp'])
    
    # Create outcomes table
    op.create_table(
        'outcomes',
        sa.Column('outcome_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True),
        sa.Column('outcome_type', sa.String(50), nullable=False),
        sa.Column('outcome_data', JSONB, nullable=True),
        sa.Column('timestamp', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create indexes for outcomes table
    op.create_index('idx_outcomes_user_id', 'outcomes', ['user_id'])
    op.create_index('idx_outcomes_outcome_type', 'outcomes', ['outcome_type'])
    op.create_index('idx_outcomes_timestamp', 'outcomes', ['timestamp'])
    op.create_index('idx_outcomes_user_timestamp', 'outcomes', ['user_id', 'timestamp'])
    op.create_index('idx_outcomes_outcome_type_timestamp', 'outcomes', ['outcome_type', 'timestamp'])


def downgrade() -> None:
    # Drop outcomes table and its indexes
    op.drop_index('idx_outcomes_outcome_type_timestamp', 'outcomes')
    op.drop_index('idx_outcomes_user_timestamp', 'outcomes')
    op.drop_index('idx_outcomes_timestamp', 'outcomes')
    op.drop_index('idx_outcomes_outcome_type', 'outcomes')
    op.drop_index('idx_outcomes_user_id', 'outcomes')
    op.drop_table('outcomes')
    
    # Drop interactions table and its indexes
    op.drop_index('idx_interactions_event_type_timestamp', 'interactions')
    op.drop_index('idx_interactions_user_timestamp', 'interactions')
    op.drop_index('idx_interactions_timestamp', 'interactions')
    op.drop_index('idx_interactions_language', 'interactions')
    op.drop_index('idx_interactions_event_type', 'interactions')
    op.drop_index('idx_interactions_user_id', 'interactions')
    op.drop_table('interactions')
