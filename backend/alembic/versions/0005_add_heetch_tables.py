"""Add Heetch tables"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0005_add_heetch_tables"
down_revision = "0004_add_bolt_organizations"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "heetch_drivers",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("org_id", sa.String(), nullable=False),
        sa.Column("first_name", sa.String(), nullable=False, server_default=""),
        sa.Column("last_name", sa.String(), nullable=False, server_default=""),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("image_url", sa.String(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=True, server_default=sa.true()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_heetch_drivers_id"), "heetch_drivers", ["id"])
    op.create_index(op.f("ix_heetch_drivers_org_id"), "heetch_drivers", ["org_id"])
    op.create_index(op.f("ix_heetch_drivers_email"), "heetch_drivers", ["email"])

    op.create_table(
        "heetch_earnings",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("org_id", sa.String(), nullable=False),
        sa.Column("driver_id", sa.String(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("period", sa.String(), nullable=False),
        sa.Column("gross_earnings", sa.Float(), nullable=True, server_default="0"),
        sa.Column("net_earnings", sa.Float(), nullable=True, server_default="0"),
        sa.Column("cash_collected", sa.Float(), nullable=True, server_default="0"),
        sa.Column("card_gross_earnings", sa.Float(), nullable=True, server_default="0"),
        sa.Column("cash_commission_fees", sa.Float(), nullable=True, server_default="0"),
        sa.Column("card_commission_fees", sa.Float(), nullable=True, server_default="0"),
        sa.Column("cancellation_fees", sa.Float(), nullable=True, server_default="0"),
        sa.Column("cancellation_fee_adjustments", sa.Float(), nullable=True, server_default="0"),
        sa.Column("bonuses", sa.Float(), nullable=True, server_default="0"),
        sa.Column("terminated_rides", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("cancelled_rides", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("cash_discount", sa.Float(), nullable=True, server_default="0"),
        sa.Column("currency", sa.String(), nullable=True, server_default="EUR"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_heetch_earnings_id"), "heetch_earnings", ["id"])
    op.create_index(op.f("ix_heetch_earnings_org_id"), "heetch_earnings", ["org_id"])
    op.create_index(op.f("ix_heetch_earnings_driver_id"), "heetch_earnings", ["driver_id"])
    op.create_index(op.f("ix_heetch_earnings_date"), "heetch_earnings", ["date"])
    op.create_index(op.f("ix_heetch_earnings_period"), "heetch_earnings", ["period"])


def downgrade():
    op.drop_table("heetch_earnings")
    op.drop_table("heetch_drivers")

