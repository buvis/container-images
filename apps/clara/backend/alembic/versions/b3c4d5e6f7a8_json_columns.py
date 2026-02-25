"""json columns for scopes and feature_flags

Revision ID: b3c4d5e6f7a8
Revises: a1b2c3d4e5f6
Create Date: 2026-02-23 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, Sequence[str]] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'personal_access_tokens',
        'scopes',
        type_=sa.JSON(),
        postgresql_using='scopes::jsonb',
        server_default='["read","write"]',
    )
    op.alter_column(
        'vault_settings',
        'feature_flags',
        type_=sa.JSON(),
        postgresql_using='feature_flags::jsonb',
        server_default='{"debts":true,"gifts":true,"pets":true,"journal":true}',
    )


def downgrade() -> None:
    op.alter_column(
        'vault_settings',
        'feature_flags',
        type_=sa.Text(),
        postgresql_using='feature_flags::text',
        server_default='{"debts":true,"gifts":true,"pets":true,"journal":true}',
    )
    op.alter_column(
        'personal_access_tokens',
        'scopes',
        type_=sa.Text(),
        postgresql_using='scopes::text',
        server_default='["read","write"]',
    )
