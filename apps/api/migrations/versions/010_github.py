"""Tenant-owned GitHub consent and reviewable repository patches."""
from alembic import op
import sqlalchemy as sa
revision='010_github'
down_revision='009_profile'
branch_labels=None
depends_on=None

def identity():return [sa.Column('id',sa.String(36),primary_key=True),sa.Column('created',sa.Float(),nullable=False)]
def org():return sa.Column('org_id',sa.String(36),sa.ForeignKey('organizations.id'),nullable=False)
def upgrade():
    op.create_table('github_states',*identity(),org(),sa.Column('user_id',sa.String(36),sa.ForeignKey('users.id'),nullable=False),sa.Column('digest',sa.String(64),nullable=False,unique=True),sa.Column('expires',sa.Float(),nullable=False),sa.Column('used',sa.Boolean(),nullable=False))
    op.create_index('ix_github_states_org_id','github_states',['org_id'])
    op.create_table('github_connections',*identity(),org(),sa.Column('user_id',sa.String(36),sa.ForeignKey('users.id'),nullable=False),sa.Column('account_id',sa.String(40),nullable=False),sa.Column('login',sa.String(100),nullable=False),sa.Column('encrypted_token',sa.Text(),nullable=False),sa.Column('expires',sa.Float(),nullable=False),sa.Column('revoked',sa.Boolean(),nullable=False))
    op.create_index('ix_github_connections_org_id','github_connections',['org_id'])
    op.create_table('repository_patches',*identity(),org(),sa.Column('connection_id',sa.String(36),sa.ForeignKey('github_connections.id'),nullable=False),sa.Column('remediation_id',sa.String(36),sa.ForeignKey('remediations.id'),nullable=False),sa.Column('repository',sa.String(220),nullable=False),sa.Column('base_branch',sa.String(200),nullable=False),sa.Column('base_sha',sa.String(64),nullable=False),sa.Column('file_sha',sa.String(64),nullable=False),sa.Column('proposed_content',sa.Text(),nullable=False),sa.Column('diff',sa.Text(),nullable=False),sa.Column('status',sa.String(40),nullable=False),sa.Column('test_evidence',sa.JSON(),nullable=False),sa.Column('pull_number',sa.Integer(),nullable=True),sa.Column('approved_by',sa.String(36),sa.ForeignKey('users.id'),nullable=True))
    op.create_index('ix_repository_patches_org_id','repository_patches',['org_id'])
def downgrade():
    for name in ('repository_patches','github_connections','github_states'):
        op.drop_index('ix_'+name+'_org_id',table_name=name);op.drop_table(name)
