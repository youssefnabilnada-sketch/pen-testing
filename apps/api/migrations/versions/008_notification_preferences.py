"""Personal in-app preferences and independent read receipts."""
from alembic import op
import sqlalchemy as sa
revision='008_notification_preferences'
down_revision='007_attachments'
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('notification_preferences',sa.Column('org_id',sa.String(36),sa.ForeignKey('organizations.id'),primary_key=True),sa.Column('user_id',sa.String(36),sa.ForeignKey('users.id'),primary_key=True),sa.Column('enabled_kinds',sa.JSON(),nullable=False))
    op.create_table('notification_reads',sa.Column('notification_id',sa.String(36),sa.ForeignKey('notifications.id'),primary_key=True),sa.Column('user_id',sa.String(36),sa.ForeignKey('users.id'),primary_key=True))
def downgrade():
    op.drop_table('notification_reads');op.drop_table('notification_preferences')
