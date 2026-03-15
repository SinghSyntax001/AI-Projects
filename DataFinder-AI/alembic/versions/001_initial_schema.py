"""Initial database schema with datasets table.

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-03-15

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial tables."""
    op.create_table(
        "datasets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("size", sa.String(100), nullable=True),
        sa.Column("embedding", sa.Text(), nullable=True),
        sa.Column("keywords", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url", name="uq_datasets_url"),
    )

    # Create indices for common queries
    op.create_index("ix_datasets_name", "datasets", ["name"])
    op.create_index("ix_datasets_source", "datasets", ["source"])
    op.create_index("ix_datasets_url", "datasets", ["url"])


def downgrade() -> None:
    """Drop tables."""
    op.drop_table("datasets")
