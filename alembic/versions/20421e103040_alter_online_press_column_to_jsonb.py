"""Alter online_press column to JSONB

Revision ID: 20421e103040
Revises: 9f6beb520fc6
Create Date: 2025-06-26 09:16:39.031570

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20421e103040'
down_revision: Union[str, None] = '9f6beb520fc6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- UPGRADE: FROM ARRAY(String) of URLs TO JSONB of [{"title": "...", "url": "..."}] ---

    # 1. Add a temporary JSONB column (nullable=True initially as it will be populated)
    #    Make sure the table name 'profile' is correct for your schema.
    op.add_column('profile', sa.Column('temp_online_press', postgresql.JSONB, nullable=True))

    # 2. Migrate data from the old ARRAY(String) column to the new JSONB column
    #    This SQL query transforms each simple URL string into a JSONB object
    #    with a default 'Legacy Press' title.
    op.execute("""
        UPDATE profile
        SET temp_online_press = COALESCE(
            (SELECT jsonb_agg(jsonb_build_object('title', 'Legacy Press', 'url', elem))
             FROM unnest(online_press) AS elem
             WHERE elem IS NOT NULL),
            '[]'::jsonb
        );
    """)

    # 3. Drop the old ARRAY(String) column
    op.drop_column('profile', 'online_press')

    # 4. Rename the new JSONB column to the original name
    #    Adjust nullable based on your final model definition for 'online_press'
    op.alter_column('profile', 'temp_online_press', new_column_name='online_press',
                    existing_type=postgresql.JSONB,
                    nullable=True) # Set this to False if your model requires it to be non-nullable and you've handled existing NULLs

def downgrade() -> None:
    # --- DOWNGRADE: To revert from JSONB back to ARRAY(String) of URLs ---
    # WARNING: This downgrade will lose the 'title' information, as the original column was just simple URL strings.

    # 1. Add a temporary ARRAY(String) column for the old type (nullable=True initially)
    op.add_column('profile', sa.Column('temp_online_press_old_type', postgresql.ARRAY(sa.String()), nullable=True))

    # 2. Migrate data: Extract 'url' from JSONB objects back into a simple string array
    #    This query iterates through the JSONB array, extracts the 'url' value from each object,
    #    and aggregates them back into a text array.
    op.execute("""
        UPDATE profile
        SET temp_online_press_old_type = (
            SELECT COALESCE(
                ARRAY_AGG(elem->>'url' ORDER BY _idx), '{}'::text[]
            )
            FROM jsonb_array_elements(online_press) WITH ORDINALITY AS _e(elem, _idx)
            WHERE elem->>'url' IS NOT NULL
        )
        WHERE online_press IS NOT NULL;
    """)

    # 3. Drop the current JSONB column
    op.drop_column('profile', 'online_press')

    # 4. Rename the temporary column back to the original name
    #    Adjust nullable based on your original model definition for 'online_press'
    op.alter_column('profile', 'temp_online_press_old_type', new_column_name='online_press',
                    existing_type=postgresql.ARRAY(sa.String()),
                    nullable=True) # Set this to False if your original model required it to be non-nullable
