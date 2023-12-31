from contextlib import contextmanager
from typing import Any, Iterator, Literal, Mapping, Self, TypeAlias

Driver: TypeAlias = Any
Connection: TypeAlias = Any
Cursor: TypeAlias = Any
TransactionManager: TypeAlias = Any
SavepointTransactionManager: TypeAlias = Any

class Migration:
    id: str
    hash: str | None

    def process_steps(
        self,
        backend: "DatabaseBackend",
        direction: Literal["rollback", "apply"],
        force: bool = False,
    ) -> None: ...

class DatabaseBackend:
    driver_module: str

    log_table: str
    lock_table: str
    list_tables_sql: str
    version_table: str
    migration_table: str
    is_applied_sql: str
    mark_migration_sql: str
    unmark_migration_sql: str
    applied_migrations_sql: str
    create_test_table_sql: str
    log_migration_sql: str
    create_lock_table_sql: str

    _driver: Driver | None = None
    _is_locked: bool = False
    _in_transaction: bool = False
    _internal_schema_updated: bool = False
    _transactional_ddl_cache: dict[bytes, bool]

    def __init__(self, dburi: str, migration_table: str) -> None:
        self.uri: str
        self.DatabaseError: type[Exception]
        self._connection: Connection
        self.migration_table: str
        self.has_transactional_ddl: bool
    def init_database(self) -> None: ...
    def _load_driver_module(self) -> Any: ...
    @property
    def driver(self) -> Driver: ...
    @property
    def connection(self) -> Connection: ...
    def init_connection(self, connection: Connection) -> None: ...
    def copy(self) -> Self: ...
    def __enter__(self) -> Self: ...
    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None: ...
    def __getattr__(self, attrname: str) -> Any: ...
    def connect(self, dburi: str) -> Connection: ...
    def quote_identifier(self, s: str) -> str: ...
    def _check_transactional_ddl(self) -> bool: ...
    def list_tables(self, **kwargs: str) -> list[str]: ...
    def transaction(self, rollback_on_exit: bool = False) -> TransactionManager | SavepointTransactionManager: ...
    def cursor(self) -> Cursor: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def begin(self) -> None: ...
    def savepoint(self, id: str) -> None: ...
    def savepoint_release(self, id: str) -> None: ...
    def savepoint_rollback(self, id: str) -> None: ...
    @contextmanager
    def disable_transactions(self) -> Iterator[None]: ...
    @contextmanager
    def lock(self, timeout: int = 10) -> Iterator[None]: ...
    def _insert_lock_row(self, pid: str, timeout: int, poll_interval: float = 0.5) -> None: ...
    def _delete_lock_row(self, pid: str) -> None: ...
    def break_lock(self) -> None: ...
    def execute(self, sql: str, params: Mapping[str, Any] | None = None) -> Cursor: ...
    def create_lock_table(self) -> None: ...
    def ensure_internal_schema_updated(self) -> None: ...
    def is_applied(self, migration: Migration) -> bool: ...
    def get_applied_migration_hashes(self) -> list[str]: ...
    def to_apply(self, migrations: list[Migration]) -> list[Migration]: ...
    def to_rollback(self, migrations: list[Migration]) -> list[Migration]: ...
    def apply_migrations(self, migrations: list[Migration], force: bool = False) -> None: ...
    def apply_migrations_only(self, migrations: list[Migration], force: bool = False) -> None: ...
    def run_post_apply(self, migrations: list[Migration], force: bool = False) -> None: ...
    def rollback_migrations(self, migrations: list[Migration], force: bool = False) -> None: ...
    def mark_migrations(self, migrations: list[Migration]) -> None: ...
    def unmark_migrations(self, migrations: list[Migration]) -> None: ...
    def apply_one(self, migration: Migration, force: bool = False, mark: bool = True) -> None: ...
    def rollback_one(self, migration: Migration, force: bool = False) -> None: ...
    def unmark_one(self, migration: Migration, log: bool = True) -> None: ...
    def mark_one(self, migration: Migration, log: bool = True) -> None: ...
    def log_migration(
        self,
        migration: Migration,
        operation: Literal["rollback", "apply"],
        comment: str | None = None,
    ) -> None: ...
    def get_log_data(
        self,
        migration: Migration | None = None,
        operation: Literal["rollback", "apply"] = "apply",
        comment: str | None = None,
    ) -> dict[str, Any]: ...

class MySQLBackend(DatabaseBackend): ...
class SQLiteBackend(DatabaseBackend): ...
class PostgresqlBackend(DatabaseBackend): ...
class PostgresqlPsycopgBackend(PostgresqlBackend): ...
