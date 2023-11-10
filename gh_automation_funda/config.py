"""Configuration for the application."""
import asyncio
import os
from importlib import import_module
from typing import Annotated, Any, Literal, Self, TypeVar, cast

from dotenv import load_dotenv
from pydantic import (
    BaseModel,
    Field,
    PlainSerializer,
    field_serializer,
    model_validator,
)
from pydantic_settings import BaseSettings

from gh_automation_funda.persistence.settings import read_google_sheets

ENV_PREFIX = "GH_AUTO_"
SSLMode = Literal["require", "verify-ca", "verify-full", "prefer", "allow", "disable"]

load_dotenv()

ModelT = TypeVar("ModelT", bound=BaseModel)


class GoogleSheetsConfig(BaseSettings):
    """Configuration for Google Sheets."""

    sheet_id: str
    gid: str
    model: Annotated[
        type[BaseModel],
        PlainSerializer(lambda x: x.__name__, return_type=str, when_used="json"),
    ]

    class Config:
        env_prefix = f"{ENV_PREFIX}GOOGLE_SHEETS_"

    @classmethod
    def create_from_env(cls) -> list[Self]:
        env_prefix = cls.Config.env_prefix
        configs = []
        for i in range(1, 10):  # Assuming a max of 10 configs
            sheet_id = os.environ.get(f"{env_prefix}{i}_SHEET_ID")
            gid = os.environ.get(f"{env_prefix}{i}_GID")
            model = os.environ.get(f"{env_prefix}{i}_MODEL")

            if sheet_id and gid and model:
                model_class = cls.__load_model(model)

                if model_class is None:
                    print(f"Skipping Google Sheet {sheet_id} due to invalid model {model}.")
                    continue

                configs.append(cls(sheet_id=sheet_id, gid=gid, model=model_class))
            else:
                break
        return configs

    @staticmethod
    def __load_model(model: str) -> type[BaseModel] | None:
        """Load a Pydantic model from a string."""
        try:
            model_path, model_name = model.rsplit(".", 1)
            model_module = import_module(model_path)
            model_class = getattr(model_module, model_name)

            if not issubclass(model_class, BaseModel):
                raise AttributeError(f"Model {model} is not a subclass of Pydantic's BaseModel.")

        except (ImportError, AttributeError) as e:
            print(f"Cannot import model {model} due to error: {e}")
            return None

        return cast(type[BaseModel], model_class)


class LazyDynamicSetting(BaseModel):
    """A lazy dynamic setting."""

    sheet: "GoogleSheetsConfig"

    async def load(self) -> list[BaseModel]:
        """Load the dynamic setting."""
        return await read_google_sheets(
            sheet_id=self.sheet.sheet_id,
            gid=self.sheet.gid,
            model_class=self.sheet.model,
        )


class AivenConfig(BaseSettings):
    """Configuration for Aiven."""

    # Aiven project name
    project: str
    # Aiven API token
    service: str

    class Config:
        env_prefix = f"{ENV_PREFIX}PG_AIVEN_"


class PostgresConfig(BaseSettings):
    """Configuration for Postgres."""

    # Postgres user
    user: str
    # Postgres password
    password: str
    # Postgres database
    database: str
    # Postgres port
    port: int
    # SSL mode
    sslmode: SSLMode = Field(default="require")
    # Schema
    db_schema: str = Field(default="gh_auto_schema")
    # Aiven config
    aiven: AivenConfig = Field(default_factory=AivenConfig)

    class Config:
        env_prefix = f"{ENV_PREFIX}PG_"

    @property
    def host(self) -> str:
        """Return the host for the database."""
        return f"{self.aiven.service}-{self.aiven.project}.aivencloud.com"

    @property
    def dsn(self) -> str:
        """Return the DSN for the database."""
        return (
            f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?sslmode={self.sslmode}"
        )

    @property
    def yoyo_dns(self) -> str:
        """Return the DSN for the database (with the correct driver for Yoyo migration)."""
        return f"postgresql+psycopg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?sslmode={self.sslmode}"


class Config(BaseSettings):
    """Base configuration class."""

    postgres: PostgresConfig = Field(default_factory=PostgresConfig)
    google_sheets: list[GoogleSheetsConfig] = Field(default_factory=list)
    dynamic_settings: dict[type[BaseModel], LazyDynamicSetting] = Field(default_factory=dict, init_var=False)
    loaded_dynamic_settings: dict[type[BaseModel], list[BaseModel]] = Field(default_factory=dict, init_var=False)

    @field_serializer("loaded_dynamic_settings")
    def serialize_loaded_dynamic_settings(
        self, v: dict[type[BaseModel], list[BaseModel]]
    ) -> dict[str, list[dict[str, Any]]]:
        """Serialize the loaded dynamic settings."""
        return {model.__name__: [model.model_dump(row) for row in rows] for model, rows in v.items()}

    @model_validator(mode="before")
    @classmethod
    def assemble_google_sheets(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data["google_sheets"] = GoogleSheetsConfig.create_from_env()
            data["dynamic_settings"] = {sheet.model: LazyDynamicSetting(sheet=sheet) for sheet in data["google_sheets"]}

        return data

    async def get_settings_for(self, model: type[ModelT]) -> list[ModelT]:
        """Return the settings of a model."""
        if model not in self.loaded_dynamic_settings:
            self.loaded_dynamic_settings[model] = await self.dynamic_settings[model].load()
        return cast(list[ModelT], self.loaded_dynamic_settings[model])

    async def preload_all_dynamic_settings(self) -> None:
        """Load all dynamic settings."""
        for model, setting in self.dynamic_settings.items():
            self.loaded_dynamic_settings[model] = await setting.load()

    class Config:
        env_prefix = ENV_PREFIX


if __name__ == "__main__":
    # load_dotenv("../.env.example")
    config = Config()
    asyncio.run(config.preload_all_dynamic_settings())
    print(config.model_dump_json(indent=2))
