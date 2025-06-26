"""Merge independent fee changes

Revision ID: 9f6beb520fc6
Revises: 5326c9604561, b6cb1771a18b merged migrations
Create Date: 2025-06-26 09:14:07.589172

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f6beb520fc6'
down_revision: Union[str, None] = ('5326c9604561', 'b6cb1771a18b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
