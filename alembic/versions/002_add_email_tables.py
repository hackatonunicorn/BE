"""Add email and email_thread tables

Revision ID: 002_add_email_tables
Revises: 001_initial_tables
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_email_tables'
down_revision = '001_initial_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Create email_threads table
    op.create_table('email_threads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('thread_id', sa.String(), nullable=False),
        sa.Column('communication_id', sa.Integer(), nullable=True),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('total_emails', sa.Integer(), nullable=True),
        sa.Column('last_email_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['communication_id'], ['communications.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_threads_id'), 'email_threads', ['id'], unique=False)
    op.create_index(op.f('ix_email_threads_thread_id'), 'email_threads', ['thread_id'], unique=True)

    # Create emails table
    op.create_table('emails',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email_thread_id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.String(), nullable=False),
        sa.Column('sender_email', sa.String(), nullable=False),
        sa.Column('recipient_email', sa.String(), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('html_body', sa.Text(), nullable=True),
        sa.Column('direction', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('delivery_status', sa.JSON(), nullable=True),
        sa.Column('headers', sa.JSON(), nullable=True),
        sa.Column('attachments', sa.JSON(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('opened_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('clicked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['email_thread_id'], ['email_threads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_emails_id'), 'emails', ['id'], unique=False)
    op.create_index(op.f('ix_emails_message_id'), 'emails', ['message_id'], unique=True)
    op.create_index(op.f('ix_emails_sender_email'), 'emails', ['sender_email'], unique=False)
    op.create_index(op.f('ix_emails_recipient_email'), 'emails', ['recipient_email'], unique=False)


def downgrade():
    # Drop emails table
    op.drop_index(op.f('ix_emails_recipient_email'), table_name='emails')
    op.drop_index(op.f('ix_emails_sender_email'), table_name='emails')
    op.drop_index(op.f('ix_emails_message_id'), table_name='emails')
    op.drop_index(op.f('ix_emails_id'), table_name='emails')
    op.drop_table('emails')

    # Drop email_threads table
    op.drop_index(op.f('ix_email_threads_thread_id'), table_name='email_threads')
    op.drop_index(op.f('ix_email_threads_id'), table_name='email_threads')
    op.drop_table('email_threads')
