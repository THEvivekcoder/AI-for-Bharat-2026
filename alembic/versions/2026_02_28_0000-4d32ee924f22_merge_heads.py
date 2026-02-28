"""merge_heads

Revision ID: 4d32ee924f22
Revises: add_security_fields, b3b469f277d3
Create Date: 2026-02-28 00:00:24.208503

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4d32ee924f22'
down_revision = ('add_security_fields', 'b3b469f277d3')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
