"""Add security fields

Revision ID: add_security_fields
Revises: 
Create Date: 2026-02-27 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_security_fields'
down_revision = None  # Update this to point to your latest migration
branch_labels = None
depends_on = None


def upgrade():
    """Add security-related fields and tables"""
    
    # Add role and phone_number_hash to users table
    op.add_column('users', sa.Column('role', sa.String(20), nullable=False, server_default='user'))
    op.add_column('users', sa.Column('phone_number_hash', sa.String(64), nullable=True))
    
    # Create index on phone_number_hash
    op.create_index('ix_users_phone_number_hash', 'users', ['phone_number_hash'], unique=True)
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('log_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_role', sa.String(20), nullable=True),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', sa.String(100), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('endpoint', sa.String(200), nullable=True),
        sa.Column('success', sa.String(10), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
    )
    
    # Create indexes on audit_logs
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_event_type', 'audit_logs', ['event_type'])


def downgrade():
    """Remove security-related fields and tables"""
    
    # Drop audit_logs table
    op.drop_index('ix_audit_logs_event_type', 'audit_logs')
    op.drop_index('ix_audit_logs_user_id', 'audit_logs')
    op.drop_index('ix_audit_logs_timestamp', 'audit_logs')
    op.drop_table('audit_logs')
    
    # Remove columns from users table
    op.drop_index('ix_users_phone_number_hash', 'users')
    op.drop_column('users', 'phone_number_hash')
    op.drop_column('users', 'role')
