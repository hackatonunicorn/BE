"""Add campaign tables

Revision ID: 004
Revises: 003
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types for campaigns
    campaign_status_enum = postgresql.ENUM('draft', 'active', 'paused', 'completed', name='campaignstatus')
    campaign_status_enum.create(op.get_bind())
    
    industry_enum = postgresql.ENUM(
        'saas', 'fintech', 'healthtech', 'edtech', 'ecommerce', 'marketplace', 
        'ai_ml', 'blockchain', 'gaming', 'media', 'real_estate', 'transportation', 
        'energy', 'manufacturing', 'agriculture', 'security', name='industry'
    )
    industry_enum.create(op.get_bind())
    
    funding_stage_enum = postgresql.ENUM('preseed', 'seed', 'series_a', 'series_b', 'series_c_plus', name='fundingstage')
    funding_stage_enum.create(op.get_bind())
    
    team_size_enum = postgresql.ENUM('1-5', '6-20', '21-50', '51-100', '100+', name='teamsize')
    team_size_enum.create(op.get_bind())
    
    fundraising_timeline_enum = postgresql.ENUM('3-6 months', '6-12 months', '12+ months', name='fundraisingtimeline')
    fundraising_timeline_enum.create(op.get_bind())
    
    previous_funding_enum = postgresql.ENUM('none', 'friends_family', 'angel_investors', 'seed_round', 'series_a', 'series_b_plus', name='previousfunding')
    previous_funding_enum.create(op.get_bind())
    
    # Create campaigns table
    op.create_table('campaigns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('startup_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', campaign_status_enum, nullable=False),
        sa.Column('company_name', sa.String(length=200), nullable=False),
        sa.Column('company_website', sa.String(length=500), nullable=True),
        sa.Column('industry', industry_enum, nullable=False),
        sa.Column('current_funding_stage', funding_stage_enum, nullable=False),
        sa.Column('team_size', team_size_enum, nullable=False),
        sa.Column('location', sa.String(length=200), nullable=False),
        sa.Column('pitch_deck_url', sa.String(length=500), nullable=True),
        sa.Column('target_raise_amount', sa.Float(), nullable=False),
        sa.Column('fundraising_timeline', fundraising_timeline_enum, nullable=False),
        sa.Column('use_of_funds', sa.JSON(), nullable=False),
        sa.Column('previous_funding', previous_funding_enum, nullable=False),
        sa.Column('sent_count', sa.Integer(), nullable=False),
        sa.Column('replied_count', sa.Integer(), nullable=False),
        sa.Column('meetings_count', sa.Integer(), nullable=False),
        sa.Column('response_rate', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('launched_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['startup_id'], ['startups.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for campaigns table
    op.create_index(op.f('ix_campaigns_id'), 'campaigns', ['id'], unique=False)
    op.create_index(op.f('ix_campaigns_user_id'), 'campaigns', ['user_id'], unique=False)
    op.create_index(op.f('ix_campaigns_startup_id'), 'campaigns', ['startup_id'], unique=False)
    op.create_index(op.f('ix_campaigns_status'), 'campaigns', ['status'], unique=False)
    
    # Add campaign_id column to communications table
    op.add_column('communications', sa.Column('campaign_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_communications_campaign_id', 'communications', 'campaigns', ['campaign_id'], ['id'])
    op.create_index(op.f('ix_communications_campaign_id'), 'communications', ['campaign_id'], unique=False)


def downgrade():
    # Remove campaign_id column from communications table
    op.drop_constraint('fk_communications_campaign_id', 'communications', type_='foreignkey')
    op.drop_index(op.f('ix_communications_campaign_id'), table_name='communications')
    op.drop_column('communications', 'campaign_id')
    
    # Drop campaigns table
    op.drop_index(op.f('ix_campaigns_status'), table_name='campaigns')
    op.drop_index(op.f('ix_campaigns_startup_id'), table_name='campaigns')
    op.drop_index(op.f('ix_campaigns_user_id'), table_name='campaigns')
    op.drop_index(op.f('ix_campaigns_id'), table_name='campaigns')
    op.drop_table('campaigns')
    
    # Drop enum types
    previous_funding_enum = postgresql.ENUM('none', 'friends_family', 'angel_investors', 'seed_round', 'series_a', 'series_b_plus', name='previousfunding')
    previous_funding_enum.drop(op.get_bind())
    
    fundraising_timeline_enum = postgresql.ENUM('3-6 months', '6-12 months', '12+ months', name='fundraisingtimeline')
    fundraising_timeline_enum.drop(op.get_bind())
    
    team_size_enum = postgresql.ENUM('1-5', '6-20', '21-50', '51-100', '100+', name='teamsize')
    team_size_enum.drop(op.get_bind())
    
    funding_stage_enum = postgresql.ENUM('preseed', 'seed', 'series_a', 'series_b', 'series_c_plus', name='fundingstage')
    funding_stage_enum.drop(op.get_bind())
    
    industry_enum = postgresql.ENUM(
        'saas', 'fintech', 'healthtech', 'edtech', 'ecommerce', 'marketplace', 
        'ai_ml', 'blockchain', 'gaming', 'media', 'real_estate', 'transportation', 
        'energy', 'manufacturing', 'agriculture', 'security', name='industry'
    )
    industry_enum.drop(op.get_bind())
    
    campaign_status_enum = postgresql.ENUM('draft', 'active', 'paused', 'completed', name='campaignstatus')
    campaign_status_enum.drop(op.get_bind())
