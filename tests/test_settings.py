from app.config.settings import Settings


def test_default_settings_are_not_setup_complete():
    settings = Settings()
    assert settings.setup_complete is False
    assert settings.has_parent_pin() is False


def test_first_time_user_defaults_to_forest_adventure_theme():
    assert Settings().theme == "forest_adventure"


def test_default_font_family_and_size():
    settings = Settings()
    assert settings.font_family == "default"
    assert settings.font_size == "large"


def test_default_hub_fields_are_unset():
    settings = Settings()
    assert settings.last_learning_route == ""
    assert settings.preferred_learning_mode == ""


def test_save_and_load_settings_round_trips_hub_fields(tmp_path, monkeypatch):
    import app.config.settings as settings_module

    monkeypatch.setattr(settings_module, "get_data_dir", lambda: tmp_path)

    settings = settings_module.Settings(last_learning_route="skills", preferred_learning_mode="advanced")
    settings_module.save_settings(settings)

    loaded = settings_module.load_settings()
    assert loaded.last_learning_route == "skills"
    assert loaded.preferred_learning_mode == "advanced"


def test_load_settings_missing_hub_fields_falls_back_to_unset(tmp_path, monkeypatch):
    import json

    import app.config.settings as settings_module

    monkeypatch.setattr(settings_module, "get_data_dir", lambda: tmp_path)
    (tmp_path / "settings.json").write_text(json.dumps({"child_name": "Sam"}), encoding="utf-8")

    loaded = settings_module.load_settings()
    assert loaded.last_learning_route == ""
    assert loaded.preferred_learning_mode == ""


def test_save_and_load_settings_round_trips_font_choices(tmp_path, monkeypatch):
    import app.config.settings as settings_module

    monkeypatch.setattr(settings_module, "get_data_dir", lambda: tmp_path)

    settings = settings_module.Settings(font_family="classic", font_size="extra_large")
    settings_module.save_settings(settings)

    loaded = settings_module.load_settings()
    assert loaded.font_family == "classic"
    assert loaded.font_size == "extra_large"


def test_load_settings_ignores_unknown_fields_from_a_newer_or_older_version(tmp_path, monkeypatch):
    import json

    import app.config.settings as settings_module

    monkeypatch.setattr(settings_module, "get_data_dir", lambda: tmp_path)
    (tmp_path / "settings.json").write_text(
        json.dumps({"child_name": "Sam", "some_future_field_this_version_does_not_know": "x"}),
        encoding="utf-8",
    )

    loaded = settings_module.load_settings()
    assert loaded.child_name == "Sam"
    assert loaded.font_family == "default"  # missing from the file -- falls back to the dataclass default


def test_parent_pin_round_trip():
    settings = Settings()
    settings.set_parent_pin("1234")

    assert settings.has_parent_pin() is True
    assert settings.verify_parent_pin("1234") is True
    assert settings.verify_parent_pin("9999") is False


def test_parent_pin_salted_differently_each_time():
    a = Settings()
    a.set_parent_pin("1234")
    b = Settings()
    b.set_parent_pin("1234")

    assert a.parent_pin_hash != b.parent_pin_hash


def test_save_and_load_settings_round_trip(tmp_path, monkeypatch):
    import app.config.settings as settings_module

    monkeypatch.setattr(settings_module, "get_data_dir", lambda: tmp_path)

    settings = settings_module.Settings(child_name="Alex", setup_complete=True)
    settings.set_parent_pin("4321")
    settings_module.save_settings(settings)

    loaded = settings_module.load_settings()
    assert loaded.child_name == "Alex"
    assert loaded.setup_complete is True
    assert loaded.verify_parent_pin("4321") is True


def test_load_settings_missing_file_returns_defaults(tmp_path, monkeypatch):
    import app.config.settings as settings_module

    monkeypatch.setattr(settings_module, "get_data_dir", lambda: tmp_path)

    loaded = settings_module.load_settings()
    assert loaded == settings_module.Settings()


