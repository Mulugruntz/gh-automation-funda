"""An ETL pipeline for Funda.nl data."""

from gh_automation_funda.config import Config
from gh_automation_funda.libs.logic.funda import Funda


async def cmd_funda(config: Config) -> None:
    """
    Retrieve new properties from Funda.nl, and data from kadasterdata.nl and wozwaardeloket.nl.
    """
    funda_logic = Funda(config=config)
    await funda_logic.get_new_properties()
