"""add user

Revision ID: 75a291002c6a
Revises: 2aea59e3e201
Create Date: 2023-10-21 04:32:22.054946

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '75a291002c6a'
down_revision: Union[str, None] = '2aea59e3e201'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'roles',
               existing_type=postgresql.ENUM('admin', 'moderator', 'user', name='role'),
               type_=sa.Enum('ADMIN', 'MODERATOR', 'USER', name='role'),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'roles',
               existing_type=sa.Enum('ADMIN', 'MODERATOR', 'USER', name='role'),
               type_=postgresql.ENUM('admin', 'moderator', 'user', name='role'),
               existing_nullable=True)
    # ### end Alembic commands ###
