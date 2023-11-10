"""Scrapers for Kadasterdata.nl."""

import asyncio
import re
from datetime import datetime
from typing import Any, Final, cast

from bs4 import BeautifulSoup
from httpx import AsyncClient

URL_KADASTERDATA: Final[str] = "https://www.kadasterdata.nl"
URL_KADASTERDATA_SEARCH: Final[str] = f"{URL_KADASTERDATA}/api-hd/autocomplete"
RE_MONEY_VALUE_EURO: Final[re.Pattern[str]] = re.compile(r"€\s+([\d\.]+)")
RE_VALUE_CALCULATED_ON: Final[re.Pattern[str]] = re.compile(r"Berekend op (\d{2}-\d{2}-\d{4})")


async def get_cadaster_url_from_address(
    *, street_and_house_number: str, postal_code: str = "", city: str
) -> str | None:
    """Get the URL for a property from Kadasterdata.nl."""
    address = f"{street_and_house_number}, {postal_code} {city}"
    params = {"q": address}

    async with AsyncClient(follow_redirects=True) as client:
        response = await client.post(URL_KADASTERDATA_SEARCH, params=params)

    try:
        response.raise_for_status()
    except Exception as e:
        print(f"Error while reading Kadasterdata.nl: {e}")
        return None

    data = response.json()
    properties = data.get("properties", [])
    if not properties:
        print(f"Could not find cadaster URL for {address}. Property is probably too new.")
        return None

    url = cast(str | None, properties[0].get("url"))

    if not url:
        print(f"Could not find cadaster URL for {address}. Property is probably too new.")
        return None

    return url


async def get_property_cadaster_data(url: str) -> dict[str, Any] | None:
    """Get the data for a property from Kadasterdata.nl."""
    out_when_incomplete = {
        "cadastral_url": url,
        "value_min": None,
        "value_max": None,
        "value_calculated_on": None,
    }

    async with AsyncClient(follow_redirects=True) as client:
        response = await client.get(url)

    try:
        response.raise_for_status()
    except Exception as e:
        print(f"Error while reading Kadasterdata.nl: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    summary_amount = soup.find("div", class_="page-summary__amount")
    summary_date = soup.find("div", class_="page-summary__date")

    if not summary_amount or not summary_date:
        print(f"Could not find cadaster summary for {url}")
        return out_when_incomplete

    values = RE_MONEY_VALUE_EURO.findall(summary_amount.text)
    if len(values) != 2:
        print(f"Could not find cadaster value for {url}")
        return out_when_incomplete

    value_min, value_max = values
    value_min = int(value_min.replace(".", ""))
    value_max = int(value_max.replace(".", ""))

    value_calculated_on = RE_VALUE_CALCULATED_ON.findall(summary_date.text)
    if not value_calculated_on:
        print(f"Could not find cadaster value calculated on for {url}")
        return out_when_incomplete

    return {
        "cadastral_url": url,
        "value_min": value_min,
        "value_max": value_max,
        "value_calculated_on": datetime.strptime(value_calculated_on[0], "%d-%m-%Y").date(),
    }


async def main() -> None:
    """Run the main function."""
    # Kerkstraat 1, 1234AB Amsterdam
    url = await get_cadaster_url_from_address(
        street_and_house_number="Kerkstraat 1", postal_code="1234AB", city="Amsterdam"
    )
    print(url)
    assert url is None

    # Harderwijkoever 16, 1324HA Almere
    url2 = await get_cadaster_url_from_address(
        street_and_house_number="Harderwijkoever 16", postal_code="1324HA", city="Almere"
    )
    print(url2)
    assert url2 == "https://www.kadasterdata.nl/almere/harderwijkoever/16"

    data = await get_property_cadaster_data(url2)
    print(data)


if __name__ == "__main__":
    asyncio.run(main())