def test_load_settings_corrupt_file_returns_defaults(tmp_path, monkeypatch):
    import app.config.settings as settings_module

    monkeypatch.setattr(settings_module, "get_data_dir", lambda: tmp_path)
    (tmp_path / "settings.json").write_text("{not valid json", encoding="utf-8")

    loaded = settings_module.load_settings()
    assert loaded == settings_module.Settings()


def test_get_data_dir_delegates_to_platform_paths(tmp_path, monkeypatch):
    import app.config.settings as settings_module

    monkeypatch.setattr(settings_module, "resolve_platform_data_dir", lambda: tmp_path)
    assert settings_module.get_data_dir() == tmp_path


def test_get_data_dir_migrates_forward_from_repo_local_app_data(tmp_path, monkeypatch):
    import app.config.settings as settings_module

    fake_repo_root = tmp_path / "repo"
    repo_local_dir = fake_repo_root / settings_module.REPO_LOCAL_DATA_DIRNAME
    repo_local_dir.mkdir(parents=True)
    (repo_local_dir / settings_module.SETTINGS_FILENAME).write_text('{"child_name": "Avyaan"}', encoding="utf-8")

    platform_dir = tmp_path / "platform_data"
    platform_dir.mkdir()

    monkeypatch.setattr(settings_module, "get_repo_root", lambda: fake_repo_root)
    monkeypatch.setattr(settings_module, "resolve_platform_data_dir", lambda: platform_dir)

    data_dir = settings_module.get_data_dir()

    assert data_dir == platform_dir
    assert (data_dir / settings_module.SETTINGS_FILENAME).read_text(encoding="utf-8") == '{"child_name": "Avyaan"}'


def test_migrate_from_repo_local_dir_copies_settings_and_db(tmp_path, monkeypatch):
    import app.config.settings as settings_module

    fake_repo_root = tmp_path / "repo"
    repo_local_dir = fake_repo_root / settings_module.REPO_LOCAL_DATA_DIRNAME
    repo_local_dir.mkdir(parents=True)
    (repo_local_dir / settings_module.SETTINGS_FILENAME).write_text('{"child_name": "Avyaan"}', encoding="utf-8")
    (repo_local_dir / settings_module.DB_FILENAME).write_bytes(b"fake sqlite bytes")

    new_dir = tmp_path / "new_data_dir"
    new_dir.mkdir()

    monkeypatch.setattr(settings_module, "get_repo_root", lambda: fake_repo_root)
    settings_module._migrate_from_repo_local_dir(new_dir)

    assert (new_dir / settings_module.SETTINGS_FILENAME).read_text(encoding="utf-8") == '{"child_name": "Avyaan"}'
    assert (new_dir / settings_module.DB_FILENAME).read_bytes() == b"fake sqlite bytes"


def test_migrate_does_not_overwrite_existing_files_in_new_location(tmp_path, monkeypatch):
    import app.config.settings as settings_module

    fake_repo_root = tmp_path / "repo"
    repo_local_dir = fake_repo_root / settings_module.REPO_LOCAL_DATA_DIRNAME
    repo_local_dir.mkdir(parents=True)
    (repo_local_dir / settings_module.SETTINGS_FILENAME).write_text('{"child_name": "OldName"}', encoding="utf-8")

    new_dir = tmp_path / "new_data_dir"
    new_dir.mkdir()
    (new_dir / settings_module.SETTINGS_FILENAME).write_text('{"child_name": "NewName"}', encoding="utf-8")

    monkeypatch.setattr(settings_module, "get_repo_root", lambda: fake_repo_root)
    settings_module._migrate_from_repo_local_dir(new_dir)

    assert (new_dir / settings_module.SETTINGS_FILENAME).read_text(encoding="utf-8") == '{"child_name": "NewName"}'


def test_migrate_does_nothing_when_no_repo_local_dir_exists(tmp_path, monkeypatch):
    import app.config.settings as settings_module

    new_dir = tmp_path / "new_data_dir"
    new_dir.mkdir()

    monkeypatch.setattr(settings_module, "get_repo_root", lambda: tmp_path / "repo_that_does_not_exist")
    settings_module._migrate_from_repo_local_dir(new_dir)  # should not raise

    assert list(new_dir.iterdir()) == []
