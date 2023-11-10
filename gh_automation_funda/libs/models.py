"""This module contains the models used for the funda pipeline."""

import warnings
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Final, Mapping, Sequence, TypeAlias

from pydantic import BaseModel, Field

JSON: TypeAlias = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None
JSON_ro: TypeAlias = Mapping[str, "JSON_ro"] | Sequence["JSON_ro"] | str | int | float | bool | None


VALID_AREA_EXTRAS: Final[dict[str, str]] = {
    "Overige inpandige ruimte": "other_indoor_space",
    "Gebouwgebonden buitenruimte": "building_related_outdoor_space",
    "Externe bergruimte": "external_storage_space",
}
PROPERTY_TYPES: Final[dict[str, str]] = {
    "woonhuis": "residential house",
    "appartement": "apartment",
    "parkeergelegenheid": "parking",
    "nieuwbouwproject": "new development",
    "recreatiewoning": "recreation",
    "woonboot": "houseboat",
    "garage": "garage",
    "bouwgrond": "building land",
    "overig aanbod": "other",
}


def translate_property_type_nl_to_en(property_type_nl: str) -> str:
    """Translate the Dutch property type to the English property type."""
    if property_type_nl.lower() not in PROPERTY_TYPES:
        warnings.warn(f"Unknown property type: {property_type_nl}", UserWarning)
        return property_type_nl

    return PROPERTY_TYPES[property_type_nl.lower()]


def format_area_extra(name_nl: str, value: str) -> tuple[str, int] | None:
    """Format the area extra name and value, and filter out unwanted ones."""
    if name_nl in ("Wonen", "Perceel", "Inhoud"):
        return None

    name = VALID_AREA_EXTRAS.get(name_nl)

    if name is None:
        if value.strip().endswith("m²"):
            warnings.warn(f"Unknown area extra name: {name_nl}", UserWarning)
        elif value.strip().endswith("m³"):
            warnings.warn(f"Unknown volume extra name: {name_nl}", UserWarning)
        return None

    return name, int(value.strip().removesuffix("m²").removesuffix("m³").strip())


def get_clean_area_extras(area_extras: Mapping[str, str]) -> dict[str, int]:
    """Get the clean area extras."""
    return {extra[0]: extra[1] for k, v in area_extras.items() if (extra := format_area_extra(k, v)) is not None}


class Availability(str, Enum):
    """The availability of the property."""

    AVAILABLE = "available"
    NEGOTIATED = "negotiated"
    SOLD = "sold"

    @classmethod
    def from_nl(cls, availability: str) -> "Availability":
        """Convert the Dutch availability to the English availability."""
        return {
            "beschikbaar": cls.AVAILABLE,
            "inonderhandeling": cls.NEGOTIATED,
            "verkocht": cls.SOLD,
        }[availability.lower()]


class EnergyLabel(str, Enum):
    """The energy label of the property."""

    A_5_PLUS = "A+++++"
    A_4_PLUS = "A++++"
    A_3_PLUS = "A+++"
    A_2_PLUS = "A++"
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    UNKNOWN = "UNKNOWN"


class PropertyFundaData(BaseModel):
    """The data from Funda.nl for a property."""

    id: int | None = Field(None, description="The ID of the property.")
    url: str = Field(..., max_length=1023, description="The Funda.nl URL of the property.")
    asking_price: Decimal = Field(..., gt=0, description="The asking price of the property.")
    price_per_m2: Decimal = Field(..., gt=0, description="The price per square meter of the property.")
    availability_status: Availability = Field(..., description="The availability status of the property.")
    offered_since: date = Field(..., description="The date the property was offered for sale.")
    year_built: int = Field(..., gt=1800, lt=2100, description="The year the property was built.")
    area_to_live: int = Field(..., gt=0, description="The living area of the property, in m2.")
    area_of_plot: int = Field(..., ge=0, description="The area of the plot of the property, in m2.")
    area_extras: dict[str, int] = Field(..., description="The extra areas of the property.")
    volume: int = Field(..., gt=0, description="The volume of the property, in m3.")
    number_of_rooms: int = Field(..., gt=0, description="The number of rooms of the property.")
    number_of_floors: int = Field(..., gt=0, description="The number of floors of the property.")
    energy_label: EnergyLabel = Field(..., description="The energy label of the property.")
    property_type: str = Field(..., max_length=255, description="The type of the property.")
    has_roof_terrace: bool = Field(False, description="Whether the property has a roof terrace.")
    has_garden: bool = Field(False, description="Whether the property has a garden.")
    has_balcony: bool = Field(False, description="Whether the property has a balcony.")
    has_solar_panels: bool = Field(False, description="Whether the property has solar panels.")
    has_parking_on_site: bool = Field(False, description="Whether the property has parking on site.")
    has_parking_on_closed_site: bool = Field(False, description="Whether the property has parking on a closed site.")
    is_energy_efficient: bool = Field(False, description="Whether the property is energy efficient.")


class PropertyFundaImage(BaseModel):
    """An image of a property."""

    id: int | None = Field(None, description="The ID of the image.")
    name: str = Field(..., max_length=255, description="The name of the image.")
    image_url: str = Field(..., max_length=1023, description="The Funda.nl URL of the image.")


class PropertyCadastralData(BaseModel):
    """The cadastral data for a property."""

    id: int | None = Field(None, description="The ID of the cadastral data.")
    cadastral_url: str = Field(..., max_length=1023, description="The kadasterdata.nl URL of the property.")
    value_min: Decimal | None = Field(..., gt=0, description="The minimum value of the property.")
    value_max: Decimal | None = Field(..., gt=0, description="The maximum value of the property.")
    value_calculated_on: date | None = Field(..., description="The date the value was calculated.")


class PropertyCadastralWOZItem(BaseModel):
    """The WOZ data for a property for a specific year."""

    id: int | None = Field(None, description="The ID of the WOZ data.")
    year: int = Field(..., gt=1800, lt=2100, description="The year the WOZ value was calculated.")
    reference_date: date = Field(..., description="The reference date of the WOZ value.")
    value: Decimal = Field(..., gt=0, description="The WOZ value of the property.")


class PropertyCadastralWOZ(BaseModel):
    """The WOZ data for a property."""

    id: int | None = Field(None, description="The ID of the WOZ data.")
    woz_url: str = Field(..., max_length=1023, description="The WOZ URL of the property.")
    woz_data: list[PropertyCadastralWOZItem] = Field(..., description="The WOZ data of the property.")


class Property(BaseModel):
    """A property."""

    id: int | None = Field(None, description="The ID of the property.")
    name: str = Field(..., max_length=255, description="The name of the property.")
    address: str = Field(..., max_length=255, description="The address of the property.")
    city: str = Field(..., max_length=255, description="The city of the property.")
    postal_code: str = Field(..., max_length=255, description="The postal code of the property.")
    latitude: Decimal = Field(..., description="The latitude of the property.")
    longitude: Decimal = Field(..., description="The longitude of the property.")
    created_at: datetime = Field(default_factory=datetime.now, description="The creation date of the property.")
    updated_at: datetime = Field(default_factory=datetime.now, description="The last update date of the property.")
    funda_data: PropertyFundaData = Field(..., description="The Funda.nl data of the property.")
    funda_images: list[PropertyFundaImage] = Field(..., description="The Funda.nl images of the property.")
    cadastral_data: PropertyCadastralData | None = Field(
        ...,
        description=(
            "The cadastral data of the property. Can be NULL if there is no cadastral data (e.g. for new buildings)."
        ),
    )
    cadastral_woz: PropertyCadastralWOZ = Field(..., description="The WOZ data of the property.")
