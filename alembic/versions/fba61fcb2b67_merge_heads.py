"""merge heads

Revision ID: fba61fcb2b67
Revises: 5326c9604561, b6cb1771a18b
Create Date: 2025-05-26 17:52:22.791703

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fba61fcb2b67'
down_revision: Union[str, None] = ('5326c9604561', 'b6cb1771a18b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
