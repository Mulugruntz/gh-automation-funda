"""Scrapers for Funda.nl."""

import ast
import asyncio
import json
import re
import warnings
from datetime import date, datetime
from decimal import Decimal
from html import unescape
from typing import Any, Final, TypedDict, cast

from bs4 import BeautifulSoup, Tag
from httpx import AsyncClient

from gh_automation_funda.libs.models import (
    Availability,
    EnergyLabel,
    get_clean_area_extras,
    translate_property_type_nl_to_en,
)

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
ALT_PHOTO_REGEX: Final[re.Pattern[str]] = re.compile(r"Foto (\d+) van (\d+)")


class PropertyFromFundaData(TypedDict):
    url: str
    asking_price: Decimal
    price_per_m2: Decimal
    availability_status: Availability
    offered_since: date
    year_built: int
    area_to_live: int
    area_of_plot: int
    area_extras: dict[str, int]
    volume: int
    number_of_rooms: int
    number_of_floors: int
    energy_label: EnergyLabel
    property_type: str
    has_roof_terrace: bool
    has_garden: bool
    has_balcony: bool
    has_solar_panels: bool
    has_parking_on_site: bool
    has_parking_on_closed_site: bool
    is_energy_efficient: bool
    name: str
    address: str
    city: str
    postal_code: str
    latitude: Decimal
    longitude: Decimal
    funda_images: dict[str, str]


def _extract_in_between(text: str, start_tag: str, end_tag: str) -> str:
    """Extract the text between two tags."""
    idx_start = text.find(start_tag)
    idx_end = text[idx_start:].find(end_tag) + idx_start
    return text[idx_start + len(start_tag) : idx_end]


async def get_new_properties_url(
    *, area: list[str], price_min: int, price_max: int, days_old: int = 3, object_type: list[str]
) -> list[str]:
    """Get the new properties from Funda.nl.

    Example:
        https://www.funda.nl/zoeken/koop?selected_area=%5B%22almere%22%5D&price=%22300000-500000%22&publication_date=%223%22
    """
    areas = ",".join(f'"{a.lower()}"' for a in area)
    object_types = ",".join(f'"{o.lower()}"' for o in object_type)
    params = {
        "selected_area": f"[{areas}]",
        "price": f'"{price_min}-{price_max}"',
        "publication_date": f'"{days_old}"',
        "object_type": f"[{object_types}]",
    }

    async with AsyncClient() as client:
        response = await client.get(FUNDA_SEARCH_URL, params=params, headers=FUNDA_HEADERS)

    try:
        response.raise_for_status()
    except Exception as e:
        e.add_note(f"Error while reading Funda.nl: {e}")
        raise e

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


async def get_property_data(url: str) -> PropertyFromFundaData | None:
    """Get the data for a property from Funda.nl."""
    async with AsyncClient(follow_redirects=True) as client:
        response = await client.get(url, headers=FUNDA_HEADERS)

    try:
        response.raise_for_status()
    except Exception as e:
        e.add_note(f"Error while reading Funda.nl: {e}")
        raise e

    soup = BeautifulSoup(response.text, "html.parser")

    try:
        data = _extract_hidden_script_data(soup)
        data2 = _extract_advert_data(soup)
        data_geo = _extract_geo_data(soup)
        data_areas_vol = _extract_areas_and_volume(soup)
        image_urls = _extract_image_urls(soup)
        number_of_floors = _extract_number_of_floors(soup)
        energy_label = _extract_energy_label(soup)
    except Exception as e:
        e.add_note(f"Error while reading {url}")
        raise

    if energy_label is not data2["energy_label"]:
        # Known mismatch: A+ to A5+ are all seen as A in the advert data.
        if data2["energy_label"] is EnergyLabel.A and "+" in energy_label.value:
            pass
        else:
            warnings.warn(f"Energy label mismatch: {energy_label} vs {data2['energy_label']}", UserWarning)

    return {
        "url": str(response.url),
        "asking_price": data["asking_price"],
        "price_per_m2": data["asking_price"] / data2["area_to_live"],
        "availability_status": data2["availability_status"],
        "offered_since": data["offered_since"],
        "year_built": data2["year_built"],
        "area_to_live": data2["area_to_live"],
        "area_of_plot": data_areas_vol["area_of_plot"],
        "area_extras": data_areas_vol["area_extras"],
        "volume": data_areas_vol["volume"],
        "number_of_rooms": data2["number_of_rooms"],
        "number_of_floors": number_of_floors,
        "energy_label": energy_label,
        "property_type": data2["property_type"],
        "has_roof_terrace": data2["has_roof_terrace"],
        "has_garden": data2["has_garden"],
        "has_balcony": data2["has_balcony"],
        "has_solar_panels": data2["has_solar_panels"],
        "has_parking_on_site": data2["has_parking_on_site"],
        "has_parking_on_closed_site": data2["has_parking_on_closed_site"],
        "is_energy_efficient": data2["is_energy_efficient"],
        "name": data_geo["name"],
        "address": f"{data_geo['name']}, {data['postal_code']} {data['city']}",
        "city": data["city"],
        "postal_code": data["postal_code"],
        "latitude": data_geo["latitude"],
        "longitude": data_geo["longitude"],
        "funda_images": image_urls,
    }


