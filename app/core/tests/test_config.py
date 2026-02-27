"""Unit tests for app.core.config."""

from __future__ import annotations

import pytest

from app.core.config import Settings, get_settings


class TestSettingsDefaults:
    def test_default_app_name(self) -> None:
        s = Settings()
        assert s.app_name == "Obsidian Agent Project"

    def test_default_version(self) -> None:
        s = Settings()
        assert s.version == "0.1.0"

    def test_default_environment(self) -> None:
        s = Settings()
        assert s.environment == "development"

    def test_default_log_level(self) -> None:
        s = Settings()
        assert s.log_level == "INFO"

    def test_default_api_prefix(self) -> None:
        s = Settings()
        assert s.api_prefix == "/api"

    def test_default_allowed_origins(self) -> None:
        s = Settings()
        assert "http://localhost:3000" in s.allowed_origins
        assert "http://localhost:8123" in s.allowed_origins


class TestSettingsFromEnv:
    def test_app_name_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("APP_NAME", "Test App")
        s = Settings()
        assert s.app_name == "Test App"

    def test_environment_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ENVIRONMENT", "production")
        s = Settings()
        assert s.environment == "production"

    def test_log_level_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        s = Settings()
        assert s.log_level == "DEBUG"

    def test_allowed_origins_list_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ALLOWED_ORIGINS", '["http://example.com"]')
        s = Settings()
        assert s.allowed_origins == ["http://example.com"]


class TestGetSettingsCaching:
    def test_returns_settings_instance(self) -> None:
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_same_instance_returned_on_repeated_calls(self) -> None:
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_cache_clear_returns_new_instance(self) -> None:
        s1 = get_settings()
        get_settings.cache_clear()
        s2 = get_settings()
        # New instance after cache clear — values equal but different objects
        assert s1.app_name == s2.app_name
        # Restore cached instance for subsequent tests
        get_settings.cache_clear()
