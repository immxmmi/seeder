"""Tests for config loader (connectors list)."""

import os
import sys

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config.loader import Config


def _write_settings(path, data):
    path.write_text(yaml.safe_dump(data, sort_keys=False))


def test_load_connectors_from_settings(monkeypatch, tmp_path):
    settings = {
        "output": {"file": "./out/inputs.yaml"},
        "debug": {"enabled": False},
        "app": {"version": "1.0.0"},
        "connectors": [
            {
                "name": "c1",
                "enabled": True,
                "connection": {
                    "host": "https://example.com",
                    "auth_type": "bearer",
                    "token_env": "API_TOKEN",
                    "endpoint": "/api/v1/items",
                },
                "mapping": {
                    "replace_object": "notifiers",
                    "fields": [
                        {"from": "title", "to": "name"},
                        {"from": "kind", "to": "type"},
                    ],
                },
            }
        ],
    }

    cfg_path = tmp_path / "settings.yaml"
    _write_settings(cfg_path, settings)
    monkeypatch.setenv("SEEDER_CONFIG_FILE", str(cfg_path))
    monkeypatch.setenv("API_TOKEN", "token")

    Config.reset()
    cfg = Config()

    assert len(cfg.sources) == 1
    c = cfg.sources[0]
    assert c.name == "c1"
    assert c.target_key == "notifiers"
    assert len(c.mapping_fields) == 2


def test_missing_connectors_fails(monkeypatch, tmp_path):
    settings = {
        "output": {"file": "./out/inputs.yaml"},
        "debug": {"enabled": False},
        "app": {"version": "1.0.0"},
    }

    cfg_path = tmp_path / "settings.yaml"
    _write_settings(cfg_path, settings)
    monkeypatch.setenv("SEEDER_CONFIG_FILE", str(cfg_path))

    Config.reset()
    with pytest.raises(ValueError):
        Config()


def test_mapping_replace_object_sets_target_key(monkeypatch, tmp_path):
    settings = {
        "output": {"file": "./out/inputs.yaml"},
        "debug": {"enabled": False},
        "app": {"version": "1.0.0"},
        "connectors": [
            {
                "name": "c2",
                "enabled": True,
                "connection": {"host": "https://example.com", "endpoint": "/api", "auth_type": "none"},
                "mapping": {
                    "replace_object": "integrations",
                    "fields": [{"from": "title", "to": "name"}],
                },
            }
        ],
    }

    cfg_path = tmp_path / "settings.yaml"
    _write_settings(cfg_path, settings)
    monkeypatch.setenv("SEEDER_CONFIG_FILE", str(cfg_path))

    Config.reset()
    cfg = Config()
    assert cfg.sources[0].target_key == "integrations"
