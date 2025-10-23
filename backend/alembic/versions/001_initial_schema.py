"""Initial schema with all Phase 1 and 2 tables

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-10-23 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create knowledge_chunks table
    op.create_table(
        'knowledge_chunks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('repo_name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('section_title', sa.String(500), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(384), nullable=False),
        sa.Column('accuracy_weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_knowledge_chunks_id'), 'knowledge_chunks', ['id'], unique=False)
    op.create_index(op.f('ix_knowledge_chunks_repo_name'), 'knowledge_chunks', ['repo_name'], unique=False)
    
    # Create vector index for embedding similarity search
    op.execute(
        'CREATE INDEX ix_knowledge_chunks_embedding ON knowledge_chunks '
        'USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)'
    )
    
    # Create approved_questions table
    op.create_table(
        'approved_questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('embedding', Vector(384), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('question')
    )
    op.create_index(op.f('ix_approved_questions_id'), 'approved_questions', ['id'], unique=False)
    op.create_index(op.f('ix_approved_questions_category'), 'approved_questions', ['category'], unique=False)
    op.create_index(op.f('ix_approved_questions_is_active'), 'approved_questions', ['is_active'], unique=False)
    
    # Create vector index for question similarity search
    op.execute(
        'CREATE INDEX ix_approved_questions_embedding ON approved_questions '
        'USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)'
    )
    
    # Create training_sessions table
    op.create_table(
        'training_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('response', sa.Text(), nullable=False),
        sa.Column('reasoning_chain', JSON, nullable=False),
        sa.Column('retrieved_chunks', JSON, nullable=False),
        sa.Column('workflow_context', JSON, nullable=True),
        sa.Column('llm_provider', sa.String(50), nullable=False),
        sa.Column('llm_model', sa.String(100), nullable=True),
        sa.Column('generation_time_ms', sa.Float(), nullable=True),
        sa.Column('has_feedback', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_correct', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_training_sessions_id'), 'training_sessions', ['id'], unique=False)
    
    # Create workflow_vectors table
    op.create_table(
        'workflow_vectors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('reasoning_summary', sa.Text(), nullable=False),
        sa.Column('workflow_embedding', Vector(384), nullable=False),
        sa.Column('is_successful', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['training_sessions.id'])
    )
    op.create_index(op.f('ix_workflow_vectors_id'), 'workflow_vectors', ['id'], unique=False)
    op.create_index(op.f('ix_workflow_vectors_session_id'), 'workflow_vectors', ['session_id'], unique=False)
    
    # Create vector index for workflow similarity search
    op.execute(
        'CREATE INDEX ix_workflow_vectors_embedding ON workflow_vectors '
        'USING ivfflat (workflow_embedding vector_cosine_ops) WITH (lists = 100)'
    )
    
    # Create training_feedback table
    op.create_table(
        'training_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('feedback_type', sa.String(50), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('user_correction', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['training_sessions.id'])
    )
    op.create_index(op.f('ix_training_feedback_id'), 'training_feedback', ['id'], unique=False)
    op.create_index(op.f('ix_training_feedback_session_id'), 'training_feedback', ['session_id'], unique=False)
    
    # Create embedding_links table
    op.create_table(
        'embedding_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('chunk_id', sa.Integer(), nullable=False),
        sa.Column('similarity_score', sa.Float(), nullable=False),
        sa.Column('rank_position', sa.Integer(), nullable=False),
        sa.Column('was_useful', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['training_sessions.id']),
        sa.ForeignKeyConstraint(['chunk_id'], ['knowledge_chunks.id'])
    )
    op.create_index(op.f('ix_embedding_links_id'), 'embedding_links', ['id'], unique=False)
    op.create_index(op.f('ix_embedding_links_session_id'), 'embedding_links', ['session_id'], unique=False)
    op.create_index(op.f('ix_embedding_links_chunk_id'), 'embedding_links', ['chunk_id'], unique=False)


def downgrade() -> None:
    op.drop_table('embedding_links')
    op.drop_table('training_feedback')
    op.drop_table('workflow_vectors')
    op.drop_table('training_sessions')
    op.drop_table('approved_questions')
    op.drop_table('knowledge_chunks')
    op.execute('DROP EXTENSION IF EXISTS vector')

