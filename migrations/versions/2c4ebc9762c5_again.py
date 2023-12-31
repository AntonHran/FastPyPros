"""again

Revision ID: 2c4ebc9762c5
Revises: 75a291002c6a
Create Date: 2023-10-21 05:08:20.161750

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2c4ebc9762c5'
down_revision: Union[str, None] = '75a291002c6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'roles',
               existing_type=postgresql.ENUM('admin', 'moderator', 'user', name='role'),
               type_=sa.Enum('admin', 'moderator', 'user', name='role'),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'roles',
               existing_type=sa.Enum('admin', 'moderator', 'user', name='userrole'),
               type_=postgresql.ENUM('admin', 'moderator', 'user', name='role'),
               existing_nullable=True)
    # ### end Alembic commands ###
