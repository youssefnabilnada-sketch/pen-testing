"""Opt-in notification email subscriptions and durable delivery attempts."""
from alembic import op
import sqlalchemy as sa
revision='014_email'
down_revision='013_agency'
branch_labels=None
depends_on=None
def ident():return [sa.Column('id',sa.String(36),primary_key=True),sa.Column('created',sa.Float(),nullable=False)]
def upgrade():
    op.create_table('alert_subscriptions',*ident(),sa.Column('org_id',sa.String(36),sa.ForeignKey('organizations.id'),nullable=False),sa.Column('user_id',sa.String(36),sa.ForeignKey('users.id'),nullable=False),sa.Column('kinds',sa.JSON(),nullable=False),sa.UniqueConstraint('org_id','user_id'))
    op.create_table('email_deliveries',*ident(),sa.Column('notification_id',sa.String(36),sa.ForeignKey('notifications.id'),nullable=False),sa.Column('user_id',sa.String(36),sa.ForeignKey('users.id'),nullable=False),sa.Column('status',sa.String(30),nullable=False),sa.Column('attempts',sa.Integer(),nullable=False),sa.Column('next_due',sa.Float(),nullable=False),sa.Column('error',sa.String(200),nullable=False),sa.UniqueConstraint('notification_id','user_id'))
    op.create_index('ix_email_deliveries_user_id','email_deliveries',['user_id'])
def downgrade():
    op.drop_index('ix_email_deliveries_user_id',table_name='email_deliveries');op.drop_table('email_deliveries');op.drop_table('alert_subscriptions')
