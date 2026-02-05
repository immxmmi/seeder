"""End-to-end test: seeder writes inputs.yaml."""

import os
import sys
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config.loader import Config
from main import main
import gateway.client as client_mod


def test_seeder_writes_inputs_yaml(tmp_path, monkeypatch):
    settings = {
        "output": {"file": str(tmp_path / "inputs.yaml")},
        "debug": {"enabled": False},
        "app": {"version": "1.0.0"},
        "connectors": [
            {
                "name": "test-notifiers",
                "enabled": True,
                "connection": {
                    "host": "https://example.com",
                    "auth_type": "none",
                    "endpoint": "/api/notifiers",
                },
                "mapping": {
                    "replace_object": "notifiers",
                    "fields": [
                        {"from": "title", "to": "name"},
                        {"from": "notification_type", "to": "type"},
                    ],
                },
            }
        ],
    }

    cfg_path = tmp_path / "settings.yaml"
    cfg_path.write_text(yaml.safe_dump(settings, sort_keys=False))

    monkeypatch.setenv("SEEDER_CONFIG_FILE", str(cfg_path))
    monkeypatch.setenv("OUTPUT_FILE", str(tmp_path / "inputs.yaml"))

    def fake_get(self, endpoint, **kwargs):
        return [{"title": "Jira-Sec", "notification_type": "jira"}]

    monkeypatch.setattr(client_mod.ApiClient, "get", fake_get)

    Config.reset()
    main()

    out_path = tmp_path / "inputs.yaml"
    assert out_path.exists()
    content = yaml.safe_load(out_path.read_text())
    assert "notifiers" in content
    assert content["notifiers"][0]["name"] == "Jira-Sec"
