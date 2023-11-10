"""Logic for Funda API."""
from typing import Any

from gh_automation_funda.config import Config
from gh_automation_funda.libs.models import (
    Property,
    PropertyCadastralData,
    PropertyCadastralWOZ,
    PropertyCadastralWOZItem,
    PropertyFundaData,
    PropertyFundaImage,
)
from gh_automation_funda.libs.scrapers.funda import (
    PropertyFromFundaData,
    get_new_properties_url,
    get_property_data,
)
from gh_automation_funda.libs.scrapers.kadasterdata import (
    get_cadaster_url_from_address,
    get_property_cadaster_data,
)
from gh_automation_funda.libs.scrapers.wozwaardeloket import get_property_woz_data
from gh_automation_funda.persistence.settings import FundaSetting


class Funda:
    def __init__(self, config: Config) -> None:
        self.config = config

    async def get_new_properties(self) -> list[Property]:
        """Get the new properties from Funda.nl."""
        settings = await self.config.get_settings_for(FundaSetting)
        urls = set()
        properties = []
        for funda_setting in settings:
            batch_urls = await get_new_properties_url(
                area=funda_setting.area,
                price_min=funda_setting.price_min,
                price_max=funda_setting.price_max,
                days_old=funda_setting.days_old,
                object_type=funda_setting.object_type,
            )
            urls.update(batch_urls)

        for url in urls:
            property_data = await self.get_property_all_data(url)
            if property_data is None:
                continue

            properties.append(property_data)
            self._save_property_data(property_data)

        return properties

    async def get_property_all_data(self, url: str) -> Property | None:
        """Get the data for a property from Funda.nl."""
        data_funda = await get_property_data(url)
        if not data_funda:
            return None

        cadaster_url = await get_cadaster_url_from_address(
            street_and_house_number=data_funda["name"],
            postal_code=data_funda["postal_code"],
            city=data_funda["city"],
        )
        cadaster_data = await get_property_cadaster_data(cadaster_url) if cadaster_url else None

        woz_data = await get_property_woz_data(
            street_and_house_number=data_funda["name"],
            postal_code=data_funda["postal_code"],
            city=data_funda["city"],
        )

        return self._assemble_property_data(data_funda, cadaster_data, woz_data)

    @staticmethod
    def _assemble_property_data(
        data_funda: PropertyFromFundaData,
        data_cadaster: dict[str, Any] | None,
        data_woz: dict[str, Any],
    ) -> Property:
        """Assemble the data for a property."""
        cadastral_data = None
        if data_cadaster:
            cadastral_data = PropertyCadastralData(
                cadastral_url=data_cadaster["cadastral_url"],
                woz_url=data_woz["woz_url"],
                value_min=data_cadaster["value_min"],
                value_max=data_cadaster["value_max"],
                value_calculated_on=data_cadaster["value_calculated_on"],
            )

        return Property(
            name=data_funda["name"],
            address=data_funda["address"],
            city=data_funda["city"],
            postal_code=data_funda["postal_code"],
            latitude=data_funda["latitude"],
            longitude=data_funda["longitude"],
            funda_data=PropertyFundaData(
                url=data_funda["url"],
                asking_price=data_funda["asking_price"],
                price_per_m2=data_funda["price_per_m2"],
                availability_status=data_funda["availability_status"],
                offered_since=data_funda["offered_since"],
                year_built=data_funda["year_built"],
                area_to_live=data_funda["area_to_live"],
                area_of_plot=data_funda["area_of_plot"],
                area_extras=data_funda["area_extras"],
                volume=data_funda["volume"],
                number_of_rooms=data_funda["number_of_rooms"],
                number_of_floors=data_funda["number_of_floors"],
                energy_label=data_funda["energy_label"],
                property_type=data_funda["property_type"],
                has_roof_terrace=data_funda["has_roof_terrace"],
                has_garden=data_funda["has_garden"],
                has_balcony=data_funda["has_balcony"],
                has_solar_panels=data_funda["has_solar_panels"],
                has_parking_on_site=data_funda["has_parking_on_site"],
                has_parking_on_closed_site=data_funda["has_parking_on_closed_site"],
                is_energy_efficient=data_funda["is_energy_efficient"],
            ),
            funda_images=[
                PropertyFundaImage(name=name, image_url=url) for name, url in data_funda["funda_images"].items()
            ],
            cadastral_data=cadastral_data,
            cadastral_woz=PropertyCadastralWOZ(
                woz_url=data_woz["woz_url"],
                woz_data=[
                    PropertyCadastralWOZItem(
                        year=woz_line["year"],
                        reference_date=woz_line["reference_date"],
                        value=woz_line["value"],
                    )
                    for woz_line in data_woz["woz_data"]
                ],
            ),
        )

    def _save_property_data(self, property_data: Property) -> None:
        """Save the property data."""
        print("Saving property data:")
        # print(property_data.model_dump_json(indent=2))
        print(property_data.address)
        print(property_data.funda_data.url)
        if property_data.cadastral_data is not None:
            print(property_data.cadastral_data.cadastral_url)
        print(property_data.cadastral_woz.woz_url)
        print("Done saving property data.")
        print()
