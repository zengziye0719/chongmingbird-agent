from pathlib import Path

from src import database


def test_default_sqlite_path_resolves_to_project_root_from_other_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./data/chongmingbird.db")

    expected = database.PROJECT_ROOT / "data" / "chongmingbird.db"
    assert Path(database._path()) == expected

    database.init_db()
    assert expected.exists()
    assert not (tmp_path / "data" / "chongmingbird.db").exists()


def test_absolute_sqlite_path_is_respected(tmp_path, monkeypatch):
    absolute_db = tmp_path / "nested" / "custom.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{absolute_db}")

    assert Path(database._path()) == absolute_db
    database.init_db()
    assert absolute_db.exists()
