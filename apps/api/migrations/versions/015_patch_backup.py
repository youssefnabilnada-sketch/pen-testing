"""Encrypted original configuration backups for reviewed AutoFix proposals."""
from alembic import op
import sqlalchemy as sa
revision='015_patch_backup'
down_revision='014_email'
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('patch_backups',sa.Column('id',sa.String(36),primary_key=True),sa.Column('created',sa.Float(),nullable=False),sa.Column('patch_id',sa.String(36),sa.ForeignKey('repository_patches.id'),nullable=False,unique=True),sa.Column('encrypted_content',sa.Text(),nullable=False),sa.Column('sha256',sa.String(64),nullable=False),sa.Column('restore_verified',sa.Boolean(),nullable=False))
def downgrade():op.drop_table('patch_backups')
