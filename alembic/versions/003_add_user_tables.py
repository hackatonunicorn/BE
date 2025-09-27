"""Add user tables

Revision ID: 003
Revises: 002
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum type for user roles
    user_role_enum = postgresql.ENUM('startup', 'vc_fund', 'admin', name='userrole')
    user_role_enum.create(op.get_bind())
    
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('first_name', sa.String(length=50), nullable=False),
        sa.Column('last_name', sa.String(length=50), nullable=False),
        sa.Column('company_name', sa.String(length=100), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', user_role_enum, nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('is_superuser', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for users table
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Add owner_id column to startups table
    op.add_column('startups', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_startups_owner_id', 'startups', 'users', ['owner_id'], ['id'])
    op.create_index(op.f('ix_startups_owner_id'), 'startups', ['owner_id'], unique=False)
    
    # Update existing startups to have a default owner (if any exist)
    # This would need to be handled in production with proper data migration


def downgrade():
    # Remove foreign key and column from startups
    op.drop_constraint('fk_startups_owner_id', 'startups', type_='foreignkey')
    op.drop_index(op.f('ix_startups_owner_id'), table_name='startups')
    op.drop_column('startups', 'owner_id')
    
    # Drop users table
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
    
    # Drop enum type
    user_role_enum = postgresql.ENUM('startup', 'vc_fund', 'admin', name='userrole')
    user_role_enum.drop(op.get_bind())
