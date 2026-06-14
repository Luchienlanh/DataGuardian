from sqlalchemy import create_engine
from sqlalchemy import inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./dataguard.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def ensure_database_schema():
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    if "datasets" not in table_names:
        return

    def add_missing_columns(table_name: str, columns_to_add: dict[str, str]) -> None:
        existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
        for column_name, ddl in columns_to_add.items():
            if column_name not in existing_columns:
                connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl}"))

    with engine.begin() as connection:
        add_missing_columns("datasets", {
            "source": "VARCHAR DEFAULT 'uploaded'",
            "version": "INTEGER DEFAULT 1",
            "parent_dataset_id": "INTEGER",
            "root_dataset_id": "INTEGER",
            "cleaning_run_id": "INTEGER",
            "workspace_id": "INTEGER",
        })

        if "quality_rules" in table_names:
            add_missing_columns("quality_rules", {
                "created_by": "VARCHAR DEFAULT 'manual'",
                "workspace_id": "INTEGER",
            })

        connection.execute(text("UPDATE datasets SET source = 'uploaded' WHERE source IS NULL"))
        connection.execute(text("UPDATE datasets SET version = 1 WHERE version IS NULL"))
        connection.execute(text("UPDATE datasets SET root_dataset_id = id WHERE root_dataset_id IS NULL"))
        connection.execute(text(
            "INSERT INTO workspaces (name, slug) "
            "SELECT 'Default Workspace', 'default' "
            "WHERE NOT EXISTS (SELECT 1 FROM workspaces WHERE slug = 'default')"
        ))
        connection.execute(text(
            "INSERT INTO app_users (workspace_id, email, display_name, role) "
            "SELECT id, 'local@dataguard.dev', 'Local Analyst', 'owner' "
            "FROM workspaces WHERE slug = 'default' "
            "AND NOT EXISTS (SELECT 1 FROM app_users WHERE email = 'local@dataguard.dev')"
        ))
        connection.execute(text(
            "UPDATE datasets SET workspace_id = (SELECT id FROM workspaces WHERE slug = 'default') "
            "WHERE workspace_id IS NULL"
        ))
        if "quality_rules" in table_names:
            connection.execute(text(
                "UPDATE quality_rules SET workspace_id = (SELECT id FROM workspaces WHERE slug = 'default') "
                "WHERE workspace_id IS NULL"
            ))
            connection.execute(text("UPDATE quality_rules SET created_by = 'manual' WHERE created_by IS NULL"))
