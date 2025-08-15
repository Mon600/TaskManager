"""add all triggers for links and roles

Revision ID: dc2c818b945f
Revises: 8365d3f5b273
Create Date: 2025-07-26 22:28:06.735044

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from src.shared.db.triggers import TriggersManager

# revision identifiers, used by Alembic.
revision: str = 'dc2c818b945f'
down_revision: Union[str, Sequence[str], None] = '8365d3f5b273'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(TriggersManager.check_urls_count())

    op.execute(TriggersManager.get_links_limit_trigger())

    op.execute(TriggersManager.get_roles_counter())

    op.execute(TriggersManager.get_min_roles_limit())

    op.execute(TriggersManager.get_protect_default_role_function())

    op.execute(TriggersManager.get_protect_default_role_trigger())

    op.execute(TriggersManager.get_protect_important_roles_function())

    op.execute(TriggersManager.get_protect_important_roles_triggers_on_delete())

    op.execute(TriggersManager.get_protect_important_roles_triggers_on_update())


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS protect_important_roles_update ON roles;")
    op.execute("DROP TRIGGER IF EXISTS protect_important_roles_delete ON roles;")
    op.execute("DROP TRIGGER IF EXISTS protect_default_role_trigger ON roles;")
    op.execute("DROP TRIGGER IF EXISTS min_roles_limit ON roles;")
    op.execute("DROP TRIGGER IF EXISTS links_limit_trigger ON links;")

    print("Dropped all triggers")

    op.execute("DROP FUNCTION IF EXISTS protect_important_roles();")
    op.execute("DROP FUNCTION IF EXISTS protect_default_or_creator_role();")
    op.execute("DROP FUNCTION IF EXISTS check_roles_counter();")
    op.execute("DROP FUNCTION IF EXISTS check_urls_count();")
