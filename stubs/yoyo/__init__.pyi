from yoyo.backends import DatabaseBackend
from yoyo.migrations import default_migration_table

def get_backend(uri: str, migration_table: str = default_migration_table) -> DatabaseBackend: ...
