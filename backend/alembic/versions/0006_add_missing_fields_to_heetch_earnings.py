"""Add missing fields to heetch_earnings

Revision ID: 0006_add_missing_fields_to_heetch_earnings
Revises: 0005_add_heetch_tables
Create Date: 2025-01-23 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0006_add_missing_fields_to_heetch_earnings'
down_revision = '0005_add_heetch_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Ajouter les nouveaux champs à heetch_earnings
    op.add_column('heetch_earnings', sa.Column('start_date', sa.Date(), nullable=True))
    op.add_column('heetch_earnings', sa.Column('end_date', sa.Date(), nullable=True))
    op.add_column('heetch_earnings', sa.Column('unpaid_cash_rides_refunds', sa.Float(), nullable=True))
    op.add_column('heetch_earnings', sa.Column('debt', sa.Float(), nullable=True))
    op.add_column('heetch_earnings', sa.Column('money_transfer_amount', sa.Float(), nullable=True))
    
    # Ajouter des index pour les nouvelles colonnes date
    op.create_index(op.f('ix_heetch_earnings_start_date'), 'heetch_earnings', ['start_date'])
    op.create_index(op.f('ix_heetch_earnings_end_date'), 'heetch_earnings', ['end_date'])


def downgrade():
    # Supprimer les index
    op.drop_index(op.f('ix_heetch_earnings_end_date'), table_name='heetch_earnings')
    op.drop_index(op.f('ix_heetch_earnings_start_date'), table_name='heetch_earnings')
    
    # Supprimer les colonnes
    op.drop_column('heetch_earnings', 'money_transfer_amount')
    op.drop_column('heetch_earnings', 'debt')
    op.drop_column('heetch_earnings', 'unpaid_cash_rides_refunds')
    op.drop_column('heetch_earnings', 'end_date')
    op.drop_column('heetch_earnings', 'start_date')

