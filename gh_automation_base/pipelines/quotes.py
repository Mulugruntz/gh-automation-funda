"""An example ETL pipeline that extracts quotes from an API and loads them to a database."""
from dataclasses import dataclass
from datetime import datetime
from typing import cast, Any

import asyncpg
import httpx
from pydantic import BaseModel
import typer

from gh_automation_base.config import Config
from gh_automation_base.pipelines.etl import AsyncETL


class Quote(BaseModel):
    id: int
    quote: str
    author: str
    created_at: datetime | None = None


@dataclass(frozen=True)
class Result:
    success: bool
    status: str
    quote: Quote


class QuotesETL(AsyncETL[dict[str, Any], Quote, Result]):
    async def _get_last_id(self) -> int:
        """
        Get the last ID from the database.
        """
        connection = await asyncpg.connect(self.config.postgres.dsn)
        try:
            result = await connection.fetch(
                "SELECT id FROM quotes ORDER BY id DESC LIMIT 1;"
            )
            if len(result) == 0:
                return 0
            return int(result[0][0])
        finally:
            await connection.close()

    async def extract(self) -> dict[str, Any]:
        """
        Extract data from the quotes API.
        """
        last_id = await self._get_last_id()

        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://dummyjson.com/quotes/{last_id + 1}")
            response.raise_for_status()

        return cast(dict[str, Any], response.json())

    async def transform(self, data: dict[str, Any]) -> Quote:
        """
        Transform and validate the extracted data.
        """
        return Quote(**data)

    async def load(self, data: Quote) -> Result:
        """
        Load the transformed data to the database.
        """
        connection = await asyncpg.connect(self.config.postgres.dsn)
        try:
            await connection.execute(
                """
                INSERT INTO quotes (id, quote, author)
                VALUES ($1, $2, $3)
                ON CONFLICT (id) DO NOTHING;
                """,
                data.id,
                data.quote,
                data.author,
            )
            return Result(success=True, status="Inserted", quote=data)
        except asyncpg.exceptions.PostgresError as e:
            return Result(success=False, status=str(e), quote=data)
        except Exception as e:
            return Result(success=False, status=str(e), quote=data)
        finally:
            await connection.close()


async def cmd_quotes(config: Config) -> None:
    """
    Extract quotes from the quotes API and load them to the database.
    """
    etl = QuotesETL(config)
    data = await etl.extract()
    transformed_data = await etl.transform(data)
    result = await etl.load(transformed_data)
    if result.success:
        typer.echo(f"{result.status} quote {result.quote.id}: {result.quote.quote}")
    else:
        typer.echo(
            f"Failed to load quote {result.quote.id}: {result.quote.quote}.", err=True
        )
        typer.echo(f"Error: {result.status}", err=True)
