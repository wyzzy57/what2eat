# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Tooling and common commands

### Python and dependency management
- Python version: `>=3.12` (from `pyproject.toml` and `uv.lock`).
- Dependency management: this repo uses `uv` (presence of `uv.lock`). Prefer `uv` over `pip`.

Common commands (run from the repo root):
- Install / sync all dependencies: `uv sync`
- Run the main script: `uv run python main.py`
- Start a Python REPL in the project environment: `uv run python`
- Add a new dependency: `uv add <package>` (updates `pyproject.toml` and `uv.lock`).

If you need to build distribution artifacts, prefer `uv build` so that `uv` uses the existing `pyproject.toml` configuration.

### Tests and linting
- There is currently **no test framework, linter, or formatter configured** in `pyproject.toml` and no test files in the repo.
- Before assuming commands like `pytest`, `ruff`, or `mypy` exist, check that the corresponding tools have been added to `pyproject.toml` and `uv.lock`.
- Once a test framework is added, prefer to run it via `uv run <test-command>` so that it uses the locked environment (for example, `uv run pytest` once `pytest` is configured).

## Configuration and environment

Configuration is centralized in `src/core/config.py` via a single `Settings` class based on `pydantic-settings`:
- The global settings instance is `settings = Settings()` at the bottom of `config.py`. All other modules should import and reuse this instead of recreating settings.
- Settings are primarily driven by environment variables (with `.env` support enabled via `model_config.env_file = ".env"`).

Key aspects:
- `db_type`: selects between PostgreSQL (`"postgres"`) and SQLite (`"sqlite"`). Default is SQLite.
- PostgreSQL settings: `db_host`, `db_port`, `db_user`, `db_password`, `db_name`, plus connection pool options.
- SQLite settings: `sqlite_db_path` (default `./data/what2eat.sqlite3`).
- Redis settings: `redis_host`, `redis_port`, `auth_redis_db`, `cache_redis_db` and the computed URLs `auth_redis_url` / `cache_redis_url`.
- JWT: `jwt_secret` (must be supplied via environment variables for anything auth-related to work).

Environment variable behavior:
- Field names map directly to env vars (case-insensitive and loaded from `.env` by default), e.g. `DB_PASSWORD`, `JWT_SECRET`, `DB_TYPE`, `SQLITE_DB_PATH`, etc.
- The `database_url` and `engine_options` computed fields are derived from the above and are what the database layer consumes.

When adjusting environment or connection behavior, prefer to change `Settings` fields (and derived computed fields) rather than hard-coding URLs/options elsewhere.

## High-level architecture

This repo is currently a skeleton for an async FastAPI/SQLModel application with a small but important "core" layer.

### Entry point
- `main.py` defines a simple `main()` function and prints `"Hello from what2eat!"`. It is the current executable entry point and can be run with `uv run python main.py`.
- There is no FastAPI app object yet; future HTTP API components will likely live under `src/` and be wired into an ASGI server (e.g. `uvicorn`).

### Core layer (`src/core`)

The `core` package contains shared infrastructure: configuration, database wiring, and ORM base classes.

#### `config.py` – application configuration
- Defines the `Settings` class (subclass of `BaseSettings`) that owns all application configuration: app metadata, database, Redis, and JWT.
- Provides several `@computed_field` properties:
  - `database_url`: returns a SQLAlchemy-style async URL based on `db_type` (PostgreSQL via `asyncpg`, or SQLite via `aiosqlite`).
  - `engine_options`: returns a dict of keyword arguments for `create_async_engine`, including pool settings when using PostgreSQL and `echo` flags.
  - `auth_redis_url` and `cache_redis_url`: build Redis URLs from the base Redis config and database indices.
- Exposes a module-level singleton `settings` used throughout the project.

Design implications:
- Database and Redis clients should consume `settings.database_url`, `settings.engine_options`, and the Redis URL properties instead of reconstructing connection strings.
- Because `DateTimeMixin` and the database engine depend on `settings.db_type`, ensure `db_type` and related environment variables are set before importing modules that reference `settings` at import time.

#### `database.py` – async engine and session management
- Creates a global async SQLAlchemy engine: `engine = create_async_engine(settings.database_url, **settings.engine_options)`.
- Configures an async session factory `SessionFactory = async_sessionmaker(...)` bound to that engine with:
  - `autoflush=False`
  - `expire_on_commit=False`
- Exposes two key utilities:
  - `get_db()` – an async generator yielding `AsyncSession` instances; intended to be used as a FastAPI dependency for request-scoped database sessions.
  - `create_db_and_tables()` – an async helper that calls `SQLModel.metadata.create_all` against the engine, meant for development and testing only (comments explicitly recommend Alembic for production migrations).

When adding new models or services:
- Import `get_db` in FastAPI route modules to acquire a database session per request.
- Ensure all SQLModel model classes are imported somewhere before running `create_db_and_tables()`, otherwise `SQLModel.metadata` will be incomplete and tables will not be created.

#### `base_model.py` – ORM base class and timestamp mixin
- Imports `SQLModel` and `Field` and applies a global SQLAlchemy naming convention to `SQLModel.metadata.naming_convention` (for consistent index/constraint names across databases).
- Defines `Base(SQLModel)` as a common ORM base class for future models to inherit from.
- Defines `DateTimeMixin` to add `created_at` and `updated_at` columns to models, with behavior depending on `settings.db_type`:
  - When `db_type == "postgres"`:
    - Uses `sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), ...)` so timestamps are managed in the database via `func.now()`.
  - When `db_type != "postgres"` (e.g. SQLite):
    - Uses `default_factory` functions that return `datetime.now(timezone.utc)` and corresponding `sa_column` definitions; this relies more on application-side timestamp generation.

Key points when defining models:
- New models should typically inherit from both `Base` and `DateTimeMixin` where appropriate, for example: `class Dish(Base, DateTimeMixin, table=True): ...`.
- Because `DateTimeMixin` is defined conditionally at import time based on `settings.db_type`, changing `db_type` after import will not reconfigure the fields. Set `DB_TYPE` via env before importing `base_model`.

### Package layout and imports

Current layout:
- Root: project metadata and entry script (`pyproject.toml`, `uv.lock`, `main.py`, `LICENSE`, `.python-version`).
- Source: `src/core/` for shared infrastructure code.

Notes for imports:
- `config.py`, `database.py`, and `base_model.py` currently import `settings` via `from config import settings`. If you add new modules under `src/`, prefer a consistent import strategy (for example, `from core.config import settings`) and adjust the Python path or package structure accordingly so that imports remain unambiguous.
- Keep new foundational utilities that are reused across features inside `src/core` (or subpackages of it) so that configuration and infrastructure remain centralized.

## Working with the database in development

Typical development flow when you start adding models:
1. Define SQLModel models that inherit from `Base` (and `DateTimeMixin` if you need timestamps).
2. Ensure the modules that define these models are imported before invoking `create_db_and_tables()`.
3. Run an async initialization step (for example via a small script or a FastAPI startup event) that awaits `create_db_and_tables()` to create tables in the configured database.
4. In FastAPI endpoints or background tasks, depend on `get_db()` to obtain an `AsyncSession` and interact with the database.

Remember: `create_db_and_tables()` is intended for local development and testing; in production you should introduce a real migration workflow (e.g. Alembic) wired to the same `settings.database_url` and naming convention.
