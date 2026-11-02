"""add_resume_url_to_job_descriptions

Revision ID: d1e2f3a4b5c6
Revises: cd1afc568b9d, ea579a6839d0
Create Date: 2026-10-31 12:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, Sequence[str], None] = ('cd1afc568b9d', 'ea579a6839d0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('job_descriptions')]
    if 'resume_url' not in columns:
        op.add_column('job_descriptions', sa.Column('resume_url', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('job_descriptions', 'resume_url')
