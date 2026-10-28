"""Authorized health monitoring and bounded response history."""
from alembic import op
import sqlalchemy as sa
revision='011_health'
down_revision='010_github'
branch_labels=None
depends_on=None

def identity():
    return [sa.Column('id',sa.String(36),primary_key=True),sa.Column('created',sa.Float(),nullable=False)]

def upgrade():
    op.create_table('health_monitors',*identity(),
        sa.Column('org_id',sa.String(36),sa.ForeignKey('organizations.id'),nullable=False),
        sa.Column('asset_id',sa.String(36),sa.ForeignKey('assets.id'),nullable=False,unique=True),
        sa.Column('authorization_id',sa.String(36),sa.ForeignKey('authorizations.id'),nullable=False),
        sa.Column('interval_seconds',sa.Integer(),nullable=False),
        sa.Column('enabled',sa.Boolean(),nullable=False),
        sa.Column('next_due',sa.Float(),nullable=False),
        sa.Column('last_status',sa.String(30),nullable=False))
    op.create_index('ix_health_monitors_org_id','health_monitors',['org_id'])
    op.create_table('health_samples',*identity(),
        sa.Column('monitor_id',sa.String(36),sa.ForeignKey('health_monitors.id'),nullable=False),
        sa.Column('status',sa.String(30),nullable=False),
        sa.Column('http_status',sa.Integer(),nullable=True),
        sa.Column('response_ms',sa.Float(),nullable=True),
        sa.Column('tls_expires',sa.Float(),nullable=True),
        sa.Column('incident',sa.Boolean(),nullable=False))
    op.create_index('ix_health_samples_monitor_id','health_samples',['monitor_id'])

def downgrade():
    op.drop_index('ix_health_samples_monitor_id',table_name='health_samples')
    op.drop_table('health_samples')
    op.drop_index('ix_health_monitors_org_id',table_name='health_monitors')
    op.drop_table('health_monitors')
