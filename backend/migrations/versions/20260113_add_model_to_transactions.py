"""add model column to transactions

Revision ID: 20260113_add_model_to_transactions
Revises: 
Create Date: 2026-01-13 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260113_add_model_to_transactions'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add 'model' column to transactions (nullable to be backward compatible)
    op.add_column('transactions', sa.Column('model', sa.String(length=50), nullable=True))
    # optional index to speed up model queries
    op.create_index('idx_transactions_model', 'transactions', ['model'])


def downgrade():
    # remove index then column
    op.drop_index('idx_transactions_model', table_name='transactions')
    op.drop_column('transactions', 'model')


