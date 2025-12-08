"""merge_heads

Revision ID: 098f95a00fb7
Revises: 008_add_datasets_table, 007_add_email_verification
Create Date: 2025-12-03 10:24:31.531236+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '098f95a00fb7'
down_revision: Union[str, None] = ('008_add_datasets_table', '007_add_email_verification')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
