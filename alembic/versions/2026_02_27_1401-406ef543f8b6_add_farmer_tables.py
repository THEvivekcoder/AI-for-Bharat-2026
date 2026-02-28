"""add_farmer_tables

Revision ID: 406ef543f8b6
Revises: 66f1615298ee
Create Date: 2026-02-27 14:01:19.185509

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '406ef543f8b6'
down_revision = '66f1615298ee'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create farm_profiles table
    op.create_table(
        'farm_profiles',
        sa.Column('farm_id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('land_size_acres', sa.Float(), nullable=False),
        sa.Column('soil_type', sa.String(50), nullable=False),
        sa.Column('irrigation_type', sa.String(50), nullable=False),
        sa.Column('location_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('current_crops', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('previous_crops', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('livestock', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'])
    )
    
    # Create crop_recommendations table
    op.create_table(
        'crop_recommendations',
        sa.Column('recommendation_id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('farm_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('crop_name', sa.String(100), nullable=False),
        sa.Column('suitability_score', sa.Float(), nullable=False),
        sa.Column('expected_yield', sa.String(100), nullable=True),
        sa.Column('water_requirement', sa.String(50), nullable=False),
        sa.Column('duration_days', sa.Integer(), nullable=False),
        sa.Column('market_demand', sa.String(20), nullable=True),
        sa.Column('estimated_profit', sa.String(100), nullable=True),
        sa.Column('reasoning', sa.Text(), nullable=False),
        sa.Column('risks', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('season', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['farm_id'], ['farm_profiles.farm_id'], ondelete='CASCADE')
    )
    
    # Create fertilizer_recommendations table
    op.create_table(
        'fertilizer_recommendations',
        sa.Column('recommendation_id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('farm_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('crop_name', sa.String(100), nullable=False),
        sa.Column('growth_stage', sa.String(50), nullable=False),
        sa.Column('soil_ph', sa.Float(), nullable=True),
        sa.Column('soil_nutrients', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('fertilizer_type', sa.String(100), nullable=False),
        sa.Column('quantity_per_acre', sa.String(50), nullable=False),
        sa.Column('timing', sa.String(100), nullable=False),
        sa.Column('application_method', sa.String(100), nullable=False),
        sa.Column('additional_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['farm_id'], ['farm_profiles.farm_id'], ondelete='CASCADE')
    )
    
    # Create mandi_prices table
    op.create_table(
        'mandi_prices',
        sa.Column('price_id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('crop_name', sa.String(100), nullable=False, index=True),
        sa.Column('mandi_name', sa.String(100), nullable=False),
        sa.Column('state', sa.String(50), nullable=False, index=True),
        sa.Column('district', sa.String(50), nullable=False, index=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('price_per_quintal', sa.Float(), nullable=False),
        sa.Column('price_date', sa.Date(), nullable=False, index=True),
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )
    
    # Create crop_calendars table
    op.create_table(
        'crop_calendars',
        sa.Column('calendar_id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('crop_name', sa.String(100), nullable=False, index=True),
        sa.Column('state', sa.String(50), nullable=False, index=True),
        sa.Column('district', sa.String(50), nullable=True),
        sa.Column('season', sa.String(20), nullable=False),
        sa.Column('sowing_start', sa.String(20), nullable=False),
        sa.Column('sowing_end', sa.String(20), nullable=False),
        sa.Column('harvest_start', sa.String(20), nullable=False),
        sa.Column('harvest_end', sa.String(20), nullable=False),
        sa.Column('care_schedule', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )


def downgrade() -> None:
    op.drop_table('crop_calendars')
    op.drop_table('mandi_prices')
    op.drop_table('fertilizer_recommendations')
    op.drop_table('crop_recommendations')
    op.drop_table('farm_profiles')