def _extract_advert_data(soup: BeautifulSoup) -> dict[str, Any]:
    script_ad_targeting = soup.find(
        "script", attrs={"type": "application/ld+json", "data-advertisement-targeting": True}
    )
    assert script_ad_targeting is not None
    data = json.loads(script_ad_targeting.text)
    return {
        "availability_status": Availability.from_nl(data["status"]),
        "year_built": int(data["bouwjaar"]),
        "area_to_live": int(data["woonoppervlakte"]),
        "number_of_rooms": int(data["aantalkamers"]),
        "energy_label": EnergyLabel(data.get("energieklasse", EnergyLabel.UNKNOWN).upper()),
        "property_type": translate_property_type_nl_to_en(data["soortobject"]),
        "has_roof_terrace": data.get("dakterras", "false") == "true",
        "has_garden": data.get("tuin", "false") == "true",
        "has_balcony": data.get("balkon", "false") == "true",
        "has_solar_panels": data.get("zonnepanelen", "false") == "true",
        "has_parking_on_site": data.get("parkeergelegenheidopeigenterrein", "false") == "true",
        "has_parking_on_closed_site": data.get("parkeergelegenheidopafgeslotenterrein", "false") == "true",
        "is_energy_efficient": data.get("energiezuinig", "false") == "true",
    }


def _extract_hidden_script_data(soup: BeautifulSoup) -> dict[str, Any]:
    script_gtm = soup.find("script", attrs={"data-test-gtm-script": True})
    payload = _extract_in_between(script_gtm.text, "gtmDataLayer.push(", ");")  # type: ignore
    data = ast.literal_eval(payload)
    offered_since = (
        date.today()
        if data["aangebodensinds"] == "Vandaag"
        else datetime.strptime(data["aangebodensinds"], "%d %B %Y").date()
    )
    return {
        "asking_price": Decimal(data["koopprijs"]),
        "offered_since": offered_since,
        "city": unescape(data["plaats"]).capitalize(),
        "postal_code": data["postcode"],
    }


def _extract_number_of_floors(soup: BeautifulSoup) -> int:
    floors_str = (
        soup.find("dt", string="Aantal woonlagen")  # type: ignore
        .next_sibling.next_sibling.text.strip()
        .removesuffix(" woonlagen")
        .removesuffix(" woonlaag")
    )

    try:
        return int(floors_str)
    except ValueError:
        pass

    if floors_str.endswith(("en een zolder", "en een vliering")):
        return int(floors_str.split()[0]) + 1

    warnings.warn(f"Number of floors is unknown format: {floors_str}", UserWarning)

    return int(floors_str.split()[0])


def _extract_image_urls(soup: BeautifulSoup) -> dict[str, str]:
    images = soup.find_all("img", attrs={"data-media-viewer-overview-image": True}, alt=ALT_PHOTO_REGEX)
    image_urls = {
        f"Photo {int(m.groups()[0])} / {int(m.groups()[1])}": img.attrs["data-lazy"]
        for img in images
        if (m := ALT_PHOTO_REGEX.match(img.attrs["alt"]))
    }
    return image_urls


def _extract_geo_data(soup: BeautifulSoup) -> dict[str, Any]:
    script_object_map_config = soup.find("script", attrs={"type": "application/json", "data-object-map-config": True})
    data = json.loads(script_object_map_config.text)  # type: ignore
    return {
        "name": unescape(data["markerTitle"]),
        "latitude": data["lat"],
        "longitude": data["lng"],
    }


def _extract_areas_and_volume(soup: BeautifulSoup) -> dict[str, Any]:
    data = {}
    usable_surfaces_child = soup.find(
        "dt", attrs={"class": "object-kenmerken-group-header object-kenmerken-group-header-half"}
    )
    for dt in usable_surfaces_child.parent.find_all("dt"):  # type: ignore
        data[dt.text.strip()] = dt.next_sibling.next_sibling.text.strip()
    return {
        "area_of_plot": int(data.get("Perceel", "0").removesuffix(" m²")),
        "area_extras": get_clean_area_extras(data),
        "volume": int(data["Inhoud"].removesuffix(" m³")),
    }


def _extract_energy_label(soup: BeautifulSoup) -> EnergyLabel:
    """Extract the energy label from the page.

    The tag looks like this:

    .. code-block:: html

        <span class="energielabel energielabel-c" title="Energielabel C">C</span>


    Or sometimes like this:

    .. code-block:: html

        <span class="energielabel energielabel-c" title="Energielabel C">C
            <span class="energielabel-index" title="Energie-Indexcijfer 1,84">1,84</span>
        </span>
    """
    energy_label_tag = cast(Tag, soup.find("span", class_="energielabel"))
    if not energy_label_tag:
        return EnergyLabel.UNKNOWN

    # Get the title, check if it starts with "Energielabel" and strip it.
    energy_label_title = energy_label_tag.attrs["title"]
    if energy_label_title.startswith("Energielabel "):
        energy_label_from_title = EnergyLabel(energy_label_title.removeprefix("Energielabel ").strip())
        text = energy_label_tag.contents[0].get_text(strip=True)
        if energy_label_from_title.upper() != text.upper():
            warnings.warn(f"Energy label mismatch: title={energy_label_from_title} vs body={text}", UserWarning)
    else:
        text = energy_label_tag.get_text(strip=True)

    try:
        return EnergyLabel(text)
    except ValueError:
        warnings.warn(f"Unknown energy label: {text}", UserWarning)

    return EnergyLabel.UNKNOWN


async def main() -> None:
    """Main entry point (for testing)."""
    urls = await get_new_properties_url(area=["almere"], price_min=300_000, price_max=500_000, object_type=["house"])
    print(urls)
    for url in urls:
        try:
            property_1 = await get_property_data(url)
            print(property_1)
        except Exception as e:
            print(f"Error while reading {url}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
