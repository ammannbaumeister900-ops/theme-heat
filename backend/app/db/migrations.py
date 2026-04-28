from __future__ import annotations

import logging

from sqlalchemy import Engine, text


logger = logging.getLogger(__name__)


def run_startup_migrations(engine: Engine) -> None:
    if engine.dialect.name != "postgresql":
        return

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE themes DROP CONSTRAINT IF EXISTS themes_name_key"))
        connection.execute(text("ALTER TABLE themes DROP CONSTRAINT IF EXISTS themes_code_key"))
        connection.execute(text("DROP INDEX IF EXISTS ix_themes_name"))
        connection.execute(text("DROP INDEX IF EXISTS ix_themes_code"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_themes_name ON themes (name)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_themes_code ON themes (code)"))
        connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_themes_name_type "
                "ON themes (name, theme_type)"
            )
        )
    logger.info("startup migrations completed")
