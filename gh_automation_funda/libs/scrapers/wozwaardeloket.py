"""Scrapers for WOZwaardeloket.nl."""

import asyncio
from datetime import datetime
from typing import Any, cast

from httpx import AsyncClient

URL_WOZWAARDELOKET = "https://www.wozwaardeloket.nl"
URL_WOZWAARDELOKET_SESSION_START = f"{URL_WOZWAARDELOKET}/wozwaardeloket-api/v1/session/start"
URL_WOZWAARDELOKET_DATA = f"{URL_WOZWAARDELOKET}/wozwaardeloket-api/v1/wozwaarde/nummeraanduiding"
URL_WOZ_SUGGEST = "https://api.pdok.nl/bzk/locatieserver/search/v3_1/suggest"
URL_WOZ_LOOKUP = "https://api.pdok.nl/bzk/locatieserver/search/v3_1/lookup"


# GET /wozwaardeloket-api/v1/wozwaarde/nummeraanduiding/0034200000011616 HTTP/1.1
# Accept: application/json, text/plain, */*
# Accept-Encoding: gzip, deflate, br
# Accept-Language: en-US,en;q=0.5
# Connection: keep-alive
# Cookie: LB_STICKY=9b03043202b42a83; SESSION=63A8C57358420059F146D6E81D41DCB1
# Host: www.wozwaardeloket.nl
# Referer: https://www.wozwaardeloket.nl/
# Sec-Fetch-Dest: empty
# Sec-Fetch-Mode: cors
# Sec-Fetch-Site: same-origin
# Sec-GPC: 1
# User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36
# sec-ch-ua: "Brave";v="119", "Chromium";v="119", "Not?A_Brand";v="24"
# sec-ch-ua-mobile: ?0
# sec-ch-ua-platform: "Linux"

HEADERS_WOZWAARDELOKET = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Host": "www.wozwaardeloket.nl",
    "Referer": "https://www.wozwaardeloket.nl/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Sec-GPC": "1",
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) " "AppleWebKit/537.36 (KHTML, like Gecko) " "Chrome/119.0.0.0 " "Safari/537.36"
    ),
    "sec-ch-ua": '"Brave";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
}


async def get_lookup_id_from_address(*, street_and_house_number: str, postal_code: str = "", city: str) -> str | None:
    """Get the URL for a property from WOZwaardeloket.nl.

    We do a GET https://api.pdok.nl/bzk/locatieserver/search/v3_1/suggest?q=Harderwijkoever%2016%2C%201324HA%20Almere&rows=10
    """
    address = f"{street_and_house_number}, {postal_code} {city}"
    params = {"q": address, "rows": "10"}

    async with AsyncClient(follow_redirects=True) as client:
        response = await client.get(URL_WOZ_SUGGEST, params=params)

    try:
        response.raise_for_status()
    except Exception as e:
        print(f"Error while reading WOZwaardeloket.nl: {e}")
        return None

    data = response.json()
    response_obj = data.get("response", {"numFound": 0, "numFoundExact": False})

    if response_obj["numFound"] == 0:
        print(f"Could not find URL for {address}")
        return None

    if response_obj["numFound"] > 1 or not response_obj["numFoundExact"]:
        print(f"Found ambiguous results for {address}")

    first_result = response_obj["docs"][0]

    if first_result["type"] != "adres":
        print(f"Found non-address result for {address}: {first_result['type']}")

    return cast(str, first_result["id"])


async def get_designation_id_from_lookup_id(lookup_id: str) -> str | None:
    """Get the designation ID for a property from WOZwaardeloket.nl.

    We do a GET https://api.pdok.nl/bzk/locatieserver/search/v3_1/lookup?fl=*&id=adr-ffe6e5dd684b70643d696c6b5e64f877

    """
    params = {"fl": "*", "id": lookup_id}

    async with AsyncClient(follow_redirects=True) as client:
        response = await client.get(URL_WOZ_LOOKUP, params=params)

    try:
        response.raise_for_status()
    except Exception as e:
        print(f"Error while reading WOZwaardeloket.nl: {e}")
        return None

    data = response.json()
    response_obj = data.get("response", {"numFound": 0, "numFoundExact": False})

    if response_obj["numFound"] == 0:
        print(f"Could not find URL for {lookup_id}")
        return None

    if response_obj["numFound"] > 1 or not response_obj["numFoundExact"]:
        print(f"Found ambiguous results for {lookup_id}")

    first_result = response_obj["docs"][0]

    if first_result["type"] != "adres":
        print(f"Found non-address result for {lookup_id}: {first_result['type']}")

    return cast(str, first_result["nummeraanduiding_id"])


async def get_woz_data(designation_id: str) -> list[dict[str, Any]]:
    """Get the data for a property from WOZwaardeloket.nl.

    We do a GET https://www.wozwaardeloket.nl/wozwaardeloket-api/v1/wozwaarde/nummeraanduiding/0363010000000003
    """
    url = f"{URL_WOZWAARDELOKET_DATA}/{designation_id}"

    async with AsyncClient(follow_redirects=True, headers=HEADERS_WOZWAARDELOKET) as client:
        await client.post(URL_WOZWAARDELOKET_SESSION_START)
        response = await client.get(url)

    try:
        response.raise_for_status()
    except Exception as e:
        print(f"Error while reading WOZwaardeloket.nl: {e}")
        return []

    data = response.json()

    woz_values = data.get("wozWaarden", [])

    return [
        {
            "year": reference_date.year,
            "reference_date": reference_date,
            "value": woz_value["vastgesteldeWaarde"],
        }
        for woz_value in woz_values
        if (reference_date := datetime.strptime(woz_value["peildatum"], "%Y-%m-%d").date())
    ]


async def get_property_woz_data(*, street_and_house_number: str, postal_code: str = "", city: str) -> dict[str, Any]:
    """Get the data for a property from WOZwaardeloket.nl."""
    lookup_id = await get_lookup_id_from_address(
        street_and_house_number=street_and_house_number, postal_code=postal_code, city=city
    )
    if not lookup_id:
        return {}

    designation_id = await get_designation_id_from_lookup_id(lookup_id)
    if not designation_id:
        return {}

    woz_data = await get_woz_data(designation_id)

    return {
        "woz_url": f"{URL_WOZWAARDELOKET_DATA}/{designation_id}",
        "woz_data": woz_data,
    }


async def main() -> None:
    """Run the main program."""
    # Kerkstraat 1, 1234AB Amsterdam
    data = await get_property_woz_data(street_and_house_number="Kerkstraat 1", postal_code="1234AB", city="Amsterdam")
    print(data)

    # Harderwijkoever 16, 1324HA Almere
    data = await get_property_woz_data(
        street_and_house_number="Harderwijkoever 16", postal_code="1324HA", city="Almere"
    )
    print(data)


if __name__ == "__main__":
    asyncio.run(main())
