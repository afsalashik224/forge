import importlib

migration_001 = importlib.import_module("migrations.001_add_updated_at")
run_migration_001 = migration_001.run_migration

__all__ = ["run_migration_001"]
