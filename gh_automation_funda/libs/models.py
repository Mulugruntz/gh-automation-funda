"""This module contains the models used for the funda pipeline."""

from enum import Enum
from pydantic import BaseModel, Field
from datetime import date, datetime
from decimal import Decimal


class Availability(str, Enum):
    """The availability of the property."""

    AVAILABLE = "available"
    NEGOTIATED = "negotiated"
    SOLD = "sold"


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
    area_of_plot: int = Field(..., gt=0, description="The area of the plot of the property, in m2.")
    area_of_frontyard: int = Field(..., ge=0, description="The area of the frontyard of the property.")
    area_of_backyard: int = Field(..., ge=0, description="The area of the backyard of the property.")
    volume: int = Field(..., gt=0, description="The volume of the property, in m3.")
    number_of_rooms: int = Field(..., gt=0, description="The number of rooms of the property.")
    number_of_floors: int = Field(..., gt=0, description="The number of floors of the property.")
    energy_label: EnergyLabel = Field(..., description="The energy label of the property.")


class PropertyFundaImage(BaseModel):
    """An image of a property."""

    id: int | None = Field(None, description="The ID of the image.")
    name: str = Field(..., max_length=255, description="The name of the image.")
    image_url: str = Field(..., max_length=1023, description="The Funda.nl URL of the image.")


class PropertyCadastralData(BaseModel):
    """The cadastral data for a property."""

    id: int | None = Field(None, description="The ID of the cadastral data.")
    cadastral_url: str = Field(..., max_length=1023, description="The kadasterdata.nl URL of the property.")
    woz_url: str = Field(..., max_length=1023, description="The WOZ URL of the property.")
    value_min: Decimal = Field(..., gt=0, description="The minimum value of the property.")
    value_max: Decimal = Field(..., gt=0, description="The maximum value of the property.")
    value_calculated_on: date = Field(..., description="The date the value was calculated.")


class PropertyCadastralWOZ(BaseModel):
    """The WOZ data for a property."""

    id: int | None = Field(None, description="The ID of the WOZ data.")
    year: int = Field(..., gt=1800, lt=2100, description="The year the WOZ value was calculated.")
    effective_date: date = Field(..., description="The effective date of the WOZ value.")
    reference_date: date = Field(..., description="The reference date of the WOZ value.")
    value: Decimal = Field(..., gt=0, description="The WOZ value of the property.")


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
    cadastral_data: PropertyCadastralData = Field(..., description="The cadastral data of the property.")
    cadastral_woz: list[PropertyCadastralWOZ] = Field(..., description="The WOZ data of the property.")
