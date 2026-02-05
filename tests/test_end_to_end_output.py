"""End-to-end test: seeder writes inputs.yaml."""

import os
import sys
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config.loader import Config
from main import main
import gateway.client as client_mod


def test_seeder_writes_inputs_yaml(tmp_path, monkeypatch):
    out_path_env = os.getenv("E2E_OUTPUT_FILE")
    out_path = os.path.abspath(out_path_env) if out_path_env else str(tmp_path / "inputs.yaml")
    cfg_path = os.path.join(os.path.dirname(__file__), "fixtures", "settings.yaml")
    monkeypatch.setenv("SEEDER_CONFIG_FILE", cfg_path)
    monkeypatch.setenv("OUTPUT_FILE", out_path)

    def fake_get(self, endpoint, **kwargs):
        return {
            "1forge.com": {
                "preferred": "0.0.1",
                "versions": {
                    "0.0.1": {
                        "info": {
                            "contact": {"email": "contact@1forge.com"},
                            "title": "1Forge Finance APIs",
                            "version": "0.0.1",
                            "x-apisguru-categories": ["financial"],
                            "x-providerName": "1forge.com",
                        },
                        "swaggerUrl": "https://api.apis.guru/v2/specs/1forge.com/0.0.1/swagger.json",
                        "openapiVer": "2.0",
                        "link": "https://api.apis.guru/v2/specs/1forge.com/0.0.1.json",
                    }
                },
            },
        }

    monkeypatch.setattr(client_mod.ApiClient, "get", fake_get)

    Config.reset()
    main()

    assert os.path.exists(out_path)
    content = yaml.safe_load(open(out_path, "r").read())
    assert "apis" in content
    assert content["apis"][0]["id"] == "1forge.com"
    assert content["apis"][0]["preferred"] == "0.0.1"
    assert content["apis"][0]["title"] == "1Forge Finance APIs"
    assert content["apis"][0]["contact_email"] == "contact@1forge.com"
