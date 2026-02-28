"""add_skills_and_jobs_tables

Revision ID: 1825c4aef2aa
Revises: 406ef543f8b6
Create Date: 2026-02-27 19:52:59.031225

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '1825c4aef2aa'
down_revision = '406ef543f8b6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create skill_programs table
    op.create_table(
        'skill_programs',
        sa.Column('program_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('provider', sa.String(100), nullable=True),
        sa.Column('category', sa.String(50), nullable=False, index=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('duration_weeks', sa.Integer, nullable=True),
        sa.Column('cost', sa.Numeric(10, 2), nullable=True),
        sa.Column('state', sa.String(50), nullable=True, index=True),
        sa.Column('district', sa.String(50), nullable=True, index=True),
        sa.Column('mode', sa.String(20), nullable=True),
        sa.Column('eligibility_criteria', JSONB, nullable=True),
        sa.Column('certification', sa.Boolean, default=False),
        sa.Column('placement_support', sa.Boolean, default=False),
        sa.Column('registration_url', sa.String(500), nullable=True),
        sa.Column('contact', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create job_postings table
    op.create_table(
        'job_postings',
        sa.Column('job_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False, index=True),
        sa.Column('department', sa.String(100), nullable=True, index=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('qualifications', JSONB, nullable=True),
        sa.Column('location', JSONB, nullable=True),
        sa.Column('application_deadline', sa.Date, nullable=True, index=True),
        sa.Column('application_url', sa.String(500), nullable=True),
        sa.Column('posted_date', sa.Date, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('job_postings')
    op.drop_table('skill_programs')
