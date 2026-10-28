"""Explicit verified-recipient team invitations."""
from alembic import op
import sqlalchemy as sa
revision='004_team_invitations'
down_revision='003_firebase'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('team_invitations',
        sa.Column('id',sa.String(36),primary_key=True),
        sa.Column('created',sa.Float(),nullable=False),
        sa.Column('org_id',sa.String(36),sa.ForeignKey('organizations.id'),nullable=False),
        sa.Column('email',sa.String(254),nullable=False),
        sa.Column('role',sa.String(30),nullable=False),
        sa.Column('invited_by',sa.String(36),sa.ForeignKey('users.id'),nullable=False),
        sa.Column('expires',sa.Float(),nullable=False),
        sa.Column('status',sa.String(20),nullable=False),
        sa.Column('accepted_by',sa.String(36),sa.ForeignKey('users.id')))
    op.create_index('ix_team_invitations_org_id','team_invitations',['org_id'])
    op.create_index('ix_team_invitations_email','team_invitations',['email'])

def downgrade():
    op.drop_table('team_invitations')
