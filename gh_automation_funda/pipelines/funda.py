"""An ETL pipeline for Funda.nl data."""

from gh_automation_funda.config import Config
from gh_automation_funda.libs.logic.funda import Funda


async def cmd_funda(config: Config) -> None:
    """
    For now, do nothing.
    """
    typer.echo("Pipeline: funda")
