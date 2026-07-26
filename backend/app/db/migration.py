def to_sync_database_url(database_url: str) -> str:
    return database_url.replace("postgresql+asyncpg", "postgresql+psycopg", 1)
