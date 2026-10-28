"""Explicit client portfolio delegation and report branding."""
from alembic import op
import sqlalchemy as sa
revision='013_agency'
down_revision='012_launch'
branch_labels=None
depends_on=None
def ident():return [sa.Column('id',sa.String(36),primary_key=True),sa.Column('created',sa.Float(),nullable=False)]
def upgrade():
    op.create_table('agency_grants',*ident(),sa.Column('agency_id',sa.String(36),sa.ForeignKey('organizations.id'),nullable=False),sa.Column('client_id',sa.String(36),sa.ForeignKey('organizations.id'),nullable=False),sa.Column('expires',sa.Float(),nullable=False),sa.Column('revoked',sa.Boolean(),nullable=False),sa.Column('reports',sa.Boolean(),nullable=False),sa.UniqueConstraint('agency_id','client_id'))
    op.create_index('ix_agency_grants_agency_id','agency_grants',['agency_id'])
    op.create_table('agency_brands',*ident(),sa.Column('org_id',sa.String(36),sa.ForeignKey('organizations.id'),nullable=False,unique=True),sa.Column('settings',sa.JSON(),nullable=False))
def downgrade():
    op.drop_table('agency_brands');op.drop_index('ix_agency_grants_agency_id',table_name='agency_grants');op.drop_table('agency_grants')
