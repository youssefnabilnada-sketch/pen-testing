"""Optional explicitly linked Firebase identities; existing accounts unchanged."""
from alembic import op
import sqlalchemy as sa
revision = '003_firebase'
down_revision = '002_intelligence'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('firebase_identities',
        sa.Column('id',sa.String(36),primary_key=True),
        sa.Column('created',sa.Float(),nullable=False),
        sa.Column('user_id',sa.String(36),sa.ForeignKey('users.id'),nullable=False,unique=True),
        sa.Column('project',sa.String(100),nullable=False),
        sa.Column('subject',sa.String(128),nullable=False),
        sa.UniqueConstraint('project','subject'))

def downgrade():
    op.drop_table('firebase_identities')
