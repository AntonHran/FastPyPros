"""abstraction+properties

Revision ID: 2aea59e3e201
Revises: 2266c1f8d248
Create Date: 2023-10-20 20:35:11.351261

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2aea59e3e201'
down_revision: Union[str, None] = '2266c1f8d248'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('accounts', 'images_quantity')
    op.add_column('ban_lists', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('ban_lists', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.add_column('comment_images', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('comment_images', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.add_column('images', sa.Column('slug', sa.String(length=255), nullable=True))
    op.drop_column('images', 'qr_path')
    op.drop_column('images', 'rating')
    op.add_column('ratings', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.add_column('tag_images', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('tag_images', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.add_column('tags', sa.Column('updated_at', sa.DateTime(), nullable=True))
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
    op.drop_column('tags', 'updated_at')
    op.drop_column('tag_images', 'updated_at')
    op.drop_column('tag_images', 'created_at')
    op.drop_column('ratings', 'updated_at')
    op.add_column('images', sa.Column('rating', sa.REAL(), autoincrement=False, nullable=True))
    op.add_column('images', sa.Column('qr_path', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.drop_column('images', 'slug')
    op.drop_column('comment_images', 'updated_at')
    op.drop_column('comment_images', 'created_at')
    op.drop_column('ban_lists', 'updated_at')
    op.drop_column('ban_lists', 'created_at')
    op.add_column('accounts', sa.Column('images_quantity', sa.INTEGER(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
