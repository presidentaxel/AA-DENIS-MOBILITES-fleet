"""Add bolt_organizations table"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0004_add_bolt_organizations"
down_revision = "0003_bolt_tables"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "bolt_organizations",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("org_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bolt_organizations_id"), "bolt_organizations", ["id"])
    op.create_index(op.f("ix_bolt_organizations_org_id"), "bolt_organizations", ["org_id"])


def downgrade():
    op.drop_index(op.f("ix_bolt_organizations_org_id"), table_name="bolt_organizations")
    op.drop_index(op.f("ix_bolt_organizations_id"), table_name="bolt_organizations")
    op.drop_table("bolt_organizations")

