import os  # Remove this line
from pathlib import Path
import pytest

from medical_automation.server.app import create_app
from medical_automation.server.routes import medical_routes, snippet_routes
from medical_automation.utils.db_manager import DatabaseManager
from medical_automation import config as cfg


@pytest.fixture(scope="session")
def medical_sql(tmp_path_factory):
    p = tmp_path_factory.mktemp("sql") / "medical.sql"
    p.write_text(
        """
        CREATE TABLE IF NOT EXISTS frases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria TEXT NOT NULL,
            frase TEXT NOT NULL
        );
        INSERT INTO frases (categoria, frase) VALUES ('Cardiology', 'Normal sinus rhythm');
        INSERT INTO frases (categoria, frase) VALUES ('Cardiology', 'No ischemic changes');
        INSERT INTO frases (categoria, frase) VALUES ('Neurology', 'No focal deficits');
        """
    )
    return p


@pytest.fixture(scope="session")
def snippet_sql(tmp_path_factory):
    p = tmp_path_factory.mktemp("sql") / "snippets.sql"
    p.write_text(
        """
        CREATE TABLE IF NOT EXISTS snippets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            abbreviation TEXT UNIQUE NOT NULL,
            full_text TEXT NOT NULL
        );
        INSERT INTO snippets (abbreviation, full_text) VALUES ('addr', '123 Main Street');
        """
    )
    return p


@pytest.fixture
def app_client(tmp_path, medical_sql, snippet_sql, monkeypatch):
    # Prepare temp DB files
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    medical_db = data_dir / "medical.db"
    snippet_db = data_dir / "snippets.db"

    # Enable admin for write APIs during tests
    monkeypatch.setattr(cfg.Config, "SNIPPET_ADMIN_ENABLED", True, raising=False)
    monkeypatch.setattr(cfg.Config, "SNIPPET_ADMIN_TOKEN", "testtoken", raising=False)
    monkeypatch.setattr(cfg.Config, "SNIPPET_ADMIN_HEADER", "X-Admin-Token", raising=False)

    # Build isolated DBs
    med_manager = DatabaseManager(str(medical_db), str(medical_sql))
    snip_manager = DatabaseManager(str(snippet_db), str(snippet_sql))

    # Patch module-level DB singletons used by routes
    medical_routes.db = med_manager
    snippet_routes.db = snip_manager

    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client