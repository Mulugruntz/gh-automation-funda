"""Dynamic settings for the application."""

import csv
from io import StringIO
from typing import TypeVar

import httpx
from pydantic import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)


async def read_google_sheets(sheet_id: str, gid: str, model_class: type[ModelT]) -> list[ModelT]:
    """Read a publicly available Google Sheet and return its contents as a list of Pydantic models.

    Params:
        sheet_id: The ID of the Google Sheet.
        gid: The ID of the sheet within the Google Sheet.
        model_class: The Pydantic model class to use for the data.

    Returns:
        A list of Pydantic models representing each row in the Google Sheet.
    """
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid={gid}"
    rows: list[ModelT] = []

    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        print(f"Error while reading Google Sheet: {e}")
        return rows

    csv_data = StringIO(response.text)
    csv_reader = csv.DictReader(csv_data)

    row: dict[str, str]
    for row in csv_reader:
        try:
            row_instance = model_class(**{k: v for k, v in row.items() if k in model_class.__annotations__})
            rows.append(row_instance)
        except Exception as e:
            print(f"Skipping row {row} due to error: {e}")

    return rows


# Define your Pydantic models based on the known structure of the Google Sheet.
class MyRow(BaseModel):
    id: int
    quote: str
    author: str
