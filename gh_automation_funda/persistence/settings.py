"""Dynamic settings for the application."""

import csv
import json
from io import StringIO
from logging import getLogger
from typing import Annotated, TypeVar

import httpx
from pydantic import BaseModel, BeforeValidator

logger = getLogger(__name__)

ModelT = TypeVar("ModelT", bound=BaseModel)


async def read_google_sheets(sheet_id: str, gid: str, model_class: type[ModelT]) -> list[ModelT]:
    """Read a publicly available Google Sheet and return its contents as a list of Pydantic models.

    Params:
        sheet_id: The ID of the Google Sheet.
        gid: The ID of the sheet within the Google Sheet.
        model_class: The Pydantic model class to use for the data.

    Returns:
        A list of Pydantic models representing each row in the Google Sheet.

    Raises:
        ValueError: If one or more rows are invalid.
    """
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid={gid}"
    rows: list[ModelT] = []

    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error(f"Error while reading Google Sheet: {e}")
        return rows

    csv_data = StringIO(response.text)
    csv_reader = csv.DictReader(csv_data)

    row: dict[str, str]
    all_rows_are_valid = True

    for row in csv_reader:
        try:
            row_instance = model_class(**{k: v for k, v in row.items() if k in model_class.__annotations__})
            rows.append(row_instance)
        except Exception as e:
            all_rows_are_valid = False
            logger.error(f"Skipping row {row} due to error: {e}")

    if not all_rows_are_valid:
        raise ValueError("Some rows are invalid.")

    return rows


# Define your Pydantic models based on the known structure of the Google Sheet.


class FundaSetting(BaseModel):
    """A Funda setting."""

    area: Annotated[list[str], BeforeValidator(json.loads), str]
    object_type: Annotated[list[str], BeforeValidator(json.loads), str]
    price_min: int
    price_max: int
    days_old: int
