"""CRM requests and immutable-report integrity baselines."""
from alembic import op
import sqlalchemy as sa
revision='016_crm_vault'
down_revision='015_patch_backup'
branch_labels=None
depends_on=None
def ident():return [sa.Column('id',sa.String(36),primary_key=True),sa.Column('created',sa.Float(),nullable=False)]
def upgrade():
    op.create_table('leads',*ident(),sa.Column('org_id',sa.String(36),sa.ForeignKey('organizations.id'),nullable=False),sa.Column('user_id',sa.String(36),sa.ForeignKey('users.id'),nullable=False),sa.Column('kind',sa.String(20),nullable=False),sa.Column('message',sa.Text(),nullable=False),sa.Column('contact_consent',sa.Boolean(),nullable=False),sa.Column('status',sa.String(30),nullable=False),sa.Column('followup_at',sa.Float(),nullable=True),sa.Column('history',sa.JSON(),nullable=False),sa.Column('invite_digest',sa.String(64),nullable=True),sa.Column('invite_expires',sa.Float(),nullable=True))
    op.create_index('ix_leads_org_id','leads',['org_id'])
    op.create_table('evidence_seals',*ident(),sa.Column('report_id',sa.String(36),sa.ForeignKey('reports.id'),nullable=False,unique=True),sa.Column('sha256',sa.String(64),nullable=False))
def downgrade():
    op.drop_table('evidence_seals');op.drop_index('ix_leads_org_id',table_name='leads');op.drop_table('leads')
