"""Add Bolt tables"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0003_bolt_tables"
down_revision = "0002_backfill_org_id"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "bolt_drivers",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("org_id", sa.String(), nullable=False),
        sa.Column("first_name", sa.String(), nullable=False, server_default=""),
        sa.Column("last_name", sa.String(), nullable=False, server_default=""),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=True, server_default=sa.true()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bolt_drivers_id"), "bolt_drivers", ["id"])
    op.create_index(op.f("ix_bolt_drivers_org_id"), "bolt_drivers", ["org_id"])

    op.create_table(
        "bolt_vehicles",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("org_id", sa.String(), nullable=False),
        sa.Column("provider_vehicle_id", sa.String(), nullable=True),
        sa.Column("plate", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bolt_vehicles_id"), "bolt_vehicles", ["id"])
    op.create_index(op.f("ix_bolt_vehicles_org_id"), "bolt_vehicles", ["org_id"])

    op.create_table(
        "bolt_trips",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("org_id", sa.String(), nullable=False),
        sa.Column("driver_id", sa.String(), nullable=True),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=False),
        sa.Column("price", sa.Float(), nullable=True, server_default="0"),
        sa.Column("distance", sa.Float(), nullable=True, server_default="0"),
        sa.Column("currency", sa.String(), nullable=True, server_default="EUR"),
        sa.Column("status", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bolt_trips_id"), "bolt_trips", ["id"])
    op.create_index(op.f("ix_bolt_trips_org_id"), "bolt_trips", ["org_id"])
    op.create_index(op.f("ix_bolt_trips_driver_id"), "bolt_trips", ["driver_id"])
    op.create_index(op.f("ix_bolt_trips_start_time"), "bolt_trips", ["start_time"])

    op.create_table(
        "bolt_earnings",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("org_id", sa.String(), nullable=False),
        sa.Column("driver_id", sa.String(), nullable=True),
        sa.Column("payout_date", sa.DateTime(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=True, server_default="0"),
        sa.Column("type", sa.String(), nullable=True),
        sa.Column("currency", sa.String(), nullable=True, server_default="EUR"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bolt_earnings_id"), "bolt_earnings", ["id"])
    op.create_index(op.f("ix_bolt_earnings_org_id"), "bolt_earnings", ["org_id"])
    op.create_index(op.f("ix_bolt_earnings_driver_id"), "bolt_earnings", ["driver_id"])
    op.create_index(op.f("ix_bolt_earnings_payout_date"), "bolt_earnings", ["payout_date"])


def downgrade():
    op.drop_table("bolt_earnings")
    op.drop_table("bolt_trips")
    op.drop_table("bolt_vehicles")
    op.drop_table("bolt_drivers")

