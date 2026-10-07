"""add vm_templates table

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-06
"""

import sqlalchemy as sa
from alembic import op


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vm_templates",
        sa.Column("id", sa.Uuid(), nullable=False),

        # Proxmox identity
        sa.Column("node", sa.String(64), nullable=False),
        sa.Column("vmid", sa.Integer(), nullable=False),

        # Template metadata
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.String(64), nullable=True),
        sa.Column("os", sa.String(128), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),

        # Catalogue state
        sa.Column(
            "is_approved",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),

        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint("id", name="pk_templates"),

        sa.UniqueConstraint(
            "node",
            "vmid",
            name="uq_templates_node_vmid",
        ),
    )


def downgrade() -> None:
    op.drop_table("templates")