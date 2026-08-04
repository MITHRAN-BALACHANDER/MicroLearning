"""
Lightweight, idempotent schema upgrades.

`Base.metadata.create_all` adds new *tables* but never new *columns*, so an
existing microlearning.db would break when the multi-platform columns landed.
This runs additive ALTERs that are safe to execute on every startup and work on
both SQLite and PostgreSQL.

Alembic remains the tool for anything destructive; this only ever adds columns
and backfills them.
"""
from typing import List

from loguru import logger
from sqlalchemy import inspect, text

# (table, column, DDL type, backfill SQL or None)
_ADDITIVE_COLUMNS = [
    ("users", "platform", "VARCHAR", "UPDATE users SET platform = 'telegram' WHERE platform IS NULL"),
    ("users", "platform_user_id", "VARCHAR",
     "UPDATE users SET platform_user_id = telegram_id WHERE platform_user_id IS NULL"),
    ("users", "last_inbound_at", "TIMESTAMP", None),
]


def _existing_columns(inspector, table: str) -> List[str]:
    try:
        return [column["name"] for column in inspector.get_columns(table)]
    except Exception:  # table does not exist yet - create_all will handle it
        return []


def ensure_schema(engine) -> List[str]:
    """
    Apply additive migrations. Returns the list of changes made (empty when the
    schema is already current), so callers can log a meaningful startup message.
    """
    applied: List[str] = []
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    with engine.begin() as connection:
        for table, column, ddl_type, backfill in _ADDITIVE_COLUMNS:
            if table not in tables:
                continue
            if column in _existing_columns(inspector, table):
                continue

            connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}"))
            applied.append(f"{table}.{column}")
            logger.info(f"Schema upgrade: added {table}.{column}")

            if backfill:
                connection.execute(text(backfill))
                logger.info(f"Schema upgrade: backfilled {table}.{column}")

    if applied:
        logger.info(f"Applied {len(applied)} schema upgrade(s): {', '.join(applied)}")

    return applied
