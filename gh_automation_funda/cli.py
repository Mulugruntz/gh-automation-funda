"""Console script for GitHub Automation Base."""

import typer
import asyncpg
import asyncio

from gh_automation_funda.config import Config

app = typer.Typer()


async def time_async() -> None:
    """Get the time from the DB and prints it."""
    config = Config()
    connection = await asyncpg.connect(config.postgres.dsn)
    try:
        result = await connection.fetch("SELECT now();")
        typer.echo(result[0][0])
    finally:
        await connection.close()


@app.command()
def time() -> None:
    """Show the time in the DB."""
    asyncio.run(time_async())


@app.command()
def dsn() -> None:
    """Print the DSN."""
    config = Config()
    typer.echo(config.postgres.dsn)


@app.command()
def init() -> None:
    """Initialize a new project"""
    from gh_automation_funda.persistence.init import cmd_init

    config = Config()
    asyncio.run(cmd_init(config))


@app.command()
def clean() -> None:
    """Clean the database"""
    from gh_automation_funda.persistence.init import cmd_clean

    config = Config()
    asyncio.run(cmd_clean(config))


@app.command()
def funda() -> None:
    """Run the funda pipeline"""
    from gh_automation_funda.pipelines.funda import cmd_funda

    config = Config()
    asyncio.run(cmd_funda(config))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
