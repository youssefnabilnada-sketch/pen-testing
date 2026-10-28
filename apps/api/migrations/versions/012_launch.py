"""Persist authorized Launch Guard evidence."""
from alembic import op
import sqlalchemy as sa
revision='012_launch'
down_revision='011_health'
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('launch_reviews',sa.Column('id',sa.String(36),primary_key=True),sa.Column('created',sa.Float(),nullable=False),
        sa.Column('org_id',sa.String(36),sa.ForeignKey('organizations.id'),nullable=False),
        sa.Column('user_id',sa.String(36),sa.ForeignKey('users.id'),nullable=False),
        sa.Column('repository',sa.String(220),nullable=False),sa.Column('revision',sa.String(40),nullable=False),sa.Column('result',sa.JSON(),nullable=False))
    op.create_index('ix_launch_reviews_org_id','launch_reviews',['org_id'])
def downgrade():
    op.drop_index('ix_launch_reviews_org_id',table_name='launch_reviews');op.drop_table('launch_reviews')
