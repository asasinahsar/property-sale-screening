"""add_status_to_generated_files

Revision ID: 75ec48cab47f
Revises: c1b55b2ba0be
Create Date: 2026-06-25 22:04:13.876968

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '75ec48cab47f'
down_revision: Union[str, None] = 'c1b55b2ba0be'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the enum type first, then add the column
    file_status_enum = sa.Enum('pending', 'processing', 'completed', 'failed', name='file_status')
    file_status_enum.create(op.get_bind(), checkfirst=True)
    op.add_column('generated_files', sa.Column('status', file_status_enum, nullable=False, server_default='pending'))


def downgrade() -> None:
    op.drop_column('generated_files', 'status')
    sa.Enum(name='file_status').drop(op.get_bind(), checkfirst=True)
