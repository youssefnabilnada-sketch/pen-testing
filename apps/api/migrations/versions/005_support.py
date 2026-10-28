"""Tenant-scoped support tickets and staff notes."""
from alembic import op
import sqlalchemy as sa
revision='005_support'
down_revision='004_team_invitations'
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('support_tickets',sa.Column('id',sa.String(36),primary_key=True),sa.Column('created',sa.Float(),nullable=False),sa.Column('org_id',sa.String(36),sa.ForeignKey('organizations.id'),nullable=False),sa.Column('user_id',sa.String(36),sa.ForeignKey('users.id'),nullable=False),sa.Column('subject',sa.String(160),nullable=False),sa.Column('status',sa.String(30),nullable=False),sa.Column('updated',sa.Float(),nullable=False))
    op.create_index('ix_support_tickets_org_id','support_tickets',['org_id'])
    op.create_index('ix_support_tickets_status','support_tickets',['status'])
    op.create_table('support_messages',sa.Column('id',sa.String(36),primary_key=True),sa.Column('created',sa.Float(),nullable=False),sa.Column('ticket_id',sa.String(36),sa.ForeignKey('support_tickets.id'),nullable=False),sa.Column('user_id',sa.String(36),sa.ForeignKey('users.id'),nullable=False),sa.Column('body',sa.Text(),nullable=False),sa.Column('internal',sa.Boolean(),nullable=False),sa.Column('staff',sa.Boolean(),nullable=False))
    op.create_index('ix_support_messages_ticket_id','support_messages',['ticket_id'])
def downgrade():
    op.drop_table('support_messages');op.drop_table('support_tickets')
