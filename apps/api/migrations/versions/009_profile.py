"""Optional display name."""
from alembic import op
import sqlalchemy as sa
revision='009_profile'
down_revision='008_notification_preferences'
branch_labels=None
depends_on=None
def upgrade():
    op.add_column('users',sa.Column('display_name',sa.String(100),server_default='',nullable=False))
def downgrade():
    op.drop_column('users','display_name')
