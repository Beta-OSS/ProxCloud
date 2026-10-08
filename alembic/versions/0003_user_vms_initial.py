"""add user_vms table

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-08
"""

import sqlalchemy as sa
from alembic import op


revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_vms",
        sa.Column("id", sa.Uuid(), nullable=False),

        # Proxmox identity
        sa.Column("node", sa.String(64), nullable=False),
        sa.Column("vmid", sa.Integer(), nullable=False),

        # VM metadata
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("os", sa.String(128), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),

        # Ownership
        sa.Column("user_id", sa.Uuid(), nullable=False),

        # VM state
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.true(),
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
            "last_synced_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.PrimaryKeyConstraint("id", name="pk_user_vms"),

        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_user_vms_user_id_users",
        ),

        sa.UniqueConstraint(
            "node",
            "vmid",
            name="uq_user_vms_node_vmid",
        ),
    )


def downgrade() -> None:
    op.drop_table("user_vms")