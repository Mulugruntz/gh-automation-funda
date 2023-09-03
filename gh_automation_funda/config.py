from typing import Literal

from pydantic import Field
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

ENV_PREFIX = "GH_AUTO_"
SSLMode = Literal["require", "verify-ca", "verify-full", "prefer", "allow", "disable"]

load_dotenv()


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
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?sslmode={self.sslmode}"

    @property
    def yoyo_dns(self) -> str:
        """Return the DSN for the database (with the correct driver for Yoyo migration)."""
        return f"postgresql+psycopg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?sslmode={self.sslmode}"


class Config(BaseSettings):
    """Base configuration class."""

    postgres: PostgresConfig = Field(default_factory=PostgresConfig)

    class Config:
        env_prefix = ENV_PREFIX
