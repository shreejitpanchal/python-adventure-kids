from app.config import platform_paths


def test_uses_flet_app_storage_data_env_var_when_set(tmp_path, monkeypatch):
    android_dir = tmp_path / "android_data"
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(android_dir))

    data_dir = platform_paths.resolve_platform_data_dir()

    assert data_dir == android_dir
    assert data_dir.is_dir()


def test_flet_app_storage_data_wins_even_on_windows(tmp_path, monkeypatch):
    android_dir = tmp_path / "android_data"
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(android_dir))
    monkeypatch.setattr(platform_paths.sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path / "should_not_be_used"))

    data_dir = platform_paths.resolve_platform_data_dir()

    assert data_dir == android_dir


def test_uses_appdata_pythonadventure_on_windows(tmp_path, monkeypatch):
    monkeypatch.delenv("FLET_APP_STORAGE_DATA", raising=False)
    monkeypatch.setattr(platform_paths.sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path))

    data_dir = platform_paths.resolve_platform_data_dir()

    assert data_dir == tmp_path / "PythonAdventure"
    assert data_dir.is_dir()


def test_falls_back_to_home_dir_if_appdata_unset_on_windows(tmp_path, monkeypatch):
    monkeypatch.delenv("FLET_APP_STORAGE_DATA", raising=False)
    monkeypatch.setattr(platform_paths.sys, "platform", "win32")
    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.setattr(platform_paths.Path, "home", lambda: tmp_path)

    data_dir = platform_paths.resolve_platform_data_dir()

    assert data_dir == tmp_path / "PythonAdventure"


def test_uses_home_dotfile_dir_on_non_windows_platforms(tmp_path, monkeypatch):
    monkeypatch.delenv("FLET_APP_STORAGE_DATA", raising=False)
    monkeypatch.setattr(platform_paths.sys, "platform", "linux")
    monkeypatch.setattr(platform_paths.Path, "home", lambda: tmp_path)

    data_dir = platform_paths.resolve_platform_data_dir()

    assert data_dir == tmp_path / ".pythonadventure"
    assert data_dir.is_dir()
