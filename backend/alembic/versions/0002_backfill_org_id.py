"""Backfill org_id with default for existing rows"""

import os

from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_backfill_org_id"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade():
    default_org = os.getenv("UBER_DEFAULT_ORG_ID", "default_org")
    tables = [
        "uber_organizations",
        "uber_drivers",
        "uber_vehicles",
        "driver_daily_metrics",
        "driver_payments",
    ]
    for table in tables:
        op.execute(f"update {table} set org_id = '{default_org}' where org_id is null or org_id = ''")


def downgrade():
    # No-op: leave org_id values as-is
    pass

