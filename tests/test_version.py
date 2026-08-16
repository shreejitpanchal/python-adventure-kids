"""Tests for app/version.py -- the version/build-number info shown in Settings."""
from __future__ import annotations

import app.version as version_module


def test_get_app_version_reads_project_version_from_pyproject_toml(tmp_path, monkeypatch):
    fake_repo_root = tmp_path
    (fake_repo_root / "pyproject.toml").write_text('[project]\nversion = "2.3.4"\n', encoding="utf-8")

    monkeypatch.setattr(version_module, "get_repo_root", lambda: fake_repo_root)

    assert version_module.get_app_version() == "2.3.4"


def test_get_app_version_falls_back_to_unknown_when_pyproject_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(version_module, "get_repo_root", lambda: tmp_path)

    assert version_module.get_app_version() == "unknown"


def test_get_app_version_falls_back_to_unknown_when_version_key_missing(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "python-adventure"\n', encoding="utf-8")

    monkeypatch.setattr(version_module, "get_repo_root", lambda: tmp_path)

    assert version_module.get_app_version() == "unknown"


def test_get_build_number_reads_build_number_file(tmp_path, monkeypatch):
    (tmp_path / "BUILD_NUMBER").write_text("7\n", encoding="utf-8")

    monkeypatch.setattr(version_module, "get_repo_root", lambda: tmp_path)

    assert version_module.get_build_number() == "7"


def test_get_build_number_falls_back_to_dev_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(version_module, "get_repo_root", lambda: tmp_path)

    assert version_module.get_build_number() == "dev"


def test_get_version_label_combines_version_and_build(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "1.0.0"\n', encoding="utf-8")
    (tmp_path / "BUILD_NUMBER").write_text("3", encoding="utf-8")

    monkeypatch.setattr(version_module, "get_repo_root", lambda: tmp_path)

    assert version_module.get_version_label() == "v1.0.0 (build 3)"
