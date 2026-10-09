"""add user vm sync state fields

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-09
"""

import sqlalchemy as sa
from alembic import op


revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Track the actual Proxmox power state separately from is_active.
    op.add_column(
        "user_vms",
        sa.Column(
            "power_state",
            sa.String(length=16),
            server_default="unknown",
            nullable=False,
        ),
    )

    # Whether the VM exists in the latest successful Proxmox inventory.
    op.add_column(
        "user_vms",
        sa.Column(
            "is_present",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
    )

    # Change the default for newly created records.
    op.alter_column(
        "user_vms",
        "is_active",
        existing_type=sa.Boolean(),
        server_default=sa.false(),
        existing_nullable=False,
    )


def downgrade() -> None:
    # Restore the original default from migration 0003.
    op.alter_column(
        "user_vms",
        "is_active",
        existing_type=sa.Boolean(),
        server_default=sa.true(),
        existing_nullable=False,
    )

    op.drop_column("user_vms", "is_present")
    op.drop_column("user_vms", "power_state")
