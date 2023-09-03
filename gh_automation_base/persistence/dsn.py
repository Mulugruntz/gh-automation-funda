"""DSN model and utilities."""

from urllib.parse import parse_qsl, urlparse, urlencode

from pydantic import BaseModel


class DSN(BaseModel):
    """A DSN."""

    # The scheme
    scheme: str
    # The username
    username: str
    # The password
    password: str
    # The hostname
    hostname: str
    # The port
    port: int
    # The database
    database: str
    # The arguments
    args: dict[str, str]

    @classmethod
    def from_uri(cls, uri: str) -> "DSN":
        """Return a DSN from a URI."""
        parsed = urlparse(uri)
        return cls(
            scheme=parsed.scheme,
            username=parsed.username,
            password=parsed.password,
            hostname=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],
            args=dict(parse_qsl(parsed.query)),
        )

    def __str__(self) -> str:
        args = f"?{urlencode(self.args)}" if self.args else ""
        if self.username is None:
            return f"{self.scheme}://{self.hostname}:{self.port}/{self.database}{args}"

        if self.password is None:
            return f"{self.scheme}://{self.username}@{self.hostname}:{self.port}/{self.database}{args}"

        return f"{self.scheme}://{self.username}:{self.password}@{self.hostname}:{self.port}/{self.database}{args}"
