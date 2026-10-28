"""Bounded text evidence attachments."""
from alembic import op
import sqlalchemy as sa
revision='007_attachments'
down_revision='006_mfa'
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('attachments',sa.Column('id',sa.String(36),primary_key=True),sa.Column('created',sa.Float(),nullable=False),sa.Column('support_ticket_id',sa.String(36),sa.ForeignKey('support_tickets.id')),sa.Column('remediation_id',sa.String(36),sa.ForeignKey('remediations.id')),sa.Column('user_id',sa.String(36),sa.ForeignKey('users.id'),nullable=False),sa.Column('filename',sa.String(100),nullable=False),sa.Column('content',sa.Text(),nullable=False),sa.Column('size',sa.Integer(),nullable=False),sa.Column('internal',sa.Boolean(),nullable=False),sa.CheckConstraint('(support_ticket_id IS NULL) <> (remediation_id IS NULL)',name='one_attachment_parent'))
    op.create_index('ix_attachments_support_ticket_id','attachments',['support_ticket_id'])
    op.create_index('ix_attachments_remediation_id','attachments',['remediation_id'])
def downgrade():
    op.drop_table('attachments')
