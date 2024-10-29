"""Add bio to user

Revision ID: adc77e203424
Revises: 
Create Date: 2024-10-29 17:39:56.679542

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'adc77e203424'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('followers')
    op.drop_table('follow')
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('password_hash',
               existing_type=sa.VARCHAR(length=256),
               type_=sa.String(length=128),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('password_hash',
               existing_type=sa.String(length=128),
               type_=sa.VARCHAR(length=256),
               nullable=False)

    op.create_table('follow',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('follower_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('followed_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['followed_id'], ['user.id'], name='follow_followed_id_fkey'),
    sa.ForeignKeyConstraint(['follower_id'], ['user.id'], name='follow_follower_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='follow_pkey')
    )
    op.create_table('followers',
    sa.Column('follower_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('followed_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['followed_id'], ['user.id'], name='followers_followed_id_fkey'),
    sa.ForeignKeyConstraint(['follower_id'], ['user.id'], name='followers_follower_id_fkey'),
    sa.PrimaryKeyConstraint('follower_id', 'followed_id', name='followers_pkey')
    )
    # ### end Alembic commands ###