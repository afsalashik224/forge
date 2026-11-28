import importlib

migration_001 = importlib.import_module("migrations.001_add_updated_at")
run_migration_001 = migration_001.run_migration

migration_002 = importlib.import_module("migrations.002_add_workspaces_and_repositories")
run_migration_002 = migration_002.run_migration

migration_003 = importlib.import_module("migrations.003_add_content_tags_category")
run_migration_003 = migration_003.run_migration

migration_004 = importlib.import_module("migrations.004_add_concept_relationships")
run_migration_004 = migration_004.run_migration

migration_005 = importlib.import_module("migrations.005_add_compass_recommendations")
run_migration_005 = migration_005.run_migration

__all__ = [
    "run_migration_001",
    "run_migration_002",
    "run_migration_003",
    "run_migration_004",
    "run_migration_005",
]
