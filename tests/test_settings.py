from app.config.settings import Settings


def test_default_settings_are_not_setup_complete():
    settings = Settings()
    assert settings.setup_complete is False
    assert settings.has_parent_pin() is False


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
