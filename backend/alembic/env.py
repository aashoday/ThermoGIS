from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

import sys
import os
sys.path.append(os.getcwd())

from app.config import settings
from app.database import Base
from app.models import Hotspot, IndustrialAsset  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Only let Alembic manage tables we actually defined.
# Without this, autogenerate picks up postgis/tiger_geocoder's own
# tables (layer, county, state, faces, etc.) as "should be dropped".
OUR_TABLES = {"hotspots", "industrial_assets"}


def include_object(object_, name, type_, reflected, compare_to):
    if type_ == "table":
        return name in OUR_TABLES
    if type_ == "index":
        return object_.table.name in OUR_TABLES
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        include_object=include_object,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",````````
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()