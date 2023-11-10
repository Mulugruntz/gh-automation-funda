"""Commands to initialize and clean the database."""

import asyncio
from typing import cast

import asyncpg
from typer import echo, prompt
from yoyo import get_backend
from yoyo.backends import PostgresqlPsycopgBackend

from gh_automation_funda.config import Config
from gh_automation_funda.persistence.dsn import DSN


async def initialize_database(config: Config) -> None:
    """Initialize the database."""
    super_dsn = prompt("Please provide a DSN to access the data with priviledged user.")
    connection = await asyncpg.connect(super_dsn)
    try:
        await connection.execute(f"CREATE DATABASE {config.postgres.database};")
        echo(f"Created database {config.postgres.database}")
        await connection.execute(f"CREATE USER {config.postgres.user} WITH PASSWORD '{config.postgres.password}';")
        echo(f"Created user {config.postgres.user}")
        await connection.execute(
            f"GRANT ALL PRIVILEGES ON DATABASE {config.postgres.database}" f" TO {config.postgres.user};"
        )
        echo(f"Granted all privileges on database {config.postgres.database} " f"to user {config.postgres.user}")
    finally:
        await connection.close()

    dsn = DSN.from_uri(super_dsn)
    dsn.database = config.postgres.database
    super_dsn_new = str(dsn)
    connection = await asyncpg.connect(super_dsn_new)
    try:
        await connection.execute(f"CREATE SCHEMA {config.postgres.db_schema};")
        echo(f"Created schema {config.postgres.db_schema}")
        await connection.execute(
            f"GRANT ALL PRIVILEGES ON SCHEMA {config.postgres.db_schema} TO {config.postgres.user};"
        )
        echo(f"Granted all privileges on schema {config.postgres.db_schema}" f" to user {config.postgres.user}.")
        await connection.execute(f"ALTER ROLE {config.postgres.user} SET search_path TO {config.postgres.db_schema};")
    finally:
        echo("Never using the super user again.")
        await connection.close()


async def check_if_database_exists(config: Config) -> bool:
    """Check if the database exists."""
    try:
        connection = await asyncpg.connect(config.postgres.dsn)
    except asyncpg.exceptions.PostgresError:
        return False
    else:
        await connection.close()

    return True


async def check_if_yoyo_tables_exist(config: Config, required_tables: list[str]) -> bool:
    """Check if the required yoyo tables exist."""
    try:
        connection = await asyncpg.connect(config.postgres.dsn)
        await connection.fetch("SELECT now();")
        # check all the required tables exist
        table_count = await connection.fetch(
            "SELECT count(*) FROM pg_catalog.pg_tables WHERE tablename = ANY($1);",
            required_tables,
        )
        return bool(table_count[0][0] == len(required_tables))
    except asyncpg.exceptions.InvalidCatalogNameError:
        return False
    finally:
        await connection.close()


async def cmd_init(config: Config) -> None:
    """Initialize a new project, to work with yoyo migrations."""
    if not await check_if_database_exists(config):
        echo(f"Database {config.postgres.database} does not exist. Creating it.")
        await initialize_database(config)

    if not await check_if_yoyo_tables_exist(config, required_tables=[PostgresqlPsycopgBackend.lock_table]):
        echo(f"Database {config.postgres.database} does not have the required yoyo tables." f" Creating them.")
        backend = cast(PostgresqlPsycopgBackend, get_backend(config.postgres.yoyo_dns))
        tables = backend.list_tables()
        echo(tables)
    else:
        echo(f"Database {config.postgres.database} has the required yoyo tables. Skipping creation.")


async def cmd_clean(config: Config) -> None:
    """Clean the database"""
    echo("Dropping the database and the user.")
    super_dsn = prompt("Please provide a DSN to access the data with priviledged user.")
    connection = await asyncpg.connect(super_dsn)
    try:
        await connection.execute(f"DROP DATABASE IF EXISTS {config.postgres.database};")
        echo(f"Dropped database {config.postgres.database}, if it existed.")
        await connection.execute(f"DROP USER IF EXISTS {config.postgres.user};")
        echo(f"Dropped user {config.postgres.user}, if it existed.")
    finally:
        await connection.close()


if __name__ == "__main__":
    config = Config()
    asyncio.run(cmd_init(config))
