"""add_resume_url_to_users

Revision ID: cd1afc568b9d
Revises: ba7cf3bbd018
Create Date: 2026-10-14 12:40:12.085546

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cd1afc568b9d'
down_revision: Union[str, Sequence[str], None] = 'ba7cf3bbd018'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('resume_url', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'resume_url')

