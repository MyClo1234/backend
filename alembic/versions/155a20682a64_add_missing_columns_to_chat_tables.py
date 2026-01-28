"""add_missing_columns_to_chat_tables

Revision ID: 155a20682a64
Revises: c6f1f41c8389
Create Date: 2026-01-28 11:09:28.610272

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import func


# revision identifiers, used by Alembic.
revision: str = '155a20682a64'
down_revision: Union[str, Sequence[str], None] = 'c6f1f41c8389'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # chat_sessions 테이블에 누락된 컬럼 추가
    op.add_column(
        'chat_sessions',
        sa.Column('finished_at', sa.DateTime(), nullable=True)
    )
    op.add_column(
        'chat_sessions',
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=func.now(),
            nullable=False
        )
    )
    
    # chat_messages 테이블에 누락된 컬럼 추가
    op.add_column(
        'chat_messages',
        sa.Column('content', sa.Text(), nullable=True)  # 기존 데이터를 위해 nullable=True로 시작
    )
    op.add_column(
        'chat_messages',
        sa.Column('node_name', sa.String(), nullable=True)
    )
    op.add_column(
        'chat_messages',
        sa.Column(
            'message_metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True
        )
    )
    op.add_column(
        'chat_messages',
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=func.now(),
            nullable=False
        )
    )
    
    # 기존 데이터가 있다면 content에 기본값 설정
    # extracted_5w1h가 있으면 JSON 문자열로 변환, 없으면 빈 문자열
    op.execute("""
        UPDATE chat_messages 
        SET content = COALESCE(
            extracted_5w1h::text,
            ''
        )
        WHERE content IS NULL
    """)
    
    # content를 NOT NULL로 변경
    op.alter_column('chat_messages', 'content', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # chat_messages 테이블에서 추가한 컬럼 제거
    op.drop_column('chat_messages', 'created_at')
    op.drop_column('chat_messages', 'message_metadata')
    op.drop_column('chat_messages', 'node_name')
    op.drop_column('chat_messages', 'content')
    
    # chat_sessions 테이블에서 추가한 컬럼 제거
    op.drop_column('chat_sessions', 'created_at')
    op.drop_column('chat_sessions', 'finished_at')
