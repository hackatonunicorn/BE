"""Initial database tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create startups table
    op.create_table('startups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('industry', sa.String(), nullable=False),
        sa.Column('stage', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('contact_person', sa.String(), nullable=False),
        sa.Column('pitch_deck_path', sa.String(), nullable=True),
        sa.Column('pitch_analysis_result', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_startups_id'), 'startups', ['id'], unique=False)
    op.create_index(op.f('ix_startups_name'), 'startups', ['name'], unique=False)
    op.create_index(op.f('ix_startups_industry'), 'startups', ['industry'], unique=False)
    op.create_index(op.f('ix_startups_stage'), 'startups', ['stage'], unique=False)
    op.create_index(op.f('ix_startups_email'), 'startups', ['email'], unique=False)

    # Create vc_funds table
    op.create_table('vc_funds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('focus_industries', sa.JSON(), nullable=False),
        sa.Column('investment_stages', sa.JSON(), nullable=False),
        sa.Column('geography', sa.String(), nullable=False),
        sa.Column('ticket_size_min', sa.Float(), nullable=True),
        sa.Column('ticket_size_max', sa.Float(), nullable=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('contact_info', sa.JSON(), nullable=True),
        sa.Column('matching_criteria', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vc_funds_id'), 'vc_funds', ['id'], unique=False)
    op.create_index(op.f('ix_vc_funds_name'), 'vc_funds', ['name'], unique=False)
    op.create_index(op.f('ix_vc_funds_email'), 'vc_funds', ['email'], unique=False)

    # Create communications table
    op.create_table('communications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('startup_id', sa.Integer(), nullable=False),
        sa.Column('vc_fund_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, default='initiated'),
        sa.Column('email_thread_id', sa.String(), nullable=True),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('generated_emails', sa.JSON(), nullable=True),
        sa.Column('escalated_to_human', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['startup_id'], ['startups.id'], ),
        sa.ForeignKeyConstraint(['vc_fund_id'], ['vc_funds.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communications_id'), 'communications', ['id'], unique=False)
    op.create_index(op.f('ix_communications_email_thread_id'), 'communications', ['email_thread_id'], unique=False)

    # Create meetings table
    op.create_table('meetings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('communication_id', sa.Integer(), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('meeting_link', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, default='scheduled'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['communication_id'], ['communications.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_meetings_id'), 'meetings', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order due to foreign key constraints
    op.drop_index(op.f('ix_meetings_id'), table_name='meetings')
    op.drop_table('meetings')
    
    op.drop_index(op.f('ix_communications_email_thread_id'), table_name='communications')
    op.drop_index(op.f('ix_communications_id'), table_name='communications')
    op.drop_table('communications')
    
    op.drop_index(op.f('ix_vc_funds_email'), table_name='vc_funds')
    op.drop_index(op.f('ix_vc_funds_name'), table_name='vc_funds')
    op.drop_index(op.f('ix_vc_funds_id'), table_name='vc_funds')
    op.drop_table('vc_funds')
    
    op.drop_index(op.f('ix_startups_email'), table_name='startups')
    op.drop_index(op.f('ix_startups_stage'), table_name='startups')
    op.drop_index(op.f('ix_startups_industry'), table_name='startups')
    op.drop_index(op.f('ix_startups_name'), table_name='startups')
    op.drop_index(op.f('ix_startups_id'), table_name='startups')
    op.drop_table('startups')
