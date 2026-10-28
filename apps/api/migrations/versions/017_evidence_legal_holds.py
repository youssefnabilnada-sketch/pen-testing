"""Auditable customer-controlled evidence legal holds; evidence is never auto-deleted."""
from alembic import op
import sqlalchemy as sa

revision = '017_evidence_legal_holds'
down_revision = '016_crm_vault'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('evidence_legal_holds',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('created', sa.Float(), nullable=False),
        sa.Column('report_id', sa.String(36), sa.ForeignKey('reports.id'), nullable=False),
        sa.Column('reason', sa.String(500), nullable=False),
        sa.Column('placed_by', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('released_at', sa.Float(), nullable=True),
        sa.Column('released_by', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('release_reason', sa.String(500), nullable=True))
    op.create_index('ix_evidence_legal_holds_report_id', 'evidence_legal_holds', ['report_id'])

def downgrade():
    op.drop_index('ix_evidence_legal_holds_report_id', table_name='evidence_legal_holds')
    op.drop_table('evidence_legal_holds')
