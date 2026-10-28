"""Encrypted authenticator enrollment and hashed one-use recovery codes."""
from alembic import op
import sqlalchemy as sa
revision='006_mfa'
down_revision='005_support'
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('mfa_states',sa.Column('user_id',sa.String(36),sa.ForeignKey('users.id'),primary_key=True),sa.Column('secret',sa.Text(),nullable=False),sa.Column('enabled',sa.Boolean(),nullable=False),sa.Column('expires',sa.Float(),nullable=False),sa.Column('enrollment_session',sa.String(64),nullable=False),sa.Column('last_counter',sa.Integer(),nullable=False))
    op.create_table('mfa_recovery_codes',sa.Column('digest',sa.String(64),primary_key=True),sa.Column('user_id',sa.String(36),sa.ForeignKey('users.id'),nullable=False),sa.Column('used',sa.Boolean(),nullable=False))
    op.create_index('ix_mfa_recovery_codes_user_id','mfa_recovery_codes',['user_id'])
def downgrade():
    op.drop_table('mfa_recovery_codes');op.drop_table('mfa_states')
