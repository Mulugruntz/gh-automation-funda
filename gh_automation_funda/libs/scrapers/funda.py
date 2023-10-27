"""Scrapers for Funda.nl."""
from typing import Final

from httpx import AsyncClient
import json
import asyncio


FUNDA_SEARCH_URL: Final[str] = "https://www.funda.nl/zoeken/koop"
FUNDA_HEADERS: Final[dict[str, str]] = {
    "authority": "www.funda.nl",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "accept-language": "en-US,en;q=0.6",
    "cache-control": "max-age=0",
    "sec-ch-ua": '"Chromium";v="118", "Brave";v="118", "Not=A?Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "sec-gpc": "1",
    "upgrade-insecure-requests": "1",
    "user-agent": (
        "Mozilla/5.0 (X11; Linux x86_64) " "AppleWebKit/537.36 (KHTML, like Gecko) " "Chrome/118.0.0.0 Safari/537.36"
    ),
}


async def get_new_properties_url(*, area: list[str], price_min: int, price_max: int, days_old: int = 3) -> list[str]:
    """Get the new properties from Funda.nl.

    Example:
        https://www.funda.nl/zoeken/koop?selected_area=%5B%22almere%22%5D&price=%22300000-500000%22&publication_date=%223%22
    """
    areas = ",".join(f'"{a}"' for a in area)
    params = {
        "selected_area": f"[{areas}]",
        "price": f'"{price_min}-{price_max}"',
        "publication_date": f'"{days_old}"',
    }

    async with AsyncClient() as client:
        response = await client.get(FUNDA_SEARCH_URL, params=params, headers=FUNDA_HEADERS)

    try:
        response.raise_for_status()
    except Exception as e:
        print(f"Error while reading Funda.nl: {e}")
        return []

    start_tag = '<script type="application/ld+json">'
    end_tag = "</script>"
    payload = ""

    for line in response.text.splitlines():
        if start_tag in line and end_tag in line:
            idx_start = line.find(start_tag)
            idx_end = line[idx_start:].find(end_tag) + idx_start
            payload = line[idx_start + len(start_tag) : idx_end]
            break

    if not payload:
        return []

    data = json.loads(payload)

    return [item["url"] for item in data.get("itemListElement", [])]


async def main() -> None:
    """Main entry point."""
    urls = await get_new_properties_url(area=["almere"], price_min=300_000, price_max=500_000)
    print(urls)


if __name__ == "__main__":
    asyncio.run(main())
