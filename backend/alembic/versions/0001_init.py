"""Initial schema with org-scoped tables"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "uber_organizations",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("org_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_uber_organizations_id"), "uber_organizations", ["id"])
    op.create_index(op.f("ix_uber_organizations_org_id"), "uber_organizations", ["org_id"])

    op.create_table(
        "uber_drivers",
        sa.Column("uuid", sa.String(), nullable=False),
        sa.Column("org_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("uuid"),
    )
    op.create_index(op.f("ix_uber_drivers_uuid"), "uber_drivers", ["uuid"])
    op.create_index(op.f("ix_uber_drivers_org_id"), "uber_drivers", ["org_id"])

    op.create_table(
        "uber_vehicles",
        sa.Column("uuid", sa.String(), nullable=False),
        sa.Column("org_id", sa.String(), nullable=False),
        sa.Column("plate", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("uuid"),
    )
    op.create_index(op.f("ix_uber_vehicles_uuid"), "uber_vehicles", ["uuid"])
    op.create_index(op.f("ix_uber_vehicles_org_id"), "uber_vehicles", ["org_id"])

    op.create_table(
        "driver_daily_metrics",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("org_id", sa.String(), nullable=False),
        sa.Column("driver_uuid", sa.String(), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("trips", sa.Float(), nullable=True, server_default="0"),
        sa.Column("online_hours", sa.Float(), nullable=True, server_default="0"),
        sa.Column("on_trip_hours", sa.Float(), nullable=True, server_default="0"),
        sa.Column("earnings", sa.Float(), nullable=True, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_driver_daily_metrics_id"), "driver_daily_metrics", ["id"])
    op.create_index(op.f("ix_driver_daily_metrics_org_id"), "driver_daily_metrics", ["org_id"])
    op.create_index(op.f("ix_driver_daily_metrics_driver_uuid"), "driver_daily_metrics", ["driver_uuid"])
    op.create_index(op.f("ix_driver_daily_metrics_day"), "driver_daily_metrics", ["day"])

    op.create_table(
        "driver_payments",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("org_id", sa.String(), nullable=False),
        sa.Column("driver_uuid", sa.String(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(), nullable=True, server_default="EUR"),
        sa.Column("description", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_driver_payments_id"), "driver_payments", ["id"])
    op.create_index(op.f("ix_driver_payments_org_id"), "driver_payments", ["org_id"])
    op.create_index(op.f("ix_driver_payments_driver_uuid"), "driver_payments", ["driver_uuid"])
    op.create_index(op.f("ix_driver_payments_occurred_at"), "driver_payments", ["occurred_at"])

    op.create_foreign_key(None, "driver_daily_metrics", "uber_drivers", ["driver_uuid"], ["uuid"])
    op.create_foreign_key(None, "driver_payments", "uber_drivers", ["driver_uuid"], ["uuid"])


def downgrade():
    op.drop_table("driver_payments")
    op.drop_table("driver_daily_metrics")
    op.drop_table("uber_vehicles")
    op.drop_table("uber_drivers")
    op.drop_table("uber_organizations")

