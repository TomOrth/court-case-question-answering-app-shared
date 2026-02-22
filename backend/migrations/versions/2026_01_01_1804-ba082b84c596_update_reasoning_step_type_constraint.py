"""update reasoning step_type constraint

Revision ID: ba082b84c596
Revises: a9cc213a5102
Create Date: 2026-01-01 18:04:33.999050

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba082b84c596'
down_revision: Union[str, None] = 'a9cc213a5102'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('valid_step_type', 'reasoning_steps', type_='check')
    op.create_check_constraint(
        'valid_step_type',
        'reasoning_steps',
        "step_type IN ('gathered_context', 'reasoning', 'tool_call', 'tool_result')"
    )


def downgrade() -> None:
    op.drop_constraint('valid_step_type', 'reasoning_steps', type_='check')
    op.create_check_constraint(
        'valid_step_type',
        'reasoning_steps',
        "step_type IN ('gathered_context', 'reasoning_step', 'tool_call', 'tool_result')"
    )
